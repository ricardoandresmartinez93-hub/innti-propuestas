/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import LoginPage from '../pages/LoginPage'
import { useAuth } from '../contexts/AuthContext'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

describe('LoginPage', () => {
  it('renders form with email and password fields', () => {
    vi.mocked(useAuth).mockReturnValue({ login: vi.fn() } as any)
    const { unmount } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )
    expect(screen.getByPlaceholderText(/email/i)).toBeDefined()
    expect(screen.getByPlaceholderText(/contraseña/i)).toBeDefined()
    expect(screen.getByRole('button', { name: /iniciar sesión/i })).toBeDefined()
    unmount()
  })

  it('shows error message on failed login', async () => {
    vi.mocked(useAuth).mockReturnValue({
      login: vi.fn().mockRejectedValue(new Error('Unauthorized')),
    } as any)

    const { unmount } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByPlaceholderText(/contraseña/i), { target: { value: 'wrong' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByText(/credenciales incorrectas/i)).toBeDefined()
    })
    unmount()
  })

  it('shows "Usuario inactivo" message when user is inactive', async () => {
    const inactiveError = Object.assign(new Error('Inactive'), {
      response: { data: { detail: 'Usuario inactivo' } },
    })
    vi.mocked(useAuth).mockReturnValue({
      login: vi.fn().mockRejectedValue(inactiveError),
    } as any)

    const { unmount } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: 'inactive@test.com' } })
    fireEvent.change(screen.getByPlaceholderText(/contraseña/i), { target: { value: 'pass' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(screen.getByText(/usuario inactivo/i)).toBeDefined()
    })
    unmount()
  })

  it('redirects to /proposals on successful login', async () => {
    vi.mocked(useAuth).mockReturnValue({
      login: vi.fn().mockResolvedValue(undefined),
    } as any)

    const { unmount } = render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    )

    fireEvent.change(screen.getByPlaceholderText(/email/i), { target: { value: 'test@test.com' } })
    fireEvent.change(screen.getByPlaceholderText(/contraseña/i), { target: { value: 'pass' } })
    fireEvent.click(screen.getByRole('button', { name: /iniciar sesión/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/proposals')
    })
    unmount()
  })
})
