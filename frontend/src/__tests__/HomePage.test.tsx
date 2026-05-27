/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'
import { MemoryRouter } from 'react-router-dom'
import HomePage from '../pages/HomePage'

afterEach(cleanup)

const renderPage = () =>
  render(
    <MemoryRouter>
      <HomePage />
    </MemoryRouter>
  )

describe('HomePage', () => {
  it('muestra el título principal', () => {
    renderPage()
    expect(
      screen.getByText('Gestión de Propuestas Comerciales')
    ).toBeInTheDocument()
  })

  it('muestra el párrafo descriptivo', () => {
    renderPage()
    expect(
      screen.getByText(/Genera propuestas comerciales profesionales/i)
    ).toBeInTheDocument()
  })

  it('el enlace "Crear Nueva Propuesta" apunta a /proposals/new', () => {
    renderPage()
    const link = screen.getByRole('link', { name: /Crear Nueva Propuesta/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/proposals/new')
  })

  it('el enlace "Ver Propuestas" apunta a /proposals', () => {
    renderPage()
    const link = screen.getByRole('link', { name: /Ver Propuestas/i })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/proposals')
  })
})
