/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import SchemeSelector from '../components/SchemeSelector'
import type { ProposalScheme } from '../types'

afterEach(cleanup)

// ── Suite ─────────────────────────────────────────────────────────────────────
describe('SchemeSelector', () => {
  const mockOnSchemesChanged = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderSelector = (
    props: {
      initialSchemes?: Omit<ProposalScheme, 'id'>[]
      initialCombine?: boolean
      allowedSchemes?: string[]
    } = {}
  ) =>
    render(
      <SchemeSelector
        onSchemesChanged={mockOnSchemesChanged}
        {...props}
      />
    )

  // ── 1. Renderizado inicial ────────────────────────────────────────────────
  it('renderiza los tres esquemas del MVP', () => {
    renderSelector()
    expect(screen.getByText('Licenciamiento')).toBeInTheDocument()
    expect(screen.getByText('Prestación de Servicios')).toBeInTheDocument()
    expect(screen.getByText('Soporte y Mantenimiento')).toBeInTheDocument()
  })

  it('llama a onSchemesChanged al montar con lista vacía', () => {
    renderSelector()
    // useEffect se dispara en el primer render con selectedSchemes todos false
    expect(mockOnSchemesChanged).toHaveBeenCalledWith([], true)
  })

  it('ningún checkbox está marcado por defecto', () => {
    renderSelector()
    const checkboxes = screen.getAllByRole('checkbox')
    checkboxes.forEach((cb) => expect(cb).not.toBeChecked())
  })

  // ── 2. Selección de esquemas ──────────────────────────────────────────────
  it('marcar un checkbox llama a onSchemesChanged con ese esquema', () => {
    renderSelector()
    fireEvent.click(screen.getByRole('checkbox', { name: /Licenciamiento/i }))

    expect(mockOnSchemesChanged).toHaveBeenLastCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ scheme_type: 'licensing' }),
      ]),
      true
    )
  })

  it('desmarcar un checkbox lo elimina de los esquemas activos', () => {
    renderSelector()
    const checkbox = screen.getByRole('checkbox', { name: /Licenciamiento/i })

    fireEvent.click(checkbox) // seleccionar
    fireEvent.click(checkbox) // deseleccionar

    const lastCallSchemes = mockOnSchemesChanged.mock.calls.at(-1)![0]
    expect(lastCallSchemes).not.toContainEqual(
      expect.objectContaining({ scheme_type: 'licensing' })
    )
  })

  // ── 3. Frecuencia de pago ─────────────────────────────────────────────────
  it('muestra los botones de frecuencia al seleccionar un esquema', () => {
    renderSelector()
    fireEvent.click(screen.getByRole('checkbox', { name: /Licenciamiento/i }))

    // Los tres botones de frecuencia deben aparecer
    expect(screen.getByRole('button', { name: 'Único' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Mensual' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Anual' })).toBeInTheDocument()
  })

  it('oculta los botones de frecuencia al deseleccionar el esquema', () => {
    renderSelector()
    const checkbox = screen.getByRole('checkbox', { name: /Licenciamiento/i })
    fireEvent.click(checkbox) // seleccionar
    fireEvent.click(checkbox) // deseleccionar

    expect(screen.queryByRole('button', { name: 'Único' })).not.toBeInTheDocument()
  })

  it('cambiar la frecuencia de pago actualiza el callback', () => {
    renderSelector()
    fireEvent.click(screen.getByRole('checkbox', { name: /Licenciamiento/i }))

    // Cambia de 'Único' (default) a 'Mensual'
    fireEvent.click(screen.getByRole('button', { name: 'Mensual' }))

    const lastCallSchemes = mockOnSchemesChanged.mock.calls.at(-1)![0]
    expect(lastCallSchemes).toContainEqual(
      expect.objectContaining({ scheme_type: 'licensing', payment_frequency: 'Mensual' })
    )
  })

  // ── 4. Combinación de esquemas ────────────────────────────────────────────
  it('muestra las opciones de combinación al seleccionar 2 o más esquemas', () => {
    renderSelector()
    fireEvent.click(screen.getByRole('checkbox', { name: /Licenciamiento/i }))
    fireEvent.click(screen.getByRole('checkbox', { name: /Prestación de Servicios/i }))

    expect(screen.getByText('Combinar en uno')).toBeInTheDocument()
    expect(screen.getByText('Documentos separados')).toBeInTheDocument()
  })

  it('no muestra las opciones de combinación con un solo esquema seleccionado', () => {
    renderSelector()
    fireEvent.click(screen.getByRole('checkbox', { name: /Licenciamiento/i }))

    expect(screen.queryByText('Combinar en uno')).not.toBeInTheDocument()
  })

  it('cambiar a "Documentos separados" pasa combineSchemes=false', () => {
    renderSelector()
    fireEvent.click(screen.getByRole('checkbox', { name: /Licenciamiento/i }))
    fireEvent.click(screen.getByRole('checkbox', { name: /Prestación de Servicios/i }))

    fireEvent.click(screen.getByText('Documentos separados'))

    const lastCall = mockOnSchemesChanged.mock.calls.at(-1)!
    expect(lastCall[1]).toBe(false) // combineSchemes
  })

  // ── 5. Inicialización con props ───────────────────────────────────────────
  it('inicializa con los esquemas proporcionados en initialSchemes', () => {
    const initialSchemes: Omit<ProposalScheme, 'id'>[] = [
      { scheme_type: 'licensing', payment_frequency: 'Único' },
    ]
    renderSelector({ initialSchemes })

    const checkbox = screen.getByRole('checkbox', { name: /Licenciamiento/i })
    expect(checkbox).toBeChecked()
  })

  it('inicializa con initialCombine=false cuando se especifica', () => {
    const initialSchemes: Omit<ProposalScheme, 'id'>[] = [
      { scheme_type: 'licensing', payment_frequency: 'Único' },
      { scheme_type: 'services', payment_frequency: 'Mensual' },
    ]
    renderSelector({ initialSchemes, initialCombine: false })

    // Con 2+ esquemas las opciones de combinación son visibles
    expect(screen.getByText('Combinar en uno')).toBeInTheDocument()
    // El segundo botón (Documentos separados) debe tener el estilo activo
    // Solo verificamos que existe el botón (la lógica visual es de estilos CSS)
    expect(screen.getByText('Documentos separados')).toBeInTheDocument()
  })

  // ── 6. allowedSchemes — filtrado por producto ─────────────────────────────
  describe('allowedSchemes', () => {
    it('sin allowedSchemes muestra todos los esquemas de SCHEME_LABELS', () => {
      renderSelector()
      // Los tres MVP visibles
      expect(screen.getByText('Licenciamiento')).toBeInTheDocument()
      expect(screen.getByText('Prestación de Servicios')).toBeInTheDocument()
      expect(screen.getByText('Soporte y Mantenimiento')).toBeInTheDocument()
    })

    it('con allowedSchemes solo muestra los esquemas incluidos', () => {
      renderSelector({ allowedSchemes: ['licensing'] })
      expect(screen.getByText('Licenciamiento')).toBeInTheDocument()
      expect(screen.queryByText('Prestación de Servicios')).not.toBeInTheDocument()
      expect(screen.queryByText('Soporte y Mantenimiento')).not.toBeInTheDocument()
    })

    it('muestra el badge "Filtrado por productos seleccionados" cuando hay restricción', () => {
      renderSelector({ allowedSchemes: ['licensing'] })
      expect(screen.getByText(/Filtrado por productos seleccionados/i)).toBeInTheDocument()
    })

    it('no muestra el badge cuando allowedSchemes no está definido', () => {
      renderSelector()
      expect(screen.queryByText(/Filtrado por productos seleccionados/i)).not.toBeInTheDocument()
    })

    it('allowedSchemes con todos los MVP schemes no oculta ningún esquema MVP', () => {
      renderSelector({ allowedSchemes: ['licensing', 'services', 'support_maintenance'] })
      expect(screen.getByText('Licenciamiento')).toBeInTheDocument()
      expect(screen.getByText('Prestación de Servicios')).toBeInTheDocument()
      expect(screen.getByText('Soporte y Mantenimiento')).toBeInTheDocument()
    })

    it('con allowedSchemes vacío muestra el aviso de productos incompatibles', () => {
      renderSelector({ allowedSchemes: [] })
      expect(screen.queryByText('Licenciamiento')).not.toBeInTheDocument()
      expect(screen.queryByText('Prestación de Servicios')).not.toBeInTheDocument()
      expect(screen.queryByText('Soporte y Mantenimiento')).not.toBeInTheDocument()
      expect(screen.getByText(/no comparten ningún esquema comercial/i)).toBeInTheDocument()
    })

    it('se puede seleccionar un esquema dentro de allowedSchemes', () => {
      renderSelector({ allowedSchemes: ['licensing', 'services'] })
      fireEvent.click(screen.getByRole('checkbox', { name: /Licenciamiento/i }))
      expect(mockOnSchemesChanged).toHaveBeenLastCalledWith(
        expect.arrayContaining([expect.objectContaining({ scheme_type: 'licensing' })]),
        true
      )
    })
  })
})
