/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import ProposalListPage from '../pages/ProposalListPage'
import { proposalApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import type { Proposal } from '../types'

vi.mock('../services/api', () => ({
  proposalApi: {
    list: vi.fn(),
    delete: vi.fn(),
  },
}))

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const mockProposals: Proposal[] = [
  {
    id: 1,
    title: 'Propuesta de Software A',
    code: 'P-001',
    status: 'draft',
    combine_schemes: false,
    client_id: 1,
    products: [],
    schemes: [],
    created_at: '2024-01-01T10:00:00Z',
    updated_at: '2024-01-01T10:00:00Z',
  },
  {
    id: 2,
    title: 'Mantenimiento de Redes',
    code: 'P-002',
    status: 'approved',
    combine_schemes: true,
    client_id: 2,
    products: [],
    schemes: [],
    created_at: '2024-02-01T10:00:00Z',
    updated_at: '2024-02-01T10:00:00Z',
  },
  {
    id: 3,
    title: 'Consultoría TI',
    code: 'P-003',
    status: 'rejected',
    combine_schemes: false,
    client_id: 1,
    products: [],
    schemes: [],
    created_at: '2024-03-01T10:00:00Z',
    updated_at: '2024-03-01T10:00:00Z',
  },
]

const renderPage = () =>
  render(
    <MemoryRouter>
      <ProposalListPage />
    </MemoryRouter>
  )

const waitForLoad = () =>
  waitFor(() => {
    expect(screen.queryByText(/Cargando propuestas.../i)).not.toBeInTheDocument()
  })

describe('ProposalListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 1, email: 'creator@test.com', full_name: 'Test Creator', role: 'creator' },
      token: 'mock-token',
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    })
  })

  afterEach(() => {
    cleanup()
  })

  it('renders "No hay propuestas" when list is empty', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: [] } as never)

    renderPage()
    await waitForLoad()

    expect(screen.getByText(/No hay propuestas creadas aún/i)).toBeInTheDocument()
  })

  it('renders a table with mocked proposals', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)

    renderPage()
    await waitForLoad()

    expect(screen.getByText('Propuesta de Software A')).toBeInTheDocument()
    expect(screen.getByText('Mantenimiento de Redes')).toBeInTheDocument()
    expect(screen.getByText('Consultoría TI')).toBeInTheDocument()
    expect(screen.getByText('P-001')).toBeInTheDocument()
    expect(screen.getByText('P-002')).toBeInTheDocument()
  })

  it('shows correct status badges with colors', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)

    renderPage()
    await waitForLoad()

    const draftBadge = screen.getAllByText('Borrador')[0]
    const approvedBadge = screen.getAllByText('Aprobada')[0]
    const rejectedBadge = screen.getAllByText('Rechazada')[0]

    expect(draftBadge).toHaveClass('bg-gray-100')
    expect(approvedBadge).toHaveClass('bg-green-100')
    expect(rejectedBadge).toHaveClass('bg-red-100')
  })

  it('renders Editar button for all proposals', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)

    renderPage()
    await waitForLoad()

    const editButtons = screen.getAllByRole('link', { name: /Editar/i })
    expect(editButtons).toHaveLength(3)
    expect(editButtons[0]).toHaveAttribute('href', '/proposals/1')
    expect(editButtons[1]).toHaveAttribute('href', '/proposals/2')
    expect(editButtons[2]).toHaveAttribute('href', '/proposals/3')
  })

  it('renders Eliminar button only for draft proposals', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)

    renderPage()
    await waitForLoad()

    // Solo la propuesta con status 'draft' (id=1) tiene botón Eliminar
    expect(screen.getByTestId('delete-btn-1')).toBeInTheDocument()
    expect(screen.queryByTestId('delete-btn-2')).not.toBeInTheDocument()
    expect(screen.queryByTestId('delete-btn-3')).not.toBeInTheDocument()
  })

  it('opens confirmation modal when Eliminar is clicked', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)

    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByTestId('delete-btn-1'))

    expect(screen.getByText(/Eliminar propuesta/i)).toBeInTheDocument()
    expect(screen.getByText(/Esta acción no se puede deshacer/i)).toBeInTheDocument()
    // El título de la propuesta aparece dentro del texto del modal
    expect(screen.getByText(/Esta acción no se puede deshacer/i).closest('div')).toBeInTheDocument()
  })

  it('calls proposalApi.delete and removes proposal from list on confirm', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)
    vi.mocked(proposalApi.delete).mockResolvedValue({ data: undefined } as never)

    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByTestId('delete-btn-1'))
    fireEvent.click(screen.getByTestId('confirm-delete-btn'))

    await waitFor(() => {
      expect(proposalApi.delete).toHaveBeenCalledWith(1)
    })
    await waitFor(() => {
      expect(screen.queryByText('Propuesta de Software A')).not.toBeInTheDocument()
    })
  })

  it('shows error message when delete fails', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)
    vi.mocked(proposalApi.delete).mockRejectedValue(new Error('Error 409'))

    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByTestId('delete-btn-1'))
    fireEvent.click(screen.getByTestId('confirm-delete-btn'))

    await waitFor(() => {
      expect(
        screen.getByText(/No se pudo eliminar la propuesta/i)
      ).toBeInTheDocument()
    })
  })

  it('closes modal when Cancelar is clicked', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)

    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByTestId('delete-btn-1'))
    expect(screen.getByText(/Eliminar propuesta/i)).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Cancelar/i }))
    expect(screen.queryByText(/Esta acción no se puede deshacer/i)).not.toBeInTheDocument()
  })

  it('Eliminar button visible for creator with draft status', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)
    renderPage()
    await waitForLoad()
    expect(screen.getByTestId('delete-btn-1')).toBeInTheDocument()
  })

  it('Eliminar button NOT visible for approver_1 even with draft status', async () => {
    vi.mocked(useAuth).mockReturnValue({
      user: { id: 2, email: 'approver@test.com', full_name: 'Test Approver', role: 'approver_1' },
      token: 'mock-token',
      login: vi.fn(),
      logout: vi.fn(),
      isLoading: false,
    })
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as never)
    renderPage()
    await waitForLoad()
    expect(screen.queryByTestId('delete-btn-1')).not.toBeInTheDocument()
  })
})
