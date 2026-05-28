/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { AuthProvider, useAuth } from './AuthContext'
import api from '../services/api'

vi.mock('../services/api')

const TestComponent = () => {
  const { user, login, logout } = useAuth()
  return (
    <div>
      <div data-testid="user-email">{user?.email}</div>
      <button onClick={() => login('test@test.com', 'pass').catch(() => {})} data-testid="login-btn">Login</button>
      <button onClick={logout} data-testid="logout-btn">Logout</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('login exitoso', async () => {
    const mockToken = 'header.' + btoa(JSON.stringify({ sub: 'test@test.com', user_id: 1, role: 'creator', exp: Math.floor(Date.now() / 1000) + 3600 })) + '.signature'
    vi.mocked(api.post).mockResolvedValue({ data: { access_token: mockToken } })
    vi.mocked(api.get).mockResolvedValue({ data: { id: 1, email: 'test@test.com', full_name: 'Test User', role: 'creator' } })

    const { getByTestId, unmount } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    getByTestId('login-btn').click()

    await waitFor(() => {
      expect(localStorage.getItem('innti_token')).toBe(mockToken)
      expect(getByTestId('user-email').textContent).toBe('test@test.com')
    })
    unmount()
  })

  it('login con credenciales inválidas (401)', async () => {
    vi.mocked(api.post).mockRejectedValue({ response: { status: 401 } })

    const { getByTestId, unmount } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    try {
      getByTestId('login-btn').click()
    } catch (e) {}

    await waitFor(() => {
      expect(getByTestId('user-email').textContent).toBe('')
    })
    unmount()
  })

  it('logout', async () => {
    localStorage.setItem('innti_token', 'some-token')
    const { getByTestId, unmount } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    getByTestId('logout-btn').click()

    expect(localStorage.getItem('innti_token')).toBeNull()
    expect(getByTestId('user-email').textContent).toBe('')
    unmount()
  })

  it('restaura sesión desde localStorage', async () => {
    const mockToken = 'header.' + btoa(JSON.stringify({ sub: 'test@test.com', user_id: 1, role: 'creator', exp: Math.floor(Date.now() / 1000) + 3600 })) + '.signature'
    localStorage.setItem('innti_token', mockToken)
    vi.mocked(api.get).mockResolvedValue({ data: { id: 1, email: 'test@test.com', full_name: 'Test User', role: 'creator' } })

    const { getByTestId, unmount } = render(
      <AuthProvider>
        <TestComponent />
      </AuthProvider>
    )

    await waitFor(() => {
      expect(getByTestId('user-email').textContent).toBe('test@test.com')
    })
    unmount()
  })
})
