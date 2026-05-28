/**
 * @vitest-environment jsdom
 */
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor, fireEvent, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import AdminPage from '../pages/AdminPage'
import { userApi } from '../services/api'
import type { AppUser } from '../types'

vi.mock('../services/api', () => ({
  userApi: {
    list: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    deactivate: vi.fn(),
  },
}))

const mockUsers: AppUser[] = [
  {
    id: 1,
    full_name: 'Administrador',
    email: 'admin@quipux.com',
    role: 'admin',
    is_active: true,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  },
  {
    id: 2,
    full_name: 'Ana Creadora',
    email: 'ana@quipux.com',
    role: 'creator',
    is_active: true,
    created_at: '2024-01-02T00:00:00Z',
    updated_at: '2024-01-02T00:00:00Z',
  },
  {
    id: 3,
    full_name: 'Carlos Inactivo',
    email: 'carlos@quipux.com',
    role: 'viewer',
    is_active: false,
    created_at: '2024-01-03T00:00:00Z',
    updated_at: '2024-01-03T00:00:00Z',
  },
]

const renderPage = () =>
  render(
    <MemoryRouter>
      <AdminPage />
    </MemoryRouter>
  )

const waitForLoad = () =>
  waitFor(() => {
    expect(screen.queryByText(/Cargando usuarios.../i)).not.toBeInTheDocument()
  })

