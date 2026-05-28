import { useState, useEffect, useCallback } from 'react'
import { userApi } from '../services/api'
import type { AppUser, UserCreate, UserUpdate, UserRole } from '../types'
import { USER_ROLE_LABELS } from '../types'

const ALL_ROLES: UserRole[] = ['admin', 'creator', 'approver_1', 'approver_2', 'viewer']

const ROLE_BADGE_COLORS: Record<UserRole, string> = {
  admin: 'bg-red-100 text-red-800',
  creator: 'bg-green-100 text-green-800',
  approver_1: 'bg-purple-100 text-purple-800',
  approver_2: 'bg-orange-100 text-orange-800',
  viewer: 'bg-gray-100 text-gray-800',
}

interface UserModalProps {
  user: AppUser | null
  onClose: () => void
  onSave: () => void
}

function UserModal({ user, onClose, onSave }: UserModalProps) {
  const isEditing = !!user
  const [fullName, setFullName] = useState(user?.full_name ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [role, setRole] = useState<UserRole>(user?.role ?? 'creator')
  const [password, setPassword] = useState('')
  const [isActive, setIsActive] = useState(user?.is_active ?? true)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!isEditing && !password) {
      setError('La contraseña es obligatoria para nuevos usuarios.')
      return
    }

    setLoading(true)
    try {
      if (isEditing) {
        const updateData: UserUpdate = { full_name: fullName, email, role, is_active: isActive }
        if (password) updateData.new_password = password
        await userApi.update(user.id, updateData)
      } else {
        const createData: UserCreate = { full_name: fullName, email, role, password }
        await userApi.create(createData)
      }
      onSave()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Error al guardar el usuario.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            {isEditing ? 'Editar usuario' : 'Nuevo usuario'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl leading-none">&times;</button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">{error}</div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Nombre completo</label>
            <input
              type="text"
              value={fullName}
              onChange={e => setFullName(e.target.value)}
              required
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Nombre completo"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Correo electrónico</label>
            <input
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              required
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="usuario@quipux.com"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Rol</label>
            <select
              value={role}
              onChange={e => setRole(e.target.value as UserRole)}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {ALL_ROLES.map(r => (
                <option key={r} value={r}>{USER_ROLE_LABELS[r]}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {isEditing ? 'Nueva contraseña (dejar vacío para no cambiar)' : 'Contraseña'}
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required={!isEditing}
              className="w-full border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder={isEditing ? 'Sin cambios' : 'Contraseña segura'}
            />
          </div>

          {isEditing && (
            <div className="flex items-center gap-2">
              <input
                id="is-active"
                type="checkbox"
                checked={isActive}
                onChange={e => setIsActive(e.target.checked)}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded"
              />
              <label htmlFor="is-active" className="text-sm font-medium text-gray-700">Usuario activo</label>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 rounded transition-colors"
            >
              {loading ? 'Guardando...' : isEditing ? 'Guardar cambios' : 'Crear usuario'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const [users, setUsers] = useState<AppUser[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showInactive, setShowInactive] = useState(false)
  const [modalUser, setModalUser] = useState<AppUser | null | undefined>(undefined)
  const [confirmDeactivate, setConfirmDeactivate] = useState<AppUser | null>(null)
  const [deactivating, setDeactivating] = useState(false)

  const loadUsers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await userApi.list(undefined, showInactive)
      setUsers(resp.data)
    } catch {
      setError('No se pudo cargar la lista de usuarios.')
    } finally {
      setLoading(false)
    }
  }, [showInactive])

  useEffect(() => { loadUsers() }, [loadUsers])

  const handleDeactivate = async () => {
    if (!confirmDeactivate) return
    setDeactivating(true)
    try {
      await userApi.deactivate(confirmDeactivate.id)
      setConfirmDeactivate(null)
      loadUsers()
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setError(msg ?? 'Error al desactivar el usuario.')
      setConfirmDeactivate(null)
    } finally {
      setDeactivating(false)
    }
  }

  const activeCount = users.filter(u => u.is_active).length

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Gestión de Usuarios</h1>
          <p className="text-sm text-gray-500 mt-1">
            {activeCount} usuario{activeCount !== 1 ? 's' : ''} activo{activeCount !== 1 ? 's' : ''}
            {showInactive && users.length > activeCount ? ` · ${users.length - activeCount} inactivo${users.length - activeCount !== 1 ? 's' : ''}` : ''}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={e => setShowInactive(e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded"
            />
            Mostrar inactivos
          </label>
          <button
            onClick={() => setModalUser(null)}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors"
          >
            + Nuevo usuario
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded text-sm">{error}</div>
      )}

      {/* Tabla */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-16 text-gray-400">Cargando usuarios...</div>
        ) : users.length === 0 ? (
          <div className="flex items-center justify-center py-16 text-gray-400">No hay usuarios registrados.</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Nombre</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Correo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rol</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Estado</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {users.map(user => (
                <tr key={user.id} className={user.is_active ? '' : 'opacity-50'}>
                  <td className="px-6 py-4 text-sm font-medium text-gray-900 whitespace-nowrap">{user.full_name}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 whitespace-nowrap">{user.email}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_BADGE_COLORS[user.role]}`}>
                      {USER_ROLE_LABELS[user.role]}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-medium ${
                      user.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-500'
                    }`}>
                      {user.is_active ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right whitespace-nowrap">
                    <div className="flex items-center justify-end gap-2">
                      <button
                        onClick={() => setModalUser(user)}
                        className="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 rounded transition-colors"
                      >
                        Editar
                      </button>
                      {user.is_active && (
                        <button
                          onClick={() => setConfirmDeactivate(user)}
                          className="px-3 py-1 text-xs font-medium text-red-700 bg-red-50 hover:bg-red-100 rounded transition-colors"
                        >
                          Desactivar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Modal crear/editar */}
      {modalUser !== undefined && (
        <UserModal
          user={modalUser}
          onClose={() => setModalUser(undefined)}
          onSave={() => { setModalUser(undefined); loadUsers() }}
        />
      )}

      {/* Confirmación desactivar */}
      {confirmDeactivate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-sm p-6 space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">¿Desactivar usuario?</h3>
            <p className="text-sm text-gray-600">
              El usuario <strong>{confirmDeactivate.full_name}</strong> no podrá iniciar sesión mientras esté inactivo.
              Puedes reactivarlo editando su perfil.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setConfirmDeactivate(null)}
                className="flex-1 px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleDeactivate}
                disabled={deactivating}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 disabled:opacity-50 rounded transition-colors"
              >
                {deactivating ? 'Desactivando...' : 'Sí, desactivar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
