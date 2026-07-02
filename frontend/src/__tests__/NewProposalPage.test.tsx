/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import NewProposalPage from '../pages/NewProposalPage'
import { portfolioApi, clientApi } from '../services/api'
import type { Client, PortfolioProduct } from '../types'

// Garantiza que el DOM se limpie entre tests (necesario en Vitest sin globals:true)
afterEach(cleanup)

// ─── Mock de navegación ───────────────────────────────────────────────────────
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

// ─── Mocks de API ─────────────────────────────────────────────────────────────
vi.mock('../services/api', () => ({
  portfolioApi: { listProducts: vi.fn() },
  clientApi:    { list: vi.fn() },
  proposalApi:  { create: vi.fn() },
}))

// ─── Mock SchemeSelector ──────────────────────────────────────────────────────
// Botón que simula asignar un esquema a cada producto (evita depender del
// componente real). Expone los productos recibidos para poder verificarlos.
vi.mock('../components/SchemeSelector', () => ({
  default: ({ products, onSelectionChanged }: {
    products: { name: string }[]
    onSelectionChanged: (
      assignments: Record<string, { scheme_type: string; payment_frequency: string }>,
      combine: boolean,
      isComplete: boolean,
    ) => void
  }) => (
    <div>
      <span data-testid="selector-products">{products.map(p => p.name).join(',')}</span>
      <button
        data-testid="mock-scheme-btn"
        onClick={() => {
          const assignments = Object.fromEntries(
            products.map(p => [p.name, { scheme_type: 'licensing', payment_frequency: 'Único' }])
          )
          onSelectionChanged(assignments, true, products.length > 0)
        }}
      >
        Seleccionar Esquema Mock
      </button>
    </div>
  ),
}))

// ─── Mock ClientForm ──────────────────────────────────────────────────────────
// Botón que simula guardar un cliente nuevo.
vi.mock('../components/ClientForm', () => ({
  default: ({ onClientCreated }: { onClientCreated: (client: Client) => void }) => (
    <button
      data-testid="mock-client-form-btn"
      onClick={() =>
        onClientCreated({
          id: 99,
          name: 'Cliente Nuevo Test',
          entity: 'Entidad Nueva',
          city: 'Bogotá',
          email: 'nuevo@test.com',
        })
      }
    >
      Guardar Cliente Mock
    </button>
  ),
}))

// ─── Datos de prueba ──────────────────────────────────────────────────────────
const mockProducts: PortfolioProduct[] = [
  {
    name: 'Producto Alpha',
    product_type: 'software',
    description: 'Descripción de prueba',
    business_framework: '',
    monetization_model: '',
    pricing_model: '',
    country: 'Colombia',
    allowed_schemes: ['licensing', 'services', 'support_maintenance'],
  },
]

const mockClients: Client[] = [
  { id: 1, name: 'Carlos Pérez', entity: 'Alcaldía de Medellín',     city: 'Medellín', email: 'carlos@medellin.gov.co' },
  { id: 2, name: 'María López',  entity: 'Gobernación de Antioquia', city: 'Medellín', email: 'maria@antioquia.gov.co' },
]

// ─── Helper: renderizar ───────────────────────────────────────────────────────
const renderPage = () =>
  render(
    <MemoryRouter>
      <NewProposalPage />
    </MemoryRouter>
  )

// ─── Helper: obtener el botón "Siguiente" habilitado ─────────────────────────
// Usa getAllByText para tolerar múltiples instancias en el DOM si las hubiera.
const getEnabledNextBtn = () => {
  const btns = screen.getAllByText('Siguiente')
  return btns.find(btn => !btn.hasAttribute('disabled'))
}

// ─── Helper: avanzar hasta el paso 3 ─────────────────────────────────────────
const navigateToStep3 = async () => {
  // Paso 1 → esperar checkbox y seleccionar producto
  await waitFor(() => {
    expect(screen.getByRole('checkbox')).toBeInTheDocument()
  })
  fireEvent.click(screen.getByRole('checkbox'))

  // Esperar que "Siguiente" se habilite y avanzar a paso 2
  await waitFor(() => expect(getEnabledNextBtn()).toBeTruthy())
  fireEvent.click(getEnabledNextBtn()!)

  // Paso 2 → seleccionar esquema
  await waitFor(() => {
    expect(screen.getByTestId('mock-scheme-btn')).toBeInTheDocument()
  })
  fireEvent.click(screen.getByTestId('mock-scheme-btn'))

  // Esperar que "Siguiente" se habilite y avanzar a paso 3
  await waitFor(() => expect(getEnabledNextBtn()).toBeTruthy())
  fireEvent.click(getEnabledNextBtn()!)

  // Confirmar paso 3
  await waitFor(() => {
    expect(screen.getByText('Información del Cliente')).toBeInTheDocument()
  })
}

