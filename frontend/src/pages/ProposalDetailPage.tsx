import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { proposalApi } from '../services/api'
import { Proposal, STATUS_LABELS } from '../types'
import ProposalEditor from '../components/ProposalEditor'

const ProposalDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isGenerating, setIsGenerating] = useState<string | null>(null)

  useEffect(() => {
    const fetchProposal = async () => {
      if (!id) return
      try {
        setIsLoading(true)
        const response = await proposalApi.get(parseInt(id))
        setProposal(response.data)
      } catch (err) {
        console.error('Error fetching proposal:', err)
        setError('No se pudo cargar la propuesta.')
      } finally {
        setIsLoading(false)
      }
    }

    fetchProposal()
  }, [id])

  const handleGenerateDocument = async (type: 'word' | 'pdf' | 'annex') => {
    if (!proposal) return
    setIsGenerating(type)
    try {
      let response
      if (type === 'annex') {
        response = await proposalApi.generateAnnex(proposal.id)
      } else if (type === 'pdf') {
        response = await proposalApi.generatePdf(proposal.id, true)
      } else {
        response = await proposalApi.generateDocument(proposal.id, true)
      }
      
      const blob = new Blob([response.data], { 
        type: type === 'pdf' ? 'application/pdf' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' 
      })
      const url = window.URL.createObjectURL(blob)
      window.open(url, '_blank')
      // Optional: window.URL.revokeObjectURL(url) - though usually kept for preview
    } catch (err) {
      console.error(`Error generating ${type}:`, err)
      alert(`Error al generar el documento ${type}.`)
    } finally {
      setIsGenerating(null)
    }
  }

  const handleSubmitForReview = async () => {
    if (!proposal) return
    if (!confirm('¿Estás seguro de enviar esta propuesta a revisión? Ya no podrás editarla directamente.')) return

    setIsSubmitting(true)
    try {
      await proposalApi.submitForReview(proposal.id)
      const response = await proposalApi.get(proposal.id)
      setProposal(response.data)
      alert('Propuesta enviada a revisión exitosamente.')
    } catch (err) {
      console.error('Error submitting for review:', err)
      alert('Error al enviar a revisión.')
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
        
        {proposal.status === 'draft' && (
          <button
            onClick={handleSubmitForReview}
            disabled={isSubmitting}
            className="px-6 py-2 bg-green-600 text-white rounded-lg font-medium shadow hover:bg-green-700 transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Enviando...' : 'Enviar a Revisión'}
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <ProposalEditor 
            proposalId={proposal.id} 
            initialContent={{
              context_content: proposal.context_content || '',
              scope_content: proposal.scope_content || '',
              economic_conditions: proposal.economic_conditions || '',
              payment_terms: proposal.payment_terms || '',
            }} 
          />
        </div>

        <div className="space-y-4">
          <div className="bg-white p-4 rounded-lg shadow border">
            <h3 className="font-semibold text-gray-900 mb-4">Acciones de Documento</h3>
            <div className="space-y-2">
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
    </div>
  )
}

export default ProposalDetailPage
