/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import ClientForm from '../components/ClientForm'
import { clientApi } from '../services/api'
import type { Client } from '../types'

afterEach(cleanup)

// ── Mock de API ───────────────────────────────────────────────────────────────
vi.mock('../services/api', () => ({
  clientApi: { create: vi.fn() },
}))

// ── Datos de prueba ───────────────────────────────────────────────────────────
const MOCK_CREATED_CLIENT: Client = {
  id: 1,
  name: 'Juan Pérez',
  entity: 'Alcaldía de Bogotá',
  country: 'Colombia',
  department: 'Cundinamarca',
  city: 'Bogotá D.C.',
  email: 'juan@bogota.gov.co',
}

// ── Suite ─────────────────────────────────────────────────────────────────────
describe('ClientForm', () => {
  const mockOnClientCreated = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  const renderForm = () => {
    const result = render(
      <ClientForm onClientCreated={mockOnClientCreated} />
    )
    return result
  }

  // ── Helpers para campos de formulario ────────────────────────────────────
  const getInput = (container: HTMLElement, name: string) =>
    container.querySelector(`input[name="${name}"]`) as HTMLInputElement

  const getSelect = (container: HTMLElement, name: string) =>
    container.querySelector(`select[name="${name}"]`) as HTMLSelectElement

  // ── 1. Renderizado ────────────────────────────────────────────────────────
  it('renderiza todos los campos del formulario', () => {
    const { container } = renderForm()

    expect(getInput(container, 'name')).toBeInTheDocument()
    expect(getInput(container, 'position')).toBeInTheDocument()
    expect(getInput(container, 'entity')).toBeInTheDocument()
    expect(getSelect(container, 'country')).toBeInTheDocument()
    expect(getSelect(container, 'department')).toBeInTheDocument()
    expect(getSelect(container, 'city')).toBeInTheDocument()
    expect(getInput(container, 'email')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Guardar Cliente/i })
    ).toBeInTheDocument()
  })

  it('renderiza las etiquetas de los campos', () => {
    renderForm()
    expect(screen.getByText('Nombre *')).toBeInTheDocument()
    expect(screen.getByText('Entidad *')).toBeInTheDocument()
    expect(screen.getByText('Cargo')).toBeInTheDocument()
    expect(screen.getByText('País')).toBeInTheDocument()
    expect(screen.getByText('Departamento')).toBeInTheDocument()
    expect(screen.getByText('Ciudad')).toBeInTheDocument()
  })

  // ── 2. Validación ─────────────────────────────────────────────────────────
  it('muestra error de validación cuando falta el nombre', async () => {
    const { container } = renderForm()

    fireEvent.change(getInput(container, 'entity'), {
      target: { value: 'Alcaldía' },
    })
    fireEvent.submit(container.querySelector('form')!)

    await waitFor(() => {
      expect(
        screen.getByText(/Nombre y Entidad son campos obligatorios/i)
      ).toBeInTheDocument()
    })
    expect(clientApi.create).not.toHaveBeenCalled()
  })

  it('muestra error de validación cuando falta la entidad', async () => {
    const { container } = renderForm()

    fireEvent.change(getInput(container, 'name'), {
      target: { value: 'Juan' },
    })
    fireEvent.submit(container.querySelector('form')!)

    await waitFor(() => {
      expect(
        screen.getByText(/Nombre y Entidad son campos obligatorios/i)
      ).toBeInTheDocument()
    })
    expect(clientApi.create).not.toHaveBeenCalled()
  })

  // ── 3. Envío exitoso ──────────────────────────────────────────────────────
  it('llama a clientApi.create con country, department y city correctos', async () => {
    vi.mocked(clientApi.create).mockResolvedValue({ data: MOCK_CREATED_CLIENT } as any)

    const { container } = renderForm()
    fireEvent.change(getInput(container, 'name'), { target: { value: 'Juan Pérez' } })
    fireEvent.change(getInput(container, 'entity'), { target: { value: 'Alcaldía de Bogotá' } })
    fireEvent.change(getSelect(container, 'country'), { target: { value: 'Colombia' } })
    fireEvent.change(getSelect(container, 'department'), { target: { value: 'Cundinamarca' } })
    fireEvent.change(getSelect(container, 'city'), { target: { value: 'Bogotá D.C.' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => {
      expect(clientApi.create).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Juan Pérez',
          entity: 'Alcaldía de Bogotá',
          country: 'Colombia',
          department: 'Cundinamarca',
          city: 'Bogotá D.C.',
        })
      )
      expect(mockOnClientCreated).toHaveBeenCalledWith(MOCK_CREATED_CLIENT)
    })
  })

  it('limpia el formulario después de envío exitoso', async () => {
    vi.mocked(clientApi.create).mockResolvedValue({
      data: MOCK_CREATED_CLIENT,
    } as any)

    const { container } = renderForm()
    const nameInput = getInput(container, 'name')

    fireEvent.change(nameInput, { target: { value: 'Juan' } })
    fireEvent.change(getInput(container, 'entity'), { target: { value: 'Alcaldía' } })
    fireEvent.change(getSelect(container, 'country'), { target: { value: 'Colombia' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => expect(mockOnClientCreated).toHaveBeenCalled())
    expect(nameInput.value).toBe('')
    expect(getSelect(container, 'country').value).toBe('')
  })

  it('muestra "Guardando..." y deshabilita el botón mientras se envía', async () => {
    vi.mocked(clientApi.create).mockReturnValue(new Promise(() => {}) as any)

    const { container } = renderForm()
    fireEvent.change(getInput(container, 'name'), { target: { value: 'Juan' } })
    fireEvent.change(getInput(container, 'entity'), { target: { value: 'Alcaldía' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => {
      expect(screen.getByText('Guardando...')).toBeInTheDocument()
    })
    expect(screen.getByRole('button')).toBeDisabled()
  })

  it('muestra el mensaje de error cuando la API falla', async () => {
    vi.mocked(clientApi.create).mockRejectedValue({
      response: { data: { detail: 'Error del servidor al guardar.' } },
    })

    const { container } = renderForm()
    fireEvent.change(getInput(container, 'name'), { target: { value: 'Juan' } })
    fireEvent.change(getInput(container, 'entity'), { target: { value: 'Alcaldía' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Error del servidor al guardar.')
      ).toBeInTheDocument()
    })
  })

  it('muestra mensaje genérico cuando la API falla sin detalle', async () => {
    vi.mocked(clientApi.create).mockRejectedValue(new Error('Network Error'))

    const { container } = renderForm()
    fireEvent.change(getInput(container, 'name'), { target: { value: 'Juan' } })
    fireEvent.change(getInput(container, 'entity'), { target: { value: 'Alcaldía' } })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/Error al guardar el cliente/i)
      ).toBeInTheDocument()
    })
  })

  // ── 6. Cascada de ubicaciones ──────────────────────────────────────────────
  it('department y city están deshabilitados si no hay país seleccionado', () => {
    const { container } = renderForm()
    expect(getSelect(container, 'department')).toBeDisabled()
    expect(getSelect(container, 'city')).toBeDisabled()
  })

  it('al seleccionar Colombia se habilita Departamento con opciones', () => {
    const { container } = renderForm()
    fireEvent.change(getSelect(container, 'country'), {
      target: { value: 'Colombia' },
    })
    const deptSelect = getSelect(container, 'department')
    expect(deptSelect).not.toBeDisabled()
    expect(deptSelect.querySelector('option[value="Cundinamarca"]')).toBeInTheDocument()
  })

  it('al seleccionar departamento se habilita Ciudad con opciones', () => {
    const { container } = renderForm()
    fireEvent.change(getSelect(container, 'country'), {
      target: { value: 'Colombia' },
    })
    fireEvent.change(getSelect(container, 'department'), {
      target: { value: 'Cundinamarca' },
    })
    const citySelect = getSelect(container, 'city')
    expect(citySelect).not.toBeDisabled()
    expect(citySelect.querySelector('option[value="Bogotá D.C."]')).toBeInTheDocument()
  })

  it('al cambiar de país se limpian departamento y ciudad', () => {
    const { container } = renderForm()
    fireEvent.change(getSelect(container, 'country'), { target: { value: 'Colombia' } })
    fireEvent.change(getSelect(container, 'department'), { target: { value: 'Cundinamarca' } })
    fireEvent.change(getSelect(container, 'city'), { target: { value: 'Bogotá D.C.' } })

    fireEvent.change(getSelect(container, 'country'), { target: { value: 'Ecuador' } })

    expect(getSelect(container, 'department').value).toBe('')
    expect(getSelect(container, 'city').value).toBe('')
  })

  it('al cambiar de departamento se limpia ciudad', () => {
    const { container } = renderForm()
    fireEvent.change(getSelect(container, 'country'), { target: { value: 'Colombia' } })
    fireEvent.change(getSelect(container, 'department'), { target: { value: 'Cundinamarca' } })
    fireEvent.change(getSelect(container, 'city'), { target: { value: 'Bogotá D.C.' } })

    fireEvent.change(getSelect(container, 'department'), { target: { value: 'Antioquia' } })

    expect(getSelect(container, 'city').value).toBe('')
  })
})