// ─── Suite de tests ───────────────────────────────────────────────────────────
describe('NewProposalPage — Paso 3: selección de cliente', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(portfolioApi.listProducts).mockResolvedValue({ data: mockProducts } as any)
    vi.mocked(clientApi.list).mockResolvedValue({ data: mockClients } as any)
  })

  // ── 1. Llamada a API al llegar al paso 3 ────────────────────────────────────
  it('llama a clientApi.list() una sola vez al entrar al paso 3', async () => {
    renderPage()
    await navigateToStep3()

    expect(clientApi.list).toHaveBeenCalledTimes(1)
  })

  // ── 2. Estado de carga ──────────────────────────────────────────────────────
  it('muestra "Cargando clientes..." mientras se obtiene la lista', async () => {
    vi.mocked(clientApi.list).mockReturnValue(new Promise(() => {}) as any)

    renderPage()
    await navigateToStep3()

    expect(screen.getByText(/Cargando clientes\.\.\./i)).toBeInTheDocument()
  })

  // ── 3. Lista de clientes se renderiza ───────────────────────────────────────
  it('renderiza los clientes existentes tras la carga', async () => {
    renderPage()
    await navigateToStep3()

    await waitFor(() => {
      expect(screen.getByText('Carlos Pérez')).toBeInTheDocument()
      expect(screen.getByText('María López')).toBeInTheDocument()
    })
    expect(screen.getByText(/Alcaldía de Medellín/i)).toBeInTheDocument()
    expect(screen.getByText(/Gobernación de Antioquia/i)).toBeInTheDocument()
  })

  // ── 4. Filtro por nombre ────────────────────────────────────────────────────
  it('filtra la lista por nombre del cliente', async () => {
    renderPage()
    await navigateToStep3()

    await waitFor(() => expect(screen.getByText('Carlos Pérez')).toBeInTheDocument())

    fireEvent.change(
      screen.getByPlaceholderText(/Buscar por nombre o entidad\.\.\./i),
      { target: { value: 'Carlos' } }
    )

    expect(screen.getByText('Carlos Pérez')).toBeInTheDocument()
    expect(screen.queryByText('María López')).not.toBeInTheDocument()
  })

  // ── 5. Filtro por entidad ───────────────────────────────────────────────────
  it('filtra la lista por entidad del cliente', async () => {
    renderPage()
    await navigateToStep3()

    await waitFor(() => expect(screen.getByText('María López')).toBeInTheDocument())

    fireEvent.change(
      screen.getByPlaceholderText(/Buscar por nombre o entidad\.\.\./i),
      { target: { value: 'Gobernación' } }
    )

    expect(screen.getByText('María López')).toBeInTheDocument()
    expect(screen.queryByText('Carlos Pérez')).not.toBeInTheDocument()
  })

  // ── 6. Seleccionar cliente existente activa el banner verde ─────────────────
  it('al hacer clic en un cliente aparece el banner verde y "Siguiente" se habilita', async () => {
    renderPage()
    await navigateToStep3()

    await waitFor(() => expect(screen.getByText('Carlos Pérez')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Carlos Pérez'))

    await waitFor(() => {
      expect(screen.getByText('Cambiar')).toBeInTheDocument()
    })
    expect(getEnabledNextBtn()).toBeTruthy()
  })

  // ── 7. El botón "Cambiar" limpia la selección y vuelve a la lista ────────────
  it('el botón "Cambiar" del banner verde restaura la vista de lista', async () => {
    renderPage()
    await navigateToStep3()

    await waitFor(() => expect(screen.getByText('Carlos Pérez')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Carlos Pérez'))

    await waitFor(() => expect(screen.getByText('Cambiar')).toBeInTheDocument())
    fireEvent.click(screen.getByText('Cambiar'))

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/Buscar por nombre o entidad\.\.\./i)
      ).toBeInTheDocument()
    })
  })

  // ── 8. Tab "Seleccionar existente" activo por defecto ──────────────────────
  it('el buscador se muestra por defecto (tab "Seleccionar existente" activo)', async () => {
    renderPage()
    await navigateToStep3()

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/Buscar por nombre o entidad\.\.\./i)
      ).toBeInTheDocument()
    })
    expect(screen.queryByTestId('mock-client-form-btn')).not.toBeInTheDocument()
  })

  // ── 9. Tab "Crear nuevo" muestra el ClientForm ──────────────────────────────
  it('el tab "Crear nuevo" muestra el formulario de creación', async () => {
    renderPage()
    await navigateToStep3()

    fireEvent.click(screen.getByText('Crear nuevo'))

    await waitFor(() => {
      expect(screen.getByTestId('mock-client-form-btn')).toBeInTheDocument()
    })
    expect(
      screen.queryByPlaceholderText(/Buscar por nombre o entidad\.\.\./i)
    ).not.toBeInTheDocument()
  })

  // ── 10. Estado vacío: sin clientes en BD ────────────────────────────────────
  it('muestra el mensaje correcto cuando no hay clientes registrados', async () => {
    vi.mocked(clientApi.list).mockResolvedValue({ data: [] } as any)

    renderPage()
    await navigateToStep3()

    await waitFor(() => {
      expect(
        screen.getByText(/No hay clientes registrados\. Crea uno nuevo\./i)
      ).toBeInTheDocument()
    })
  })

  // ── 11. Estado vacío: búsqueda sin resultados ───────────────────────────────
  it('muestra el mensaje correcto cuando la búsqueda no tiene resultados', async () => {
    renderPage()
    await navigateToStep3()

    await waitFor(() => expect(screen.getByText('Carlos Pérez')).toBeInTheDocument())

    fireEvent.change(
      screen.getByPlaceholderText(/Buscar por nombre o entidad\.\.\./i),
      { target: { value: 'zzz_inexistente' } }
    )

    expect(
      screen.getByText(/No se encontraron clientes que coincidan con la búsqueda\./i)
    ).toBeInTheDocument()
  })

  // ── 12. Crear cliente nuevo lo selecciona automáticamente ───────────────────
  it('al crear un cliente nuevo aparece el banner verde con su nombre', async () => {
    renderPage()
    await navigateToStep3()

    fireEvent.click(screen.getByText('Crear nuevo'))
    await waitFor(() => expect(screen.getByTestId('mock-client-form-btn')).toBeInTheDocument())

    fireEvent.click(screen.getByTestId('mock-client-form-btn'))

    await waitFor(() => {
      expect(screen.getByText('Cliente Nuevo Test')).toBeInTheDocument()
      expect(screen.getByText('Cambiar')).toBeInTheDocument()
    })
  })

  // ── 13. "Siguiente" deshabilitado sin cliente seleccionado ──────────────────
  it('el botón "Siguiente" está deshabilitado cuando no hay cliente seleccionado', async () => {
    renderPage()
    await navigateToStep3()

    await waitFor(() => {
      expect(
        screen.getByPlaceholderText(/Buscar por nombre o entidad\.\.\./i)
      ).toBeInTheDocument()
    })

    expect(getEnabledNextBtn()).toBeUndefined()
  })
})

