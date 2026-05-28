import React, { useState, useEffect, useRef, useMemo } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { proposalApi } from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import {
  Proposal,
  STATUS_LABELS,
  Approval,
  ApprovalRole,
  ROLE_LABELS,
  ApproveRequest,
  RejectRequest,
} from '../types'
import ProposalEditor, { type ProposalEditorHandle } from '../components/ProposalEditor'

const ProposalDetailPage: React.FC = () => {
  const { user } = useAuth()
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const editorRef = useRef<ProposalEditorHandle>(null)
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [approvals, setApprovals] = useState<Approval[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isGenerating, setIsGenerating] = useState<string | null>(null)
  const [isGeneratingInnti, setIsGeneratingInnti] = useState(false)
  const [proposalVersion, setProposalVersion] = useState(0)
  const [showApprovalModal, setShowApprovalModal] = useState(false)
  const [approvalForm, setApprovalForm] = useState<{
    approver_name: string
    approver_email: string
    role: ApprovalRole
    comments: string
    action: 'approved' | 'rejected'
  }>({
    approver_name: '',
    approver_email: '',
    role: 'reviewer',
    comments: '',
    action: 'approved',
  })

  useEffect(() => {
    const fetchProposalAndApprovals = async () => {
      if (!id) return
      try {
        setIsLoading(true)
        const [proposalRes, approvalsRes] = await Promise.all([
          proposalApi.get(parseInt(id)),
          proposalApi.getApprovals(parseInt(id)),
        ])
        setProposal(proposalRes.data)
        setApprovals(approvalsRes.data)
      } catch (err) {
        console.error('Error fetching data:', err)
        setError('No se pudo cargar la propuesta.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchProposalAndApprovals()
  }, [id])

  const handleGenerateDocument = async (type: 'word' | 'pdf' | 'annex') => {
    if (!proposal) return

    // Auto-guardar cambios pendientes antes de generar para que el backend
    // trabaje con el contenido más reciente del editor, no con el estado de la BD.
    if (editorRef.current?.hasUnsavedChanges) {
      try {
        await editorRef.current.save(true) // silent=true: sin alert de éxito
      } catch {
        alert('No se pudo guardar el contenido antes de generar. Guarda manualmente e intenta de nuevo.')
        return
      }
    }

    setIsGenerating(type)
    try {
      let response
      if (type === 'annex') {
        response = await proposalApi.generateAnnex(proposal.id)
      } else if (type === 'pdf') {
        // use_innti=false: solo genera con el contenido guardado en BD.
        // La generación con IA se hace desde el botón "Generar con Innti".
        response = await proposalApi.generatePdf(proposal.id, false)
      } else {
        // use_innti=false: mismo motivo — evita llamada a Innti al descargar Word.
        response = await proposalApi.generateDocument(proposal.id, false)
      }

      // Usar el Content-Type real de la respuesta para detectar si el backend
      // devolvió un ZIP (documentos separados) en lugar de un archivo único.
      // response.headers['content-type'] puede ser string | AxiosHeaders | …
      // String() normaliza cualquier valor al string que necesitamos.
      const contentType = String(
        response.headers['content-type'] ?? 'application/octet-stream'
      )
      const isZip = contentType.includes('zip')
      const mimeType = contentType.split(';')[0].trim()
      const extension = isZip ? 'zip' : type === 'pdf' ? 'pdf' : 'docx'
      const filename = `propuesta_${proposal.id}_${type}.${extension}`

      const blob = new Blob([response.data], { type: mimeType })
      const url = window.URL.createObjectURL(blob)

      // Usar <a download> en lugar de window.open para garantizar la descarga
      // sin que los bloqueadores de popups interfieran.
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = filename
      document.body.appendChild(anchor)
      anchor.click()
      document.body.removeChild(anchor)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error(`Error generating ${type}:`, err)
      alert(`Error al generar el documento ${type}.`)
    } finally {
      setIsGenerating(null)
    }
  }

  const handleGenerateWithInnti = async () => {
    if (!proposal) return
    if (!confirm('¿Generar contenido con Innti? Esto sobreescribirá el contenido actual.')) return

    setIsGeneratingInnti(true)
    try {
      await proposalApi.generateDocument(proposal.id, true)
      const [proposalRes, approvalsRes] = await Promise.all([
        proposalApi.get(proposal.id),
        proposalApi.getApprovals(proposal.id),
      ])
      setProposal(proposalRes.data)
      setApprovals(approvalsRes.data)
      setProposalVersion(v => v + 1)

      // Llamada imperativa directa: actualiza el editor con datos frescos sin
      // depender de la cadena reactiva memo→prop→effect.
      editorRef.current?.refreshContent({
        context_content: proposalRes.data.context_content || '',
        scope_content: proposalRes.data.scope_content || '',
        validity_period: proposalRes.data.validity_period || '',
        economic_conditions: proposalRes.data.economic_conditions || '',
        payment_terms: proposalRes.data.payment_terms || '',
        excluded_services: proposalRes.data.excluded_services || '',
        ip_section: proposalRes.data.ip_section || '',
        letter_content: proposalRes.data.letter_content || '',
      })

      alert('Contenido generado con Innti exitosamente.')
    } catch (err) {
      console.error('Error generating with Innti:', err)
      alert('Error al generar contenido con Innti.')
    } finally {
      setIsGeneratingInnti(false)
    }
  }

  const handleSubmitForReview = async () => {
    if (!proposal) return
    const isSentToClient = proposal.status === 'approved'

    const CONFIRM_MESSAGES: Partial<Record<typeof proposal.status, string>> = {
      draft: '¿Enviar esta propuesta a revisión? Ya no podrás editarla directamente.',
      reviewed: '¿Enviar esta propuesta al VP para aprobación final?',
      approved: '¿Marcar esta propuesta como enviada al cliente?',
      rejected: '¿Restaurar esta propuesta a borrador para continuar editándola?',
    }
    const confirmMsg = CONFIRM_MESSAGES[proposal.status] ?? '¿Estás seguro?'

    if (!confirm(confirmMsg)) return

    setIsSubmitting(true)
    try {
      if (isSentToClient) {
        await proposalApi.markSentToClient(proposal.id)
      } else {
        await proposalApi.submitForReview(proposal.id)
      }
      const [proposalRes, approvalsRes] = await Promise.all([
        proposalApi.get(proposal.id),
        proposalApi.getApprovals(proposal.id),
      ])
      setProposal(proposalRes.data)
      setApprovals(approvalsRes.data)
      alert(isSentToClient ? 'Propuesta marcada como enviada.' : 'Propuesta enviada a revisión exitosamente.')
    } catch (err) {
      console.error('Error submitting for review:', err)
      alert('Error al procesar la solicitud.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleApprovalAction = (action: 'approved' | 'rejected') => {
    if (!proposal) return
    let role: ApprovalRole = 'reviewer'
    if (proposal.status === 'pending_vp') {
      role = 'vp'
    }

    setApprovalForm({
      approver_name: '',
      approver_email: '',
      role,
      comments: '',
      action,
    })
    setShowApprovalModal(true)
  }

  const handleSubmitApproval = async () => {
    if (!proposal) return
    if (!approvalForm.approver_name) {
      alert('El nombre del aprobador es obligatorio.')
      return
    }
    if (approvalForm.action === 'rejected' && !approvalForm.comments) {
      alert('Los comentarios son obligatorios al rechazar.')
      return
    }

    setIsSubmitting(true)
    try {
      if (approvalForm.action === 'approved') {
        const data: ApproveRequest = {
          approver_name: approvalForm.approver_name,
          approver_email: approvalForm.approver_email || undefined,
          role: approvalForm.role,
          action: 'approved',
          comments: approvalForm.comments,
        }
        await proposalApi.approve(proposal.id, data)
      } else {
        const data: RejectRequest = {
          approver_name: approvalForm.approver_name,
          approver_email: approvalForm.approver_email || undefined,
          role: approvalForm.role,
          action: 'rejected',
          comments: approvalForm.comments,
        }
        await proposalApi.reject(proposal.id, data)
      }

      const [proposalRes, approvalsRes] = await Promise.all([
        proposalApi.get(proposal.id),
        proposalApi.getApprovals(proposal.id),
      ])
      setProposal(proposalRes.data)
      setApprovals(approvalsRes.data)
      setShowApprovalModal(false)
      alert(approvalForm.action === 'approved' ? 'Propuesta aprobada.' : 'Propuesta rechazada.')
    } catch (err) {
      console.error('Error submitting approval:', err)
      alert('Error al procesar la aprobación/rechazo.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const getStatusBadgeClass = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-800 border-gray-300'
      case 'pending_review': return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'approved': return 'bg-green-100 text-green-800 border-green-300'
      case 'rejected': return 'bg-red-100 text-red-800 border-red-300'
      default: return 'bg-yellow-100 text-yellow-800 border-yellow-300'
    }
  }

  const renderActionButtons = () => {
    if (!proposal || !user) return null

    switch (proposal.status) {
      case 'draft':
        if (user.role !== 'creator') return null
        return (
          <button
            onClick={handleSubmitForReview}
            disabled={isSubmitting}
            className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium shadow hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Enviando...' : 'Enviar a Revisión'}
          </button>
        )
      case 'pending_review':
        if (user.role !== 'approver_1') return null
        return (
          <div className="flex space-x-3">
            <button
              onClick={() => handleApprovalAction('approved')}
              disabled={isSubmitting}
              className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium shadow hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              ✅ Aprobar (Ángela)
            </button>
            <button
              onClick={() => handleApprovalAction('rejected')}
              disabled={isSubmitting}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium shadow hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              ❌ Rechazar
            </button>
          </div>
        )
      case 'reviewed':
        if (user.role !== 'creator') return null
        return (
          <button
            onClick={handleSubmitForReview}
            disabled={isSubmitting}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium shadow hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Enviando...' : 'Enviar a VP →'}
          </button>
        )
      case 'pending_vp':
        if (user.role !== 'approver_2') return null
        return (
          <div className="flex space-x-3">
            <button
              onClick={() => handleApprovalAction('approved')}
              disabled={isSubmitting}
              className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium shadow hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              ✅ Aprobar (Juan Pablo)
            </button>
            <button
              onClick={() => handleApprovalAction('rejected')}
              disabled={isSubmitting}
              className="px-4 py-2 bg-red-600 text-white rounded-lg font-medium shadow hover:bg-red-700 transition-colors disabled:opacity-50"
            >
              ❌ Rechazar
            </button>
          </div>
        )
      case 'approved':
        if (user.role !== 'creator') return null
        return (
          <button
            onClick={handleSubmitForReview}
            disabled={isSubmitting}
            className="px-6 py-2 bg-orange-500 text-white rounded-lg font-medium shadow hover:bg-orange-600 transition-colors disabled:opacity-50"
          >
            📤 Marcar como Enviada al Cliente
          </button>
        )
      case 'rejected':
        if (user.role !== 'creator') return null
        return (
          <button
            onClick={handleSubmitForReview}
            disabled={isSubmitting}
            className="px-6 py-2 bg-gray-600 text-white rounded-lg font-medium shadow hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            ↩ Volver a Borrador
          </button>
        )
      default:
        return null
    }
  }

  const editorInitialContent = useMemo(() => ({
    context_content: proposal?.context_content || '',
    scope_content: proposal?.scope_content || '',
    validity_period: proposal?.validity_period || '',
    economic_conditions: proposal?.economic_conditions || '',
    payment_terms: proposal?.payment_terms || '',
    excluded_services: proposal?.excluded_services || '',
    ip_section: proposal?.ip_section || '',
    letter_content: proposal?.letter_content || '',
  }), [proposal?.id, proposalVersion]) // eslint-disable-line react-hooks/exhaustive-deps

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !proposal) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg">
        {error || 'Propuesta no encontrada.'}
        <button onClick={() => navigate('/proposals')} className="ml-4 underline">Volver a la lista</button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{proposal.title}</h1>
          <div className="flex items-center space-x-3 mt-1">
            <span className="text-sm font-mono text-gray-500">{proposal.code || 'SIN CÓDIGO'}</span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusBadgeClass(proposal.status)}`}>
              {STATUS_LABELS[proposal.status]}
            </span>
          </div>
        </div>
        
        {renderActionButtons()}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <ProposalEditor
            ref={editorRef}
            key={proposal.id}
            proposalId={proposal.id}
            initialContent={editorInitialContent}
          />

          {/* Historial de Aprobaciones */}
          <div className="bg-white rounded-lg shadow border overflow-hidden">
            <div className="px-4 py-3 border-b bg-gray-50">
              <h3 className="text-sm font-semibold text-gray-900">Historial de Aprobaciones</h3>
            </div>
            <div className="p-4">
              {approvals.length === 0 ? (
                <p className="text-sm text-gray-500 italic">Sin aprobaciones registradas</p>
              ) : (
                <div className="space-y-4">
                  {approvals.map((approval) => (
                    <div key={approval.id} className="flex items-start space-x-3 text-sm border-b pb-3 last:border-0 last:pb-0">
                      <div className={`mt-0.5 px-2 py-0.5 rounded text-xs font-medium ${
                        approval.action === 'approved' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {approval.action === 'approved' ? '✅' : '❌'}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-semibold text-gray-900">{approval.approver_name}</span>
                          <span className="text-gray-400">•</span>
                          <span className="text-gray-600">{ROLE_LABELS[approval.role]}</span>
                          <span className="text-gray-400">•</span>
                          <span className="text-gray-500">{new Date(approval.created_at).toLocaleString()}</span>
                        </div>
                        {approval.comments && (
                          <p className="mt-1 text-gray-700 bg-gray-50 p-2 rounded border border-gray-100 italic">
                            "{approval.comments}"
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="font-semibold text-gray-900 mb-4">Acciones de Documento</h3>
            <div className="space-y-2">
              {proposal.status === 'draft' && (user?.role === 'creator' || user?.role === 'approver_1') && (
                <>
                  <button
                    onClick={handleGenerateWithInnti}
                    disabled={isGeneratingInnti}
                    className="w-full text-center px-4 py-2 text-sm bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 flex items-center justify-center space-x-2 disabled:opacity-50 mb-2"
                  >
                    <span>✨ Generar con Innti</span>
                    {isGeneratingInnti && <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>}
                  </button>
                  <hr className="my-3 border-gray-100" />
                </>
              )}
              <button
                onClick={() => handleGenerateDocument('word')}
                disabled={!!isGenerating}
                className="w-full text-left px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 flex items-center justify-between disabled:opacity-50"
              >
                <span>Generar Word</span>
                {isGenerating === 'word' && <span className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></span>}
              </button>
              <button
                onClick={() => handleGenerateDocument('pdf')}
                disabled={!!isGenerating}
                className="w-full text-left px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 flex items-center justify-between disabled:opacity-50"
              >
                <span>Generar PDF</span>
                {isGenerating === 'pdf' && <span className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></span>}
              </button>
              <button
                onClick={() => handleGenerateDocument('annex')}
                disabled={!!isGenerating}
                className="w-full text-left px-4 py-2 text-sm border rounded-lg hover:bg-gray-50 flex items-center justify-between disabled:opacity-50"
              >
                <span>Generar Anexo Técnico</span>
                {isGenerating === 'annex' && <span className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full"></span>}
              </button>
            </div>
          </div>

          <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <h4 className="text-sm font-semibold text-blue-800 mb-2">Información de la Propuesta</h4>
            <ul className="text-xs space-y-2 text-blue-700">
              <li><strong>Creada:</strong> {new Date(proposal.created_at).toLocaleDateString()}</li>
              <li><strong>Última actualización:</strong> {new Date(proposal.updated_at).toLocaleDateString()}</li>
              <li><strong>Productos:</strong> {proposal.products.length}</li>
              <li><strong>Esquemas:</strong> {proposal.schemes.length}</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Modal de Aprobación */}
      {showApprovalModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
          <div className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden">
            <div className={`px-6 py-4 border-b ${approvalForm.action === 'approved' ? 'bg-green-50' : 'bg-red-50'}`}>
              <h3 className="text-lg font-bold text-gray-900">
                {approvalForm.action === 'approved' ? 'Aprobar propuesta' : 'Rechazar propuesta'}
              </h3>
              <p className="text-sm text-gray-600">
                Como {ROLE_LABELS[approvalForm.role]}
              </p>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nombre del aprobador *</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={approvalForm.approver_name}
                  onChange={(e) => setApprovalForm({ ...approvalForm, approver_name: e.target.value })}
                  placeholder="Ej: Ángela Maria"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email (opcional)</label>
                <input
                  type="email"
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  value={approvalForm.approver_email}
                  onChange={(e) => setApprovalForm({ ...approvalForm, approver_email: e.target.value })}
                  placeholder="email@quipux.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Comentarios {approvalForm.action === 'rejected' ? '*' : '(opcional)'}
                </label>
                <textarea
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 h-24"
                  value={approvalForm.comments}
                  onChange={(e) => setApprovalForm({ ...approvalForm, comments: e.target.value })}
                  placeholder={approvalForm.action === 'rejected' ? 'Indique el motivo del rechazo...' : 'Opcional...'}
                />
              </div>
            </div>
            <div className="px-6 py-4 bg-gray-50 border-t flex justify-end space-x-3">
              <button
                onClick={() => setShowApprovalModal(false)}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
              >
                Cancelar
              </button>
              <button
                onClick={handleSubmitApproval}
                disabled={isSubmitting}
                className={`px-4 py-2 text-sm font-medium text-white rounded-lg shadow disabled:opacity-50 ${
                  approvalForm.action === 'approved' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'
                }`}
              >
                {isSubmitting ? 'Procesando...' : 'Confirmar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProposalDetailPage
