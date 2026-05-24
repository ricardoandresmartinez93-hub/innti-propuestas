import { Outlet, Link, useLocation } from 'react-router-dom'

export default function Layout() {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Inicio' },
    { path: '/proposals', label: 'Propuestas' },
    { path: '/proposals/new', label: 'Nueva Propuesta' },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-quipux-dark text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <h1 className="text-xl font-bold">Innti Propuestas</h1>
            <span className="text-xs bg-blue-600 px-2 py-1 rounded">MVP</span>
          </div>
          <nav className="flex space-x-4">
            {navItems.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`px-3 py-2 rounded text-sm transition-colors ${
                  location.pathname === item.path
                    ? 'bg-white/20 font-medium'
                    : 'hover:bg-white/10'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        <Outlet />
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 border-t mt-auto">
        <div className="max-w-7xl mx-auto px-4 py-3 text-center text-sm text-gray-500">
          Quipux S.A.S. - Innti Propuestas MVP v0.1.0
        </div>
      </footer>
    </div>
  )
}