// ─── Helper: avanzar hasta el paso 4 ─────────────────────────────────────────
const navigateToStep4 = async () => {
  await navigateToStep3()

  // Seleccionar cliente existente
  await waitFor(() => expect(screen.getByText('Carlos Pérez')).toBeInTheDocument())
  fireEvent.click(screen.getByText('Carlos Pérez'))

  // Esperar banner verde y avanzar al paso 4
  await waitFor(() => expect(screen.getByText('Cambiar')).toBeInTheDocument())
  await waitFor(() => expect(getEnabledNextBtn()).toBeTruthy())
  fireEvent.click(getEnabledNextBtn()!)

  // Confirmar paso 4
  await waitFor(() => {
    expect(screen.getByText('Resumen y Título de la Propuesta')).toBeInTheDocument()
  })
}

// ─── Suite: Paso 4 — Código y Título ─────────────────────────────────────────
describe('NewProposalPage — Paso 4: código y título', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(portfolioApi.listProducts).mockResolvedValue({ data: mockProducts } as any)
    vi.mocked(clientApi.list).mockResolvedValue({ data: mockClients } as any)
  })

  // ── 14. Campo "Código" visible en el paso 4 ─────────────────────────────────
  it('muestra el campo "Código de Propuesta" al llegar al paso 4', async () => {
    renderPage()
    await navigateToStep4()

    expect(screen.getByText('Código de Propuesta *')).toBeInTheDocument()
    expect(screen.getByText('Título de la Propuesta *')).toBeInTheDocument()
  })

  // ── 15. "Crear Propuesta" deshabilitado sin código ──────────────────────────
  it('"Crear Propuesta" está deshabilitado cuando el campo código está vacío', async () => {
    renderPage()
    await navigateToStep4()

    // Escribir solo el título, dejar código vacío
    fireEvent.change(
      screen.getByPlaceholderText(/Propuesta Modernización/i),
      { target: { value: 'Propuesta Test' } }
    )

    const createBtn = screen.getByText('Crear Propuesta')
    expect(createBtn).toBeDisabled()
  })

  // ── 16. Crear propuesta con código ─────────────────────────────────────────
  it('llama a proposalApi.create con el código ingresado', async () => {
    const { proposalApi } = await import('../services/api')
    vi.mocked(proposalApi.create).mockResolvedValue({ data: { id: 1 } } as any)

    renderPage()
    await navigateToStep4()

    fireEvent.change(
      screen.getByPlaceholderText(/Ej: 3018-/i),
      { target: { value: '3018-0526' } }
    )
    fireEvent.change(
      screen.getByPlaceholderText(/Propuesta Modernización/i),
      { target: { value: 'Propuesta Test' } }
    )

    await waitFor(() => {
      const createBtn = screen.getByText('Crear Propuesta')
      expect(createBtn).not.toBeDisabled()
    })

    fireEvent.click(screen.getByText('Crear Propuesta'))

    await waitFor(() => {
      expect(proposalApi.create).toHaveBeenCalledWith(
        expect.objectContaining({ code: '3018-0526' })
      )
    })
  })
})

