/**
 * @vitest-environment jsdom
 */
import React from 'react'
import { vi, describe, it, expect, beforeEach, afterEach, type Mock } from 'vitest'
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ProposalDetailPage from '../pages/ProposalDetailPage'
import { proposalApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import type { Proposal, Approval } from '../types'

afterEach(cleanup)

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const mockUser = (role: 'creator' | 'approver_1' | 'approver_2' | 'viewer') => {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: 1, email: 'test@test.com', full_name: 'Test User', role },
    token: 'mock-token',
    login: vi.fn(),
    logout: vi.fn(),
    isLoading: false,
  })
}

// Mock de proposalApi
vi.mock('../services/api', () => ({
  proposalApi: {
    get: vi.fn(),
    getApprovals: vi.fn(),
    approve: vi.fn(),
    reject: vi.fn(),
    submitForReview: vi.fn(),
    markSentToClient: vi.fn(),
    generateDocument: vi.fn(),
    generatePdf: vi.fn(),
    generateAnnex: vi.fn(),
  },
}))

// Mock de ProposalEditor — usa forwardRef para evitar el warning de React
// "Function components cannot be given refs", ya que ProposalDetailPage pasa
// un ref al editor (editorRef: useRef<ProposalEditorHandle>).
vi.mock('../components/ProposalEditor', () => ({
  default: React.forwardRef(
    (_props: object, _ref: React.Ref<unknown>) => (
      <div data-testid="proposal-editor">Editor Mock</div>
    )
  ),
}))

const mockProposal: Proposal = {
  id: 1,
  title: 'Test Proposal',
  code: 'P-001',
  status: 'draft',
  combine_schemes: false,
  client_id: 1,
  products: [],
  schemes: [],
  created_at: '2024-01-01T10:00:00Z',
  updated_at: '2024-01-01T10:00:00Z',
}

const renderWithRouter = () => {
  render(
    <MemoryRouter initialEntries={['/proposals/1']}>
      <Routes>
        <Route path="/proposals/:id" element={<ProposalDetailPage />} />
      </Routes>
    </MemoryRouter>
  )
}

