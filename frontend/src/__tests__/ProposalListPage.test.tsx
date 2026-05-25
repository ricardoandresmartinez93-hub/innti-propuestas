/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import ProposalListPage from '../pages/ProposalListPage'
import { proposalApi } from '../services/api'
import type { Proposal } from '../types'

// Mock de proposalApi
vi.mock('../services/api', () => ({
  proposalApi: {
    list: vi.fn(),
  },
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

describe('ProposalListPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders "No hay propuestas" when list is empty', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: [] } as any)

    render(
      <MemoryRouter>
        <ProposalListPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.queryByText(/Cargando propuestas.../i)).not.toBeInTheDocument()
    })

    expect(screen.getByText(/No hay propuestas creadas aún/i)).toBeInTheDocument()
  })

  it('renders a table with mocked proposals', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as any)

    render(
      <MemoryRouter>
        <ProposalListPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Propuesta de Software A')).toBeInTheDocument()
    })

    expect(screen.getByText('Mantenimiento de Redes')).toBeInTheDocument()
    expect(screen.getByText('Consultoría TI')).toBeInTheDocument()
    expect(screen.getByText('P-001')).toBeInTheDocument()
    expect(screen.getByText('P-002')).toBeInTheDocument()
  })

  it('shows correct status badges with colors', async () => {
    vi.mocked(proposalApi.list).mockResolvedValue({ data: mockProposals } as any)

    render(
      <MemoryRouter>
        <ProposalListPage />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getAllByText('Borrador')[0]).toBeInTheDocument()
    })

    const draftBadge = screen.getAllByText('Borrador')[0]
    const approvedBadge = screen.getAllByText('Aprobada')[0]
    const rejectedBadge = screen.getAllByText('Rechazada')[0]

    expect(draftBadge).toHaveClass('bg-gray-100')
    expect(approvedBadge).toHaveClass('bg-green-100')
    expect(rejectedBadge).toHaveClass('bg-red-100')
  })
})
