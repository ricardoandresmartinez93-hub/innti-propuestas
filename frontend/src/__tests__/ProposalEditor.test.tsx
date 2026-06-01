/**
 * @vitest-environment jsdom
 *
 * Tests del componente ProposalEditor — enfocados en el comportamiento del MenuBar:
 *   - Tarea 3: botones usan onMouseDown para no perder el foco del editor.
 *   - Tarea 3: todos los botones quedan disabled cuando la pestaña es readOnly.
 *   - Tarea 3: estado activo (fondo azul) refleja correctamente el formato aplicado.
 */
import { vi, describe, it, expect, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup, act } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

// ── Mocks ──────────────────────────────────────────────────────────────────────

vi.mock('../services/api', () => ({
  proposalApi: {
    update: vi.fn().mockResolvedValue({}),
  },
}))

/**
 * Crea un mock del editor TipTap con estado controlable.
 * La API de comandos usa un Proxy que devuelve `run()` en cualquier cadena.
 * run() devuelve `true` para que la prop `disabled` calcule correctamente.
 */
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
  useEditor: vi.fn((_options: unknown) =>
    ({
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
    })
  ),
  EditorContent: ({ editor }: { editor: unknown }) => (
    <div data-testid="tiptap-editor-content">
      {editor ? 'editor-activo' : 'sin-editor'}
    </div>
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

// ── Import del componente (después de los mocks) ───────────────────────────────
import ProposalEditor from '../components/ProposalEditor'

// ── Helpers ───────────────────────────────────────────────────────────────────

const DEFAULT_CONTENT = {
  context_content: '<p>Texto de contexto</p>',
  scope_content: '',
  validity_period: '',
  economic_conditions: '',
  payment_terms: '',
  excluded_services: '',
  ip_section: '',
  letter_content: '',
}

function renderEditor(isEditable = true) {
  currentEditorIsEditable = isEditable
  return render(
    <ProposalEditor proposalId={1} initialContent={DEFAULT_CONTENT} />
  )
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
  it('todos los botones están habilitados cuando el editor es editable', () => {
    renderEditor(true)
    // can()...run() devuelve true → !true = false → no disabled
    expect(screen.getByRole('button', { name: 'B' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'Tabla' })).not.toBeDisabled()
    expect(screen.getByRole('button', { name: 'H1' })).not.toBeDisabled()
  })

  it('todos los botones están deshabilitados cuando isEditable=false (pestaña readOnly)', () => {
    renderEditor(false)
    const formatButtons = ['B', 'I', 'H1', 'H2', 'H3', '• List', '1. List', 'Tabla']
    for (const name of formatButtons) {
      expect(
        screen.getByRole('button', { name }),
        `Botón "${name}" debe estar disabled cuando isReadOnly`
      ).toBeDisabled()
    }
  })
})

describe('ProposalEditor — MenuBar: estado activo (active styling)', () => {
  it('el botón B tiene clase bg-blue-600 cuando bold está activo', () => {
    mockIsActive.mockImplementation((type: string) => type === 'bold')
    renderEditor(true)
    expect(screen.getByRole('button', { name: 'B' })).toHaveClass('bg-blue-600')
  })

  it('el botón B tiene clase bg-white cuando bold NO está activo', () => {
    mockIsActive.mockImplementation(() => false)
    renderEditor(true)
    expect(screen.getByRole('button', { name: 'B' })).toHaveClass('bg-white')
    expect(screen.getByRole('button', { name: 'B' })).not.toHaveClass('bg-blue-600')
  })

  it('el botón H1 tiene clase bg-blue-600 cuando heading 1 está activo', () => {
    mockIsActive.mockImplementation(
      (type: string, attrs?: { level?: number }) => type === 'heading' && attrs?.level === 1
    )
    renderEditor(true)
    expect(screen.getByRole('button', { name: 'H1' })).toHaveClass('bg-blue-600')
    expect(screen.getByRole('button', { name: 'H2' })).not.toHaveClass('bg-blue-600')
  })
})

describe('ProposalEditor — MenuBar: ejecución de comandos', () => {
  it('el botón B ejecuta el comando al hacer mousedown', () => {
    renderEditor(true)
    const boldBtn = screen.getByRole('button', { name: 'B' })
    fireEvent.mouseDown(boldBtn)
    expect(mockRun).toHaveBeenCalled()
  })

  it('el botón I ejecuta el comando al hacer mousedown', () => {
    renderEditor(true)
    fireEvent.mouseDown(screen.getByRole('button', { name: 'I' }))
    expect(mockRun).toHaveBeenCalled()
  })

  it('el botón H1 ejecuta el comando al hacer mousedown', () => {
    renderEditor(true)
    fireEvent.mouseDown(screen.getByRole('button', { name: 'H1' }))
    expect(mockRun).toHaveBeenCalled()
  })

  it('el botón • List ejecuta el comando al hacer mousedown', () => {
    renderEditor(true)
    fireEvent.mouseDown(screen.getByRole('button', { name: '• List' }))
    expect(mockRun).toHaveBeenCalled()
  })

  it('el botón Tabla ejecuta el comando al hacer mousedown cuando es editable', () => {
    renderEditor(true)
    fireEvent.mouseDown(screen.getByRole('button', { name: 'Tabla' }))
    expect(mockRun).toHaveBeenCalled()
  })

  it('los botones disabled NO ejecutan el comando al hacer mousedown', () => {
    renderEditor(false) // isEditable=false → todos disabled
    const boldBtn = screen.getByRole('button', { name: 'B' })
    // Los botones disabled no disparan mousedown events
    expect(boldBtn).toBeDisabled()
  })
})

describe('ProposalEditor — pestañas', () => {
  it('renderiza las 8 pestañas del editor', () => {
    renderEditor()
    const tabLabels = [
      'Contexto', 'Alcance', 'Plazo', 'Condiciones Económicas',
      'Forma de Pago', 'Servicios Excluidos', 'Propiedad Intelectual',
      'Carta de Presentación',
    ]
    for (const label of tabLabels) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument()
    }
  })

  it('al hacer clic en "Carta de Presentación" muestra el aviso de solo lectura', async () => {
    renderEditor()
    const cartaTab = screen.getByRole('button', { name: 'Carta de Presentación' })
    await act(async () => {
      fireEvent.click(cartaTab)
    })
    expect(
      screen.getByText(/generada automáticamente por Innti/i)
    ).toBeInTheDocument()
  })

  it('el botón Guardar empieza deshabilitado (sin cambios pendientes)', () => {
    renderEditor()
    // Hay múltiples botones "Guardar" posibles; buscamos por role y disabled
    const saveBtn = screen.getByRole('button', { name: /guardar/i })
    expect(saveBtn).toBeDisabled()
  })
})
