/**
 * @vitest-environment jsdom
 *
 * Tests del componente ProposalEditor — cubre el MenuBar (Tarea 3) y la
 * estructura de pestañas/sub-tabs por esquema (refactor del bug de documentos
 * separados con contenido idéntico).
 */
import { vi, describe, it, expect, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup, act } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import type { Proposal } from '../types'

// ── Mocks ──────────────────────────────────────────────────────────────────────

vi.mock('../services/api', () => ({
  proposalApi: {
    update: vi.fn().mockResolvedValue({}),
    updateScheme: vi.fn().mockResolvedValue({}),
  },
}))

const mockRun = vi.fn(() => true)

function createChain() {
  const handler: ProxyHandler<object> = {
    get: (_target, prop: string) => {
      if (prop === 'run') return mockRun
      return () => new Proxy({}, handler)
    },
  }
  return new Proxy({}, handler)
}

const mockIsActive = vi.fn((_type: string) => false)
const mockSetEditable = vi.fn()
const mockSetContent = vi.fn()
const mockGetHTML = vi.fn(() => '<p></p>')

let currentEditorIsEditable = true

vi.mock('@tiptap/react', () => ({
  useEditor: vi.fn((_options: unknown) => ({
    isEditable: currentEditorIsEditable,
    isActive: mockIsActive,
    chain: () => createChain(),
    can: () => ({ chain: () => createChain() }),
    commands: { setContent: mockSetContent },
    setEditable: mockSetEditable,
    getHTML: mockGetHTML,
    on: vi.fn(),
    off: vi.fn(),
    destroy: vi.fn(),
  })),
  EditorContent: ({ editor }: { editor: unknown }) => (
    <div data-testid="tiptap-editor-content">{editor ? 'editor-activo' : 'sin-editor'}</div>
  ),
  Editor: class MockEditor {},
}))

vi.mock('@tiptap/starter-kit', () => ({ default: {} }))
vi.mock('@tiptap/extension-table', () => ({
  default: { configure: vi.fn(() => ({})) },
}))
vi.mock('@tiptap/extension-table-row', () => ({ default: {} }))
vi.mock('@tiptap/extension-table-cell', () => ({ default: {} }))
vi.mock('@tiptap/extension-table-header', () => ({ default: {} }))

import ProposalEditor from '../components/ProposalEditor'

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeProposal(overrides: Partial<Proposal> = {}): Proposal {
  return {
    id: 1,
    title: 'Propuesta test',
    status: 'draft',
    combine_schemes: true,
    context_content: '<p>Contexto</p>',
    letter_content: '<p>Carta</p>',
    client_id: 1,
    products: [],
    schemes: [
      {
        id: 10,
        scheme_type: 'licensing',
        payment_frequency: 'unico',
        scope_content: '<p>Alcance L</p>',
        ip_section: '<p>IP L</p>',
      },
    ],
    created_at: '2026-01-01',
    updated_at: '2026-01-01',
    ...overrides,
  }
}

function renderEditor(proposal: Proposal = makeProposal(), isEditable = true) {
  currentEditorIsEditable = isEditable
  return render(<ProposalEditor proposal={proposal} />)
}

// ── Suites ────────────────────────────────────────────────────────────────────

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
  currentEditorIsEditable = true
})