// ── Esquema por producto — el selector recibe los productos seleccionados ─────
describe('NewProposalPage — esquema por producto', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(portfolioApi.listProducts).mockResolvedValue({ data: mockProducts } as any)
    vi.mocked(clientApi.list).mockResolvedValue({ data: mockClients } as any)
  })

  const renderPage = () =>
    render(
      <MemoryRouter>
        <NewProposalPage />
      </MemoryRouter>
    )

  it('pasa los productos seleccionados al SchemeSelector', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Producto Alpha')).toBeInTheDocument())

    fireEvent.click(screen.getAllByRole('checkbox')[0])
    await waitFor(() => expect(getEnabledNextBtn()).toBeTruthy())
    fireEvent.click(getEnabledNextBtn()!)

    await waitFor(() => {
      expect(screen.getByTestId('selector-products').textContent).toBe('Producto Alpha')
    })
  })

  it('no permite avanzar del paso 2 sin asignar esquema a todos los productos', async () => {
    renderPage()
    await waitFor(() => expect(screen.getByText('Producto Alpha')).toBeInTheDocument())

    fireEvent.click(screen.getAllByRole('checkbox')[0])
    await waitFor(() => expect(getEnabledNextBtn()).toBeTruthy())
    fireEvent.click(getEnabledNextBtn()!)

    // En el paso 2, sin asignaciones, "Siguiente" queda deshabilitado
    await waitFor(() => expect(screen.getByTestId('mock-scheme-btn')).toBeInTheDocument())
    expect(getEnabledNextBtn()).toBeUndefined()

    // Al asignar esquemas (mock) se habilita
    fireEvent.click(screen.getByTestId('mock-scheme-btn'))
    await waitFor(() => expect(getEnabledNextBtn()).toBeTruthy())
  })

  it('el payload de creación embebe el esquema dentro de cada producto', async () => {
    const { proposalApi } = await import('../services/api')
    vi.mocked(proposalApi.create).mockResolvedValue({ data: { id: 7 } } as any)

    renderPage()
    await navigateToStep4()

    fireEvent.change(
      screen.getByPlaceholderText(/Ej: 3018-/i),
      { target: { value: '3018-0726' } }
    )
    fireEvent.change(
      screen.getByPlaceholderText(/Propuesta Modernización/i),
      { target: { value: 'Propuesta Esquema por Producto' } }
    )

    await waitFor(() => expect(screen.getByText('Crear Propuesta')).not.toBeDisabled())
    fireEvent.click(screen.getByText('Crear Propuesta'))

    await waitFor(() => {
      expect(proposalApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          combine_schemes: true,
          products: [
            expect.objectContaining({
              product_name: 'Producto Alpha',
              scheme: expect.objectContaining({
                scheme_type: 'licensing',
                payment_frequency: 'Único',
              }),
            }),
          ],
        })
      )
      // El contrato viejo (schemes top-level) ya no se envía
      const payload = vi.mocked(proposalApi.create).mock.calls.at(-1)![0] as unknown as Record<string, unknown>
      expect(payload).not.toHaveProperty('schemes')
    })
  })
})
