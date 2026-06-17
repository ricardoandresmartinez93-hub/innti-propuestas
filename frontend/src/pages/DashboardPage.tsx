import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { proposalApi } from '../services/api'
import { STATUS_LABELS } from '../types'
import type { Proposal, ProposalStatus, ProposalStats } from '../types'
import { useAuth } from '../contexts/AuthContext'

const STATUS_CARD_STYLES: Record<ProposalStatus, { bg: string; border: string; label: string; count: string }> = {
  draft:          { bg: 'bg-gray-50',   border: 'border-gray-200',   label: 'text-gray-500',   count: 'text-gray-800'   },
  pending_review: { bg: 'bg-yellow-50', border: 'border-yellow-200', label: 'text-yellow-600', count: 'text-yellow-900' },
  reviewed:       { bg: 'bg-blue-50',   border: 'border-blue-200',   label: 'text-blue-600',   count: 'text-blue-900'   },
  pending_vp:     { bg: 'bg-orange-50', border: 'border-orange-200', label: 'text-orange-600', count: 'text-orange-900' },
  approved:       { bg: 'bg-green-50',  border: 'border-green-200',  label: 'text-green-600',  count: 'text-green-900'  },
  rejected:       { bg: 'bg-red-50',    border: 'border-red-200',    label: 'text-red-600',    count: 'text-red-900'    },
  sent_to_client: { bg: 'bg-purple-50', border: 'border-purple-200', label: 'text-purple-600', count: 'text-purple-900' },
}

const STATUS_BADGE: Record<ProposalStatus, string> = {
  draft:          'bg-gray-100 text-gray-700',
  pending_review: 'bg-yellow-100 text-yellow-800',
  reviewed:       'bg-blue-100 text-blue-800',
  pending_vp:     'bg-orange-100 text-orange-800',
  approved:       'bg-green-100 text-green-800',
  rejected:       'bg-red-100 text-red-800',
  sent_to_client: 'bg-purple-100 text-purple-800',
}

const STATUS_ORDER: ProposalStatus[] = [
  'draft', 'pending_review', 'reviewed', 'pending_vp', 'approved', 'rejected', 'sent_to_client',
]

const ROLE_PENDING_STATUSES: Record<string, ProposalStatus[]> = {
  creator:    ['draft'],
  approver_1: ['pending_review'],
  approver_2: ['pending_vp'],
  admin:      ['pending_review', 'pending_vp'],
  viewer:     [],
}

function ProposalRow({ proposal }: { proposal: Proposal }) {
  return (
    <Link
      to={`/proposals/${proposal.id}`}
      className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors"
    >
      <div className="min-w-0">
        <p className="text-sm font-medium text-gray-900 truncate">{proposal.title}</p>
        {proposal.code && (
          <p className="text-xs text-gray-400 font-mono">{proposal.code}</p>
        )}
      </div>
      <div className="flex items-center gap-3 flex-shrink-0 ml-4">
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_BADGE[proposal.status]}`}>
          {STATUS_LABELS[proposal.status]}
        </span>
        <span className="text-xs text-gray-400 hidden sm:block">
          {new Date(proposal.updated_at).toLocaleDateString('es-CO')}
        </span>
      </div>
    </Link>
  )
}

export default function DashboardPage() {
  const { user } = useAuth()
  const [stats, setStats] = useState<ProposalStats | null>(null)
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([proposalApi.stats(), proposalApi.list(0, 20)])
      .then(([statsRes, listRes]) => {
        setStats(statsRes.data)
        setProposals(listRes.data)
      })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="text-center py-16 text-gray-400">Cargando...</div>
  }

  const pendingStatuses = user ? (ROLE_PENDING_STATUSES[user.role] ?? []) : []
  const pendingProposals = proposals.filter((p) => pendingStatuses.includes(p.status))
  const recentProposals = proposals.slice(0, 5)

  const today = new Date().toLocaleDateString('es-CO', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Hola, {user?.full_name?.split(' ')[0]}
        </h1>
        <p className="text-sm text-gray-500 mt-0.5 capitalize">{today}</p>
      </div>

      {/* Status cards */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7 gap-3">
          {STATUS_ORDER.map((s) => {
            const style = STATUS_CARD_STYLES[s]
            return (
              <div
                key={s}
                className={`${style.bg} ${style.border} border rounded-lg p-4 text-center`}
              >
                <p className={`text-3xl font-bold ${style.count}`}>{stats[s]}</p>
                <p className={`text-xs mt-1 font-medium leading-tight ${style.label}`}>
                  {STATUS_LABELS[s]}
                </p>
              </div>
            )
          })}
        </div>
      )}

      {/* Pending action */}
      {pendingStatuses.length > 0 && (
        <section>
          <h2 className="text-base font-semibold text-gray-800 mb-3">
            Pendientes de tu acción
          </h2>
          {pendingProposals.length === 0 ? (
            <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-700">
              Sin pendientes. ¡Todo al día!
            </div>
          ) : (
            <div className="bg-white border rounded-lg divide-y overflow-hidden">
              {pendingProposals.map((p) => (
                <ProposalRow key={p.id} proposal={p} />
              ))}
            </div>
          )}
        </section>
      )}

      {/* Recent activity */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-base font-semibold text-gray-800">Actividad reciente</h2>
          <Link to="/proposals" className="text-sm text-primary-600 hover:underline">
            Ver todas →
          </Link>
        </div>
        {recentProposals.length === 0 ? (
          <div className="text-center py-10 bg-white border rounded-lg">
            <p className="text-gray-400 text-sm mb-3">No hay propuestas aún.</p>
            <Link to="/proposals/new" className="text-sm text-primary-600 hover:underline">
              Crear la primera propuesta
            </Link>
          </div>
        ) : (
          <div className="bg-white border rounded-lg divide-y overflow-hidden">
            {recentProposals.map((p) => (
              <ProposalRow key={p.id} proposal={p} />
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
