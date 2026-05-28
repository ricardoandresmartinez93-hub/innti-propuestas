/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import ProtectedRoute from '../components/ProtectedRoute'
import { useAuth } from '../contexts/AuthContext'
import React from 'react'

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

describe('ProtectedRoute', () => {
  it('redirects to /login when user is null', () => {
    vi.mocked(useAuth).mockReturnValue({ user: null, isLoading: false } as any)
    const { unmount } = render(
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route path="/login" element={<div>Login Page</div>} />
          <Route path="/private" element={<ProtectedRoute><div>Private Content</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.getByText(/login page/i)).toBeDefined()
    unmount()
  })

  it('renders children when user is authenticated', () => {
    vi.mocked(useAuth).mockReturnValue({ user: { role: 'creator' }, isLoading: false } as any)
    const { unmount } = render(
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route path="/private" element={<ProtectedRoute><div>Private Content</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.getByText(/private content/i)).toBeDefined()
    unmount()
  })

  it('redirects to / when role is not allowed', () => {
    vi.mocked(useAuth).mockReturnValue({ user: { role: 'viewer' }, isLoading: false } as any)
    const { unmount } = render(
      <MemoryRouter initialEntries={['/private']}>
        <Routes>
          <Route path="/" element={<div>Home Page</div>} />
          <Route path="/private" element={<ProtectedRoute allowedRoles={['creator']}><div>Private Content</div></ProtectedRoute>} />
        </Routes>
      </MemoryRouter>
    )
    expect(screen.getByText(/home page/i)).toBeDefined()
    unmount()
  })
})