describe('ProposalDetailPage Approval Flow', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockUser('creator')
    vi.mocked(proposalApi.getApprovals).mockResolvedValue({ data: [] } as any)
  })

  it('shows "Enviar a Revisión" button when status is draft', async () => {
    vi.mocked(proposalApi.get).mockResolvedValue({ data: { ...mockProposal, status: 'draft' } } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('Enviar a Revisión')).toBeInTheDocument()
    })
  })

  it('shows approval/rejection buttons for Angela when status is pending_review', async () => {
    mockUser('approver_1')
    vi.mocked(proposalApi.get).mockResolvedValue({ data: { ...mockProposal, status: 'pending_review' } } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText(/Aprobar \(Ángela\)/i)).toBeInTheDocument()
      expect(screen.getByText(/Rechazar/i)).toBeInTheDocument()
    })
  })

  it('shows "Enviar a VP" button for approver_1 (Angela) when status is reviewed', async () => {
    mockUser('approver_1')
    vi.mocked(proposalApi.get).mockResolvedValue({ data: { ...mockProposal, status: 'reviewed' } } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText(/Enviar a VP →/i)).toBeInTheDocument()
    })
  })

  it('does NOT show "Enviar a VP" button for creator when status is reviewed', async () => {
    mockUser('creator')
    vi.mocked(proposalApi.get).mockResolvedValue({ data: { ...mockProposal, status: 'reviewed' } } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.queryByText(/Enviar a VP →/i)).not.toBeInTheDocument()
    })
  })

  it('shows approval/rejection buttons for VP when status is pending_vp', async () => {
    mockUser('approver_2')
    vi.mocked(proposalApi.get).mockResolvedValue({ data: { ...mockProposal, status: 'pending_vp' } } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText(/Aprobar \(Juan Pablo\)/i)).toBeInTheDocument()
      expect(screen.getAllByText(/Rechazar/i)[0]).toBeInTheDocument()
    })
  })

  it('shows "Marcar como Enviada al Cliente" button for approver_2 when status is approved', async () => {
    mockUser('approver_2')
    vi.mocked(proposalApi.get).mockResolvedValue({ data: { ...mockProposal, status: 'approved' } } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText(/Marcar como Enviada al Cliente/i)).toBeInTheDocument()
    })
  })

  it('does NOT show "Marcar como Enviada al Cliente" button for creator when status is approved', async () => {
    mockUser('creator')
    vi.mocked(proposalApi.get).mockResolvedValue({ data: { ...mockProposal, status: 'approved' } } as any)

    renderWithRouter()

    await waitFor(() => {
      expect(screen.queryByText(/Marcar como Enviada al Cliente/i)).not.toBeInTheDocument()
    })
  })

  it('opens rejection modal with comments field when clicking "Rechazar"', async () => {
    mockUser('approver_1')
    vi.mocked(proposalApi.get).mockResolvedValue({ data: { ...mockProposal, status: 'pending_review' } } as any)

    renderWithRouter()

    await waitFor(() => {
      fireEvent.click(screen.getAllByText(/Rechazar/i)[0])
    })

    expect(screen.getByText(/Rechazar propuesta/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/Indique el motivo del rechazo.../i)).toBeInTheDocument()
  })

  it('shows approval history when data is present', async () => {
    const mockApprovals: Approval[] = [
      {
        id: 1,
        proposal_id: 1,
        role: 'reviewer',
        approver_name: 'Angela Test',
        action: 'approved',
        comments: 'Looks good',
        created_at: '2024-01-01T12:00:00Z',
      }
    ]
    vi.mocked(proposalApi.get).mockResolvedValue({ data: mockProposal } as any)
    vi.mocked(proposalApi.getApprovals).mockResolvedValue({ data: mockApprovals } as any)
    
    renderWithRouter()

    await waitFor(() => {
      expect(screen.getByText('Angela Test')).toBeInTheDocument()
      expect(screen.getByText('Revisora (Ángela)')).toBeInTheDocument()
      expect(screen.getByText(/"Looks good"/i)).toBeInTheDocument()
    })
  })
})

describe('ProposalDetailPage — descarga de documentos', () => {
  let createObjectURL: Mock

  beforeEach(() => {
    vi.clearAllMocks()
    mockUser('creator')
    vi.mocked(proposalApi.getApprovals).mockResolvedValue({ data: [] } as any)

    createObjectURL = vi.fn(() => 'blob:mock')
    Object.defineProperty(window, 'URL', {
      writable: true,
      value: { createObjectURL, revokeObjectURL: vi.fn() },
    })
  })

  afterEach(() => {
    cleanup()
  })

  it('crea un Blob application/zip cuando el backend responde con ese content-type', async () => {
    vi.mocked(proposalApi.get).mockResolvedValue({
      data: { ...mockProposal, status: 'draft' },
    } as any)
    vi.mocked(proposalApi.generateDocument).mockResolvedValue({
      data: new Blob(['PK']),
      headers: { 'content-type': 'application/zip' },
    } as any)

    renderWithRouter()
    await waitFor(() => expect(screen.getByText('Generar Word')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Generar Word'))

    await waitFor(() => expect(createObjectURL).toHaveBeenCalled())
    const blob: Blob = createObjectURL.mock.calls[0][0]
    expect(blob.type).toBe('application/zip')
  })

  it('crea un Blob wordprocessingml cuando el backend responde con ese content-type', async () => {
    vi.mocked(proposalApi.get).mockResolvedValue({
      data: { ...mockProposal, status: 'draft' },
    } as any)
    vi.mocked(proposalApi.generateDocument).mockResolvedValue({
      data: new Blob(['PK']),
      headers: {
        'content-type':
          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      },
    } as any)

    renderWithRouter()
    await waitFor(() => expect(screen.getByText('Generar Word')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Generar Word'))

    await waitFor(() => expect(createObjectURL).toHaveBeenCalled())
    const blob: Blob = createObjectURL.mock.calls[0][0]
    expect(blob.type).toContain('wordprocessingml')
  })
})
