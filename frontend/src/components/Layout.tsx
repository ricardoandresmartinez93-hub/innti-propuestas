import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const getRoleBadge = (role: string) => {
    switch (role) {
      case 'admin': return { label: 'Administrador', color: 'bg-red-700' }
      case 'creator': return { label: 'Creador', color: 'bg-green-600' }
      case 'approver_1': return { label: 'Revisor', color: 'bg-purple-600' }
      case 'approver_2': return { label: 'VP', color: 'bg-orange-600' }
      case 'viewer': return { label: 'Visor', color: 'bg-gray-600' }
      default: return { label: role, color: 'bg-gray-600' }
    }
  }

  const badge = user ? getRoleBadge(user.role) : null

  const navItems = [
    { path: '/', label: 'Inicio' },
    { path: '/proposals', label: 'Propuestas' },
  ]

  if (user?.role === 'creator') {
    navItems.push({ path: '/proposals/new', label: 'Nueva Propuesta' })
  }

  if (user?.role === 'admin') {
    navItems.push({ path: '/admin', label: 'Usuarios' })
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-quipux-dark text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-6">
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
          
          <div className="flex items-center space-x-4">
            {user && (
              <>
                <div className="text-right hidden sm:block">
                  <div className="text-sm font-medium">{user.full_name || user.email}</div>
                  <div className={`text-[10px] inline-block px-2 py-0.5 rounded-full text-white ${badge?.color}`}>
                    {badge?.label}
                  </div>
                </div>
                <button
                  onClick={handleLogout}
                  className="text-sm bg-red-600/20 hover:bg-red-600/40 px-3 py-1.5 rounded border border-red-500/30 transition-colors"
                >
                  Cerrar sesión
                </button>
              </>
            )}
          </div>
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