describe('ProposalEditor — MenuBar: estructura de botones', () => {
  it('renderiza los 8 botones de formato esperados', () => {
    renderEditor()
    expect(screen.getByRole('button', { name: 'B' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'I' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'H1' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'H2' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'H3' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '• List' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: '1. List' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Tabla' })).toBeInTheDocument()
  })
})

describe('ProposalEditor — MenuBar: estado disabled', () => {
  it('los botones están habilitados cuando el editor es editable', () => {
    renderEditor(makeProposal(), true)
    expect(screen.getByRole('button', { name: 'B' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Tabla' })).not.toBeDisabled()
  })

  it('los botones están deshabilitados cuando isEditable=false (pestaña readOnly)', () => {
    renderEditor(makeProposal(), false)
    for (const name of ['B', 'I', 'H1', 'H2', 'H3', '• List', '1. List', 'Tabla']) {
      expect(screen.getByRole('button', { name }), `Botón "${name}"`).toBeDisabled()
    }
  })
})

describe('ProposalEditor — MenuBar: estado activo', () => {
  it('B tiene bg-blue-600 cuando bold está activo', () => {
    mockIsActive.mockImplementation((type: string) => type === 'bold')
    renderEditor(makeProposal(), true)
    expect(screen.getByRole('button', { name: 'B' })).toHaveClass('bg-blue-600')
  })

  it('B tiene bg-white cuando bold NO está activo', () => {
    mockIsActive.mockImplementation(() => false)
    renderEditor(makeProposal(), true)
    expect(screen.getByRole('button', { name: 'B' })).toHaveClass('bg-white')
  })
})

describe('ProposalEditor — pestañas globales', () => {
  it('renderiza las 8 pestañas (2 globales + 6 por esquema)', () => {
    renderEditor()
    for (const label of [
      'Contexto', 'Alcance', 'Plazo', 'Condiciones Económicas',
      'Forma de Pago', 'Servicios Excluidos', 'Propiedad Intelectual',
      'Carta de Presentación',
    ]) {
      // getAllByRole porque el label "Alcance" puede aparecer en pestaña y badge
      expect(screen.getAllByRole('button', { name: new RegExp(label) }).length).toBeGreaterThan(0)
    }
  })

  it('al hacer clic en "Carta de Presentación" muestra el aviso de solo lectura', async () => {
    renderEditor()
    const cartaTab = screen.getByRole('button', { name: /Carta de Presentación/ })
    await act(async () => { fireEvent.click(cartaTab) })
    expect(screen.getByText(/generada automáticamente por Innti/i)).toBeInTheDocument()
  })

  it('Guardar empieza deshabilitado (sin cambios)', () => {
    renderEditor()
    expect(screen.getByRole('button', { name: /guardar/i })).toBeDisabled()
  })
})

describe('ProposalEditor — sub-tabs por esquema', () => {
  const multiSchemeProposal = makeProposal({
    schemes: [
      { id: 10, scheme_type: 'licensing', payment_frequency: 'unico', ip_section: '<p>IP L</p>' },
      { id: 20, scheme_type: 'services', payment_frequency: 'mensual', ip_section: '<p>IP S</p>' },
      { id: 30, scheme_type: 'support_maintenance', payment_frequency: 'anual', ip_section: '<p>IP M</p>' },
    ],
  })

  it('NO muestra sub-tabs cuando hay un solo esquema', () => {
    renderEditor(makeProposal())
    expect(screen.queryByText(/^Esquema:/)).not.toBeInTheDocument()
  })

  it('muestra sub-tabs de esquema cuando hay >= 2 esquemas y la pestaña es scope=scheme', async () => {
    renderEditor(multiSchemeProposal)
    // Por defecto la pestaña activa es "Contexto" (global) — sin sub-tabs visibles
    expect(screen.queryByText(/^Esquema:$/)).not.toBeInTheDocument()
    // Cambiar a "Propiedad Intelectual" (scope=scheme)
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Propiedad Intelectual/ }))
    })
    // Ahora aparece el selector de esquema
    expect(screen.getByText(/^Esquema:$/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Licenciamiento' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Prestación de Servicios' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Soporte y Mantenimiento' })).toBeInTheDocument()
  })

  it('cambiar de sub-tab actualiza el contenido del editor (setContent invocado)', async () => {
    renderEditor(multiSchemeProposal)
    mockSetContent.mockClear()

    // Cambiar a Propiedad Intelectual primero (scope=scheme)
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: /Propiedad Intelectual/ }))
    })
    mockSetContent.mockClear()

    // Cambiar al esquema "Prestación de Servicios"
    await act(async () => {
      fireEvent.click(screen.getByRole('button', { name: 'Prestación de Servicios' }))
    })
    // setContent se debe haber invocado con el HTML de IP del esquema services
    const calls = mockSetContent.mock.calls
    expect(calls.length).toBeGreaterThan(0)
    expect(calls.some((args) => String(args[0]).includes('IP S'))).toBe(true)
  })

  it('muestra etiqueta "×N" en pestañas scope=scheme cuando hay múltiples esquemas', () => {
    renderEditor(multiSchemeProposal)
    // Los botones de "Alcance", "Plazo", etc. deben mostrar "×3"
    const alcanceTab = screen.getByRole('button', { name: /Alcance/ })
    expect(alcanceTab.textContent).toContain('×3')
  })
})