describe('AdminPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    cleanup()
  })

  it('muestra "Cargando usuarios..." durante la carga inicial', () => {
    vi.mocked(userApi.list).mockImplementation(() => new Promise(() => {}))
    renderPage()
    expect(screen.getByText(/Cargando usuarios.../i)).toBeInTheDocument()
  })

  it('muestra la lista de usuarios activos al cargar', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers.filter(u => u.is_active) } as never)

    renderPage()
    await waitForLoad()

    // "Administrador" aparece en el nombre Y en el badge de rol → usar getAllByText
    expect(screen.getAllByText('Administrador').length).toBeGreaterThanOrEqual(1)
    expect(screen.getByText('Ana Creadora')).toBeInTheDocument()
    expect(screen.getByText('admin@quipux.com')).toBeInTheDocument()
    expect(screen.getByText('ana@quipux.com')).toBeInTheDocument()
  })

  it('muestra "No hay usuarios registrados." cuando la lista está vacía', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: [] } as never)

    renderPage()
    await waitForLoad()

    expect(screen.getByText(/No hay usuarios registrados/i)).toBeInTheDocument()
  })

  it('muestra mensaje de error cuando falla la carga', async () => {
    vi.mocked(userApi.list).mockRejectedValue(new Error('Network error'))

    renderPage()
    await waitForLoad()

    expect(screen.getByText(/No se pudo cargar la lista de usuarios/i)).toBeInTheDocument()
  })

  it('muestra etiquetas de rol correctas (Revisor, VP, sin apellidos)', async () => {
    const usersWithAllRoles: AppUser[] = [
      { id: 1, full_name: 'U1', email: 'u1@test.com', role: 'approver_1', is_active: true, created_at: '', updated_at: '' },
      { id: 2, full_name: 'U2', email: 'u2@test.com', role: 'approver_2', is_active: true, created_at: '', updated_at: '' },
    ]
    vi.mocked(userApi.list).mockResolvedValue({ data: usersWithAllRoles } as never)

    renderPage()
    await waitForLoad()

    expect(screen.getByText('Revisor')).toBeInTheDocument()
    expect(screen.getByText('VP')).toBeInTheDocument()
    expect(screen.queryByText(/Ángela/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/Juan Pablo/i)).not.toBeInTheDocument()
  })

  it('muestra badge "Activo" e "Inactivo" según el estado', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    const activeBadges = screen.getAllByText('Activo')
    expect(activeBadges.length).toBeGreaterThanOrEqual(2)
    expect(screen.getByText('Inactivo')).toBeInTheDocument()
  })

  it('muestra el contador correcto de usuarios activos', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    // 2 activos de 3
    expect(screen.getByText(/2 usuarios activos/i)).toBeInTheDocument()
  })

  it('abre el modal de "Nuevo usuario" al hacer clic en el botón', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByText('+ Nuevo usuario'))

    expect(screen.getByText('Nuevo usuario')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Nombre completo')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('usuario@quipux.com')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('Contraseña segura')).toBeInTheDocument()
  })

  it('cierra el modal al hacer clic en Cancelar', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByText('+ Nuevo usuario'))
    expect(screen.getByText('Nuevo usuario')).toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /Cancelar/i }))
    expect(screen.queryByText('Nuevo usuario')).not.toBeInTheDocument()
  })

  it('muestra error de validación si se envía sin contraseña (modo crear)', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByText('+ Nuevo usuario'))

    // Llenar nombre y email pero NO contraseña
    fireEvent.change(screen.getByPlaceholderText('Nombre completo'), { target: { value: 'Nuevo Usuario' } })
    fireEvent.change(screen.getByPlaceholderText('usuario@quipux.com'), { target: { value: 'nuevo@quipux.com' } })

    // Usar fireEvent.submit directamente en el <form> para evitar que jsdom bloquee
    // la propagación por la validación HTML5 del campo required vacío.
    const submitBtn = screen.getByRole('button', { name: /Crear usuario/i })
    fireEvent.submit(submitBtn.closest('form')!)

    await waitFor(() => {
      expect(screen.getByText(/La contraseña es obligatoria/i)).toBeInTheDocument()
    })
    expect(userApi.create).not.toHaveBeenCalled()
  })

  it('llama a userApi.create con los datos correctos al crear usuario', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)
    vi.mocked(userApi.create).mockResolvedValue({ data: mockUsers[1] } as never)

    renderPage()
    await waitForLoad()

    fireEvent.click(screen.getByText('+ Nuevo usuario'))

    fireEvent.change(screen.getByPlaceholderText('Nombre completo'), { target: { value: 'Nuevo Usuario' } })
    fireEvent.change(screen.getByPlaceholderText('usuario@quipux.com'), { target: { value: 'nuevo@quipux.com' } })
    fireEvent.change(screen.getByPlaceholderText('Contraseña segura'), { target: { value: 'Password123!' } })

    fireEvent.click(screen.getByRole('button', { name: /Crear usuario/i }))

    await waitFor(() => {
      expect(userApi.create).toHaveBeenCalledWith({
        full_name: 'Nuevo Usuario',
        email: 'nuevo@quipux.com',
        role: 'creator',
        password: 'Password123!',
      })
    })
  })

  it('abre el modal de edición con datos precargados al hacer clic en Editar', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    const editButtons = screen.getAllByRole('button', { name: /Editar/i })
    fireEvent.click(editButtons[0])

    expect(screen.getByText('Editar usuario')).toBeInTheDocument()

    const nombreInput = screen.getByPlaceholderText('Nombre completo') as HTMLInputElement
    expect(nombreInput.value).toBe('Administrador')

    const emailInput = screen.getByPlaceholderText('usuario@quipux.com') as HTMLInputElement
    expect(emailInput.value).toBe('admin@quipux.com')

    // En modo edición aparece el checkbox "Usuario activo"
    expect(screen.getByLabelText('Usuario activo')).toBeInTheDocument()
  })

  it('llama a userApi.update con los datos correctos al editar usuario', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)
    vi.mocked(userApi.update).mockResolvedValue({ data: mockUsers[0] } as never)

    renderPage()
    await waitForLoad()

    const editButtons = screen.getAllByRole('button', { name: /Editar/i })
    fireEvent.click(editButtons[1]) // editar "Ana Creadora"

    fireEvent.change(screen.getByPlaceholderText('Nombre completo'), { target: { value: 'Ana Editada' } })

    fireEvent.click(screen.getByRole('button', { name: /Guardar cambios/i }))

    await waitFor(() => {
      expect(userApi.update).toHaveBeenCalledWith(2, expect.objectContaining({
        full_name: 'Ana Editada',
        email: 'ana@quipux.com',
        role: 'creator',
        is_active: true,
      }))
    })
  })

  it('muestra botón "Desactivar" solo para usuarios activos', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    const deactivateButtons = screen.getAllByRole('button', { name: /Desactivar/i })
    // Solo hay 2 activos de los 3 usuarios
    expect(deactivateButtons).toHaveLength(2)
  })

  it('abre el diálogo de confirmación al hacer clic en Desactivar', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    const deactivateButtons = screen.getAllByRole('button', { name: /Desactivar/i })
    fireEvent.click(deactivateButtons[0])

    expect(screen.getByText(/¿Desactivar usuario\?/i)).toBeInTheDocument()
    expect(screen.getByText(/no podrá iniciar sesión/i)).toBeInTheDocument()
  })

  it('cancela la desactivación al hacer clic en Cancelar del diálogo', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    const deactivateButtons = screen.getAllByRole('button', { name: /Desactivar/i })
    fireEvent.click(deactivateButtons[0])
    expect(screen.getByText(/¿Desactivar usuario\?/i)).toBeInTheDocument()

    // Cancelar del diálogo de confirmación
    const cancelBtn = screen.getAllByRole('button', { name: /Cancelar/i })
    fireEvent.click(cancelBtn[cancelBtn.length - 1])

    expect(screen.queryByText(/¿Desactivar usuario\?/i)).not.toBeInTheDocument()
    expect(userApi.deactivate).not.toHaveBeenCalled()
  })

  it('llama a userApi.deactivate y recarga la lista al confirmar desactivación', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)
    vi.mocked(userApi.deactivate).mockResolvedValue({ data: undefined } as never)

    renderPage()
    await waitForLoad()

    const deactivateButtons = screen.getAllByRole('button', { name: /Desactivar/i })
    fireEvent.click(deactivateButtons[0]) // Administrador (id=1)

    fireEvent.click(screen.getByRole('button', { name: /Sí, desactivar/i }))

    await waitFor(() => {
      expect(userApi.deactivate).toHaveBeenCalledWith(1)
    })
    // Debe recargar la lista (segunda llamada a list)
    await waitFor(() => {
      expect(userApi.list).toHaveBeenCalledTimes(2)
    })
  })

  it('muestra error cuando falla la desactivación', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)
    vi.mocked(userApi.deactivate).mockRejectedValue({
      response: { data: { detail: 'No puedes desactivarte a ti mismo.' } },
    })

    renderPage()
    await waitForLoad()

    const deactivateButtons = screen.getAllByRole('button', { name: /Desactivar/i })
    fireEvent.click(deactivateButtons[0])
    fireEvent.click(screen.getByRole('button', { name: /Sí, desactivar/i }))

    await waitFor(() => {
      expect(screen.getByText(/No puedes desactivarte a ti mismo/i)).toBeInTheDocument()
    })
  })

  it('llama a userApi.list con includeInactive=true al activar "Mostrar inactivos"', async () => {
    vi.mocked(userApi.list).mockResolvedValue({ data: mockUsers } as never)

    renderPage()
    await waitForLoad()

    const checkbox = screen.getByRole('checkbox', { name: /Mostrar inactivos/i })
    fireEvent.click(checkbox)

    await waitFor(() => {
      expect(userApi.list).toHaveBeenCalledWith(undefined, true)
    })
  })
})
