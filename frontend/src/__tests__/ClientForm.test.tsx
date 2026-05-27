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
  city: 'Bogotá',
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
  // ClientForm no usa htmlFor/id, por lo que accedemos por name attribute.
  const getInput = (container: HTMLElement, name: string) =>
    container.querySelector(`input[name="${name}"]`) as HTMLInputElement

  // ── 1. Renderizado ────────────────────────────────────────────────────────
  it('renderiza todos los campos del formulario', () => {
    const { container } = renderForm()

    expect(getInput(container, 'name')).toBeInTheDocument()
    expect(getInput(container, 'position')).toBeInTheDocument()
    expect(getInput(container, 'entity')).toBeInTheDocument()
    expect(getInput(container, 'department')).toBeInTheDocument()
    expect(getInput(container, 'city')).toBeInTheDocument()
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
    expect(screen.getByText('Ciudad')).toBeInTheDocument()
  })

  // ── 2. Validación ─────────────────────────────────────────────────────────
  // Usamos fireEvent.submit(form) en lugar de click(button) para los tests
  // de validación React, ya que JSDOM bloquea el submit via HTML5 constraint
  // validation cuando un campo `required` está vacío y se hace click en submit.
  it('muestra error de validación cuando falta el nombre', async () => {
    const { container } = renderForm()

    // Solo rellena Entidad, deja Nombre vacío
    fireEvent.change(getInput(container, 'entity'), {
      target: { value: 'Alcaldía' },
    })
    // Disparar submit directamente sobre el form para evitar constraint validation del HTML5
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
    // Disparar submit directamente sobre el form para evitar constraint validation del HTML5
    fireEvent.submit(container.querySelector('form')!)

    await waitFor(() => {
      expect(
        screen.getByText(/Nombre y Entidad son campos obligatorios/i)
      ).toBeInTheDocument()
    })
    expect(clientApi.create).not.toHaveBeenCalled()
  })

  // ── 3. Envío exitoso ──────────────────────────────────────────────────────
  it('llama a clientApi.create y onClientCreated al enviar correctamente', async () => {
    vi.mocked(clientApi.create).mockResolvedValue({
      data: MOCK_CREATED_CLIENT,
    } as any)

    const { container } = renderForm()

    fireEvent.change(getInput(container, 'name'), {
      target: { value: 'Juan Pérez' },
    })
    fireEvent.change(getInput(container, 'entity'), {
      target: { value: 'Alcaldía de Bogotá' },
    })
    fireEvent.change(getInput(container, 'city'), {
      target: { value: 'Bogotá' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => {
      expect(mockOnClientCreated).toHaveBeenCalledWith(MOCK_CREATED_CLIENT)
    })
    expect(clientApi.create).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Juan Pérez', entity: 'Alcaldía de Bogotá' })
    )
  })

  it('limpia el formulario después de envío exitoso', async () => {
    vi.mocked(clientApi.create).mockResolvedValue({
      data: MOCK_CREATED_CLIENT,
    } as any)

    const { container } = renderForm()
    const nameInput = getInput(container, 'name')

    fireEvent.change(nameInput, { target: { value: 'Juan' } })
    fireEvent.change(getInput(container, 'entity'), {
      target: { value: 'Alcaldía' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => expect(mockOnClientCreated).toHaveBeenCalled())
    expect(nameInput.value).toBe('')
  })

  // ── 4. Estado de carga ────────────────────────────────────────────────────
  it('muestra "Guardando..." y deshabilita el botón mientras se envía', async () => {
    // Promesa que nunca resuelve → simula carga indefinida
    vi.mocked(clientApi.create).mockReturnValue(new Promise(() => {}) as any)

    const { container } = renderForm()
    fireEvent.change(getInput(container, 'name'), {
      target: { value: 'Juan' },
    })
    fireEvent.change(getInput(container, 'entity'), {
      target: { value: 'Alcaldía' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => {
      expect(screen.getByText('Guardando...')).toBeInTheDocument()
    })
    expect(screen.getByRole('button')).toBeDisabled()
  })

  // ── 5. Manejo de error de API ─────────────────────────────────────────────
  it('muestra el mensaje de error cuando la API falla', async () => {
    vi.mocked(clientApi.create).mockRejectedValue({
      response: { data: { detail: 'Error del servidor al guardar.' } },
    })

    const { container } = renderForm()
    fireEvent.change(getInput(container, 'name'), {
      target: { value: 'Juan' },
    })
    fireEvent.change(getInput(container, 'entity'), {
      target: { value: 'Alcaldía' },
    })
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
    fireEvent.change(getInput(container, 'name'), {
      target: { value: 'Juan' },
    })
    fireEvent.change(getInput(container, 'entity'), {
      target: { value: 'Alcaldía' },
    })
    fireEvent.click(screen.getByRole('button', { name: /Guardar Cliente/i }))

    await waitFor(() => {
      expect(
        screen.getByText(/Error al guardar el cliente/i)
      ).toBeInTheDocument()
    })
  })
})
