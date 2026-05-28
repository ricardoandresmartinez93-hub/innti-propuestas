import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { proposalApi } from '../services/api'
import { STATUS_LABELS } from '../types'
import type { Proposal, ProposalStatus } from '../types'
import { useAuth } from '../contexts/AuthContext'

const STATUS_COLORS: Record<ProposalStatus, string> = {
  draft: 'bg-gray-100 text-gray-800',
  pending_review: 'bg-yellow-100 text-yellow-800',
  reviewed: 'bg-blue-100 text-blue-800',
  pending_vp: 'bg-orange-100 text-orange-800',
  approved: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-800',
  sent_to_client: 'bg-purple-100 text-purple-800',
}

export default function ProposalListPage() {
  const { user } = useAuth()
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState<{ id: number; title: string } | null>(null)
  const [deletingId, setDeletingId] = useState<number | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    proposalApi.list()
      .then((res) => setProposals(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const handleDelete = async () => {
    if (!confirmDelete) return
    setDeletingId(confirmDelete.id)
    setDeleteError(null)
    try {
      await proposalApi.delete(confirmDelete.id)
      setProposals((prev) => prev.filter((p) => p.id !== confirmDelete.id))
      setConfirmDelete(null)
    } catch {
      setDeleteError('No se pudo eliminar la propuesta. Inténtalo de nuevo.')
    } finally {
      setDeletingId(null)
    }
  }

  const handleCancelDelete = () => {
    setConfirmDelete(null)
    setDeleteError(null)
  }

  if (loading) {
    return <div className="text-center py-8 text-gray-500">Cargando propuestas...</div>
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-quipux-dark">Propuestas</h2>
        <Link
          to="/proposals/new"
          className="bg-primary-600 text-white px-4 py-2 rounded hover:bg-primary-700 text-sm"
        >
          + Nueva Propuesta
        </Link>
      </div>

      {proposals.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg border">
          <p className="text-gray-500 mb-4">No hay propuestas creadas aún.</p>
          <Link to="/proposals/new" className="text-primary-600 hover:underline">
            Crear la primera propuesta
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Código</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Título</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Estado</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Fecha</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {proposals.map((p) => (
                <tr key={p.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-mono">{p.code || '-'}</td>
                  <td className="px-4 py-3 text-sm">{p.title}</td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-1 rounded-full ${STATUS_COLORS[p.status]}`}>
                      {STATUS_LABELS[p.status]}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(p.updated_at).toLocaleDateString('es-CO')}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <Link
                        to={`/proposals/${p.id}`}
                        className="text-xs px-3 py-1.5 rounded-md bg-primary-50 text-primary-700 hover:bg-primary-100 font-medium"
                      >
                        Editar
                        </Link>
                      {p.status === 'draft' && user?.role === 'creator' && (
                        <button
                          onClick={() => setConfirmDelete({ id: p.id, title: p.title })}
                          data-testid={`delete-btn-${p.id}`}
                          className="text-xs px-3 py-1.5 rounded-md bg-red-50 text-red-700 hover:bg-red-100 font-medium"
                        >
                          Eliminar
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {confirmDelete !== null && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-sm w-full p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-2">Eliminar propuesta</h3>
            <p className="text-sm text-gray-600 mb-4">
              ¿Eliminar{' '}
              <span className="font-semibold">"{confirmDelete.title}"</span>?{' '}
              Esta acción no se puede deshacer.
            </p>
            {deleteError !== null && (
              <p className="text-sm text-red-600 mb-3">{deleteError}</p>
            )}
            <div className="flex justify-end gap-3">
              <button
                onClick={handleCancelDelete}
                disabled={deletingId !== null}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleDelete}
                disabled={deletingId !== null}
                data-testid="confirm-delete-btn"
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {deletingId !== null ? 'Eliminando...' : 'Eliminar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
