/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import SchemeSelector from '../components/SchemeSelector'
import type { SchemeAssignments } from '../components/SchemeSelector'
import type { PortfolioProduct } from '../types'

afterEach(cleanup)

// ── Helpers ───────────────────────────────────────────────────────────────────
const makeProduct = (
  name: string,
  productType = 'Plataforma',
  allowedSchemes?: string[],
): PortfolioProduct => ({
  name,
  product_type: productType,
  description: `Descripción de ${name}`,
  business_framework: '',
  monetization_model: '',
  pricing_model: '',
  country: 'Colombia',
  allowed_schemes: allowedSchemes,
})

const PLATFORM = makeProduct('Qx-Tránsito', 'Plataforma', [
  'licensing', 'services', 'support_maintenance',
])
const PLATFORM_B = makeProduct('Qx-Recaudo', 'Plataforma', [
  'licensing', 'services', 'support_maintenance',
])
// El backend ya excluye licensing para QloudSI en allowed_schemes
const QLOUDSI = makeProduct('Innti', 'Servicio QloudSI', ['services', 'support_maintenance'])

// ── Suite ─────────────────────────────────────────────────────────────────────
describe('SchemeSelector (esquema por producto)', () => {
  const mockOnSelectionChanged = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderSelector = (
    products: PortfolioProduct[],
    props: {
      initialAssignments?: SchemeAssignments
      initialCombine?: boolean
    } = {},
  ) =>
    render(
      <SchemeSelector
        products={products}
        onSelectionChanged={mockOnSelectionChanged}
        {...props}
      />
    )

  const lastCall = () => mockOnSelectionChanged.mock.calls.at(-1)!

  // ── 1. Tarjeta por producto ───────────────────────────────────────────────
  it('renderiza una tarjeta por producto seleccionado', () => {
    renderSelector([PLATFORM, QLOUDSI])
    expect(screen.getByTestId('product-card-Qx-Tránsito')).toBeInTheDocument()
    expect(screen.getByTestId('product-card-Innti')).toBeInTheDocument()
  })

  it('cada tarjeta muestra solo los esquemas permitidos de SU producto', () => {
    renderSelector([QLOUDSI])
    const card = screen.getByTestId('product-card-Innti')
    expect(card).toHaveTextContent('Prestación de Servicios')
    expect(card).toHaveTextContent('Soporte y Mantenimiento')
  })

  it('sin productos muestra el aviso de volver al paso anterior', () => {
    renderSelector([])
    expect(screen.getByText(/no hay productos seleccionados/i)).toBeInTheDocument()
  })

  // ── 2. Regla QloudSI ──────────────────────────────────────────────────────
  it('un producto QloudSI no renderiza la opción Licenciamiento', () => {
    renderSelector([QLOUDSI])
    const card = screen.getByTestId('product-card-Innti')
    const radios = card.querySelectorAll('input[type="radio"]')
    const values = Array.from(radios).map((r) => (r as HTMLInputElement).value)
    expect(values).not.toContain('licensing')
    expect(values).toContain('services')
  })

  it('un producto QloudSI muestra la nota de Licenciamiento no disponible', () => {
    renderSelector([QLOUDSI])
    expect(
      screen.getByText('Licenciamiento no disponible para servicios QloudSI')
    ).toBeInTheDocument()
  })

  it('QloudSI sin allowed_schemes del backend filtra licensing igual (fallback defensivo)', () => {
    const qloudsiNoList = makeProduct('Qloudsi Raw', 'Servicio QloudSI', undefined)
    renderSelector([qloudsiNoList])
    const card = screen.getByTestId('product-card-Qloudsi Raw')
    const values = Array.from(card.querySelectorAll('input[type="radio"]')).map(
      (r) => (r as HTMLInputElement).value
    )
    expect(values).not.toContain('licensing')
  })

  it('una Plataforma sí muestra Licenciamiento y no muestra la nota QloudSI', () => {
    renderSelector([PLATFORM])
    const card = screen.getByTestId('product-card-Qx-Tránsito')
    const values = Array.from(card.querySelectorAll('input[type="radio"]')).map(
      (r) => (r as HTMLInputElement).value
    )
    expect(values).toContain('licensing')
    expect(
      screen.queryByText('Licenciamiento no disponible para servicios QloudSI')
    ).not.toBeInTheDocument()
  })

  // ── 3. Asignación y completitud ───────────────────────────────────────────
  it('isComplete es false hasta que TODOS los productos tengan esquema', () => {
    renderSelector([PLATFORM, QLOUDSI])
    expect(lastCall()[2]).toBe(false)

    // Asignar esquema solo al primero → sigue incompleto
    const cardA = screen.getByTestId('product-card-Qx-Tránsito')
    fireEvent.click(cardA.querySelector('input[value="licensing"]')!)
    expect(lastCall()[2]).toBe(false)

    // Asignar al segundo → completo
    const cardB = screen.getByTestId('product-card-Innti')
    fireEvent.click(cardB.querySelector('input[value="services"]')!)
    expect(lastCall()[2]).toBe(true)
  })

  it('emite las asignaciones por nombre de producto', () => {
    renderSelector([PLATFORM])
    const card = screen.getByTestId('product-card-Qx-Tránsito')
    fireEvent.click(card.querySelector('input[value="licensing"]')!)

    const assignments = lastCall()[0] as SchemeAssignments
    expect(assignments['Qx-Tránsito']).toEqual(
      expect.objectContaining({ scheme_type: 'licensing', payment_frequency: 'Único' })
    )
  })

  it('dos productos pueden tener el mismo tipo de esquema', () => {
    renderSelector([PLATFORM, PLATFORM_B])
    fireEvent.click(
      screen.getByTestId('product-card-Qx-Tránsito').querySelector('input[value="licensing"]')!
    )
    fireEvent.click(
      screen.getByTestId('product-card-Qx-Recaudo').querySelector('input[value="licensing"]')!
    )

    const assignments = lastCall()[0] as SchemeAssignments
    expect(assignments['Qx-Tránsito'].scheme_type).toBe('licensing')
    expect(assignments['Qx-Recaudo'].scheme_type).toBe('licensing')
    expect(lastCall()[2]).toBe(true)
  })

  // ── 4. Frecuencia de pago por producto ────────────────────────────────────
  it('muestra la frecuencia de pago al asignar un esquema y permite cambiarla', () => {
    renderSelector([PLATFORM])
    const card = screen.getByTestId('product-card-Qx-Tránsito')
    fireEvent.click(card.querySelector('input[value="licensing"]')!)

    expect(screen.getByRole('button', { name: 'Mensual' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Mensual' }))

    const assignments = lastCall()[0] as SchemeAssignments
    expect(assignments['Qx-Tránsito'].payment_frequency).toBe('Mensual')
  })

  // ── 5. Toggle unificado/separado ──────────────────────────────────────────
  it('muestra el toggle de documentos con 2 o más productos', () => {
    renderSelector([PLATFORM, QLOUDSI])
    expect(screen.getByText('Documento unificado')).toBeInTheDocument()
    expect(screen.getByText('Documentos separados')).toBeInTheDocument()
  })

  it('no muestra el toggle con un solo producto', () => {
    renderSelector([PLATFORM])
    expect(screen.queryByText('Documento unificado')).not.toBeInTheDocument()
    expect(screen.queryByText('Documentos separados')).not.toBeInTheDocument()
  })

  it('cambiar a "Documentos separados" emite combineSchemes=false', () => {
    renderSelector([PLATFORM, QLOUDSI])
    fireEvent.click(screen.getByText('Documentos separados'))
    expect(lastCall()[1]).toBe(false)
  })

  it('con un solo producto siempre emite combineSchemes=true', () => {
    renderSelector([PLATFORM], { initialCombine: false })
    expect(lastCall()[1]).toBe(true)
  })

  // ── 6. Inicialización y aviso de intersección eliminado ──────────────────
  it('inicializa con asignaciones previas', () => {
    renderSelector([PLATFORM], {
      initialAssignments: {
        'Qx-Tránsito': { scheme_type: 'licensing', payment_frequency: 'Único' },
      },
    })
    const card = screen.getByTestId('product-card-Qx-Tránsito')
    expect(card.querySelector('input[value="licensing"]')).toBeChecked()
    expect(lastCall()[2]).toBe(true)
  })

  it('ya no existe el aviso de "no comparten ningún esquema comercial"', () => {
    renderSelector([PLATFORM, QLOUDSI])
    expect(
      screen.queryByText(/no comparten ningún esquema comercial/i)
    ).not.toBeInTheDocument()
  })
})
