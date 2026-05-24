import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { proposalApi } from '../services/api'
import { STATUS_LABELS } from '../types'
import type { Proposal, ProposalStatus } from '../types'

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
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    proposalApi.list()
      .then((res) => setProposals(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

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
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
