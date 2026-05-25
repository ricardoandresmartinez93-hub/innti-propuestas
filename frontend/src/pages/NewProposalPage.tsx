import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { portfolioApi, proposalApi } from '../services/api'
import { SCHEME_LABELS } from '../types'
import type { PortfolioProduct, ProposalScheme, Client, ProposalCreate } from '../types'
import SchemeSelector from '../components/SchemeSelector'
import ClientForm from '../components/ClientForm'

export default function NewProposalPage() {
  const navigate = useNavigate()
  const [currentStep, setCurrentStep] = useState(1)
  const [loading, setLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Data State
  const [products, setProducts] = useState<PortfolioProduct[]>([])
  const [selectedProducts, setSelectedProducts] = useState<PortfolioProduct[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  
  const [selectedSchemes, setSelectedSchemes] = useState<Omit<ProposalScheme, 'id'>[]>([])
  const [combineSchemes, setCombineSchemes] = useState(true)
  
  const [client, setClient] = useState<Client | null>(null)
  const [proposalTitle, setProposalTitle] = useState('')

  useEffect(() => {
    portfolioApi.listProducts()
      .then((res) => setProducts(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const toggleProduct = (product: PortfolioProduct) => {
    setSelectedProducts((prev) => {
      const exists = prev.find(p => p.name === product.name)
      if (exists) return prev.filter(p => p.name !== product.name)
      return [...prev, product]
    })
  }

  const handleCreateProposal = async () => {
    if (!client || !proposalTitle || selectedProducts.length === 0 || selectedSchemes.length === 0) return

    setIsSubmitting(true)
    try {
      const proposalData: ProposalCreate = {
        title: proposalTitle,
        client_id: client.id,
        combine_schemes: combineSchemes,
        products: selectedProducts.map(p => ({
          product_name: p.name,
          product_type: p.product_type,
          description: p.description
        })),
        schemes: selectedSchemes
      }
      
      const res = await proposalApi.create(proposalData)
      navigate(`/proposals/${res.data.id}`)
    } catch (error) {
      console.error('Error creating proposal:', error)
      alert('Error al crear la propuesta')
    } finally {
      setIsSubmitting(false)
    }
  }

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const steps = [
    { id: 1, name: 'Productos' },
    { id: 2, name: 'Esquemas' },
    { id: 3, name: 'Cliente' },
    { id: 4, name: 'Confirmación' },
  ]

  const canAdvance = () => {
    switch (currentStep) {
      case 1: return selectedProducts.length > 0
      case 2: return selectedSchemes.length > 0
      case 3: return client !== null
      case 4: return proposalTitle.trim().length > 0
      default: return false
    }
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h2 className="text-3xl font-bold text-quipux-dark mb-8 text-center">
        Nueva Propuesta Comercial
      </h2>

      {/* Stepper */}
      <nav className="mb-12">
        <ol className="flex items-center w-full">
          {steps.map((step, idx) => (
            <li key={step.id} className={`flex items-center ${idx !== steps.length - 1 ? 'w-full' : ''}`}>
              <div className="flex flex-col items-center relative">
                <div className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors ${
                  currentStep >= step.id ? 'bg-quipux-blue border-quipux-blue text-white' : 'bg-white border-gray-300 text-gray-500'
                }`}>
                  {step.id}
                </div>
                <span className={`absolute -bottom-7 text-xs font-medium whitespace-nowrap ${
                  currentStep >= step.id ? 'text-quipux-blue' : 'text-gray-500'
                }`}>
                  {step.name}
                </span>
              </div>
              {idx !== steps.length - 1 && (
                <div className={`flex-1 h-0.5 mx-4 transition-colors ${
                  currentStep > step.id ? 'bg-quipux-blue' : 'bg-gray-300'
                }`} />
              )}
            </li>
          ))}
        </ol>
      </nav>

      <div className="mt-12">
        {/* Step 1: Products */}
        {currentStep === 1 && (
          <div className="bg-white rounded-xl shadow-sm border p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center">
              <span className="bg-quipux-blue text-white w-8 h-8 rounded-full inline-flex items-center justify-center mr-3 text-sm">1</span>
              Seleccionar Productos del Portafolio
            </h3>
            
            <div className="mb-6">
              <input
                type="text"
                placeholder="Buscar productos y servicios..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-quipux-blue focus:border-quipux-blue outline-none transition-all"
              />
            </div>

            {loading ? (
              <div className="py-12 text-center text-gray-500">Cargando portafolio...</div>
            ) : (
              <div className="max-h-[400px] overflow-y-auto border border-gray-200 rounded-lg divide-y">
                {filteredProducts.map((p) => (
                  <label
                    key={p.name}
                    className={`flex items-start px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                      selectedProducts.some(sp => sp.name === p.name) ? 'bg-blue-50' : ''
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedProducts.some(sp => sp.name === p.name)}
                      onChange={() => toggleProduct(p)}
                      className="mt-1.5 mr-4 h-5 w-5 rounded border-gray-300 text-quipux-blue focus:ring-quipux-blue"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-bold text-gray-900">{p.name}</span>
                        <span className="text-xs font-semibold bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full uppercase tracking-wider">
                          {p.product_type}
                        </span>
                      </div>
                      {p.description && (
                        <p className="text-sm text-gray-600 line-clamp-2">{p.description}</p>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            )}
            <p className="mt-4 text-sm text-gray-500 italic">
              * Seleccionados: {selectedProducts.length}
            </p>
          </div>
        )}

        {/* Step 2: Schemes */}
        {currentStep === 2 && (
          <div className="bg-white rounded-xl shadow-sm border p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center">
              <span className="bg-quipux-blue text-white w-8 h-8 rounded-full inline-flex items-center justify-center mr-3 text-sm">2</span>
              Configurar Esquemas Comerciales
            </h3>
            <SchemeSelector 
              initialSchemes={selectedSchemes}
              initialCombine={combineSchemes}
              onSchemesChanged={(schemes, combine) => {
                setSelectedSchemes(schemes)
                setCombineSchemes(combine)
              }}
            />
          </div>
        )}

        {/* Step 3: Client */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <div className="bg-white rounded-xl shadow-sm border p-8">
              <h3 className="text-xl font-bold mb-6 flex items-center">
                <span className="bg-quipux-blue text-white w-8 h-8 rounded-full inline-flex items-center justify-center mr-3 text-sm">3</span>
                Información del Cliente
              </h3>
              
              {client ? (
                <div className="bg-green-50 border border-green-200 rounded-lg p-6 flex justify-between items-center">
                  <div>
                    <h4 className="font-bold text-green-900">{client.name}</h4>
                    <p className="text-sm text-green-800">{client.entity} - {client.position}</p>
                    <p className="text-xs text-green-700 mt-1">{client.email}</p>
                  </div>
                  <button 
                    onClick={() => setClient(null)}
                    className="text-sm text-green-700 font-medium hover:underline"
                  >
                    Cambiar
                  </button>
                </div>
              ) : (
                <ClientForm onClientCreated={(newClient) => {
                  setClient(newClient)
                }} />
              )}
            </div>
          </div>
        )}

        {/* Step 4: Summary */}
        {currentStep === 4 && (
          <div className="bg-white rounded-xl shadow-sm border p-8">
            <h3 className="text-xl font-bold mb-6 flex items-center">
              <span className="bg-quipux-blue text-white w-8 h-8 rounded-full inline-flex items-center justify-center mr-3 text-sm">4</span>
              Resumen y Título de la Propuesta
            </h3>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-bold text-gray-700 mb-2">
                  Título de la Propuesta *
                </label>
                <input
                  type="text"
                  placeholder="Ej: Propuesta Modernización Tránsito - Medellín"
                  value={proposalTitle}
                  onChange={(e) => setProposalTitle(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-quipux-blue focus:border-quipux-blue outline-none transition-all"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4">
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Productos</h4>
                  <ul className="text-sm space-y-1">
                    {selectedProducts.map(p => (
                      <li key={p.name} className="flex items-center">
                        <span className="w-1.5 h-1.5 bg-quipux-blue rounded-full mr-2" />
                        {p.name}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="text-xs font-bold text-gray-500 uppercase mb-3">Esquemas</h4>
                  <ul className="text-sm space-y-1">
                    {selectedSchemes.map(s => (
                      <li key={s.scheme_type} className="flex items-center">
                        <span className="w-1.5 h-1.5 bg-quipux-blue rounded-full mr-2" />
                        {SCHEME_LABELS[s.scheme_type]} ({s.payment_frequency})
                      </li>
                    ))}
                  </ul>
                  <p className="mt-2 text-[10px] text-gray-400">
                    Generación: {combineSchemes ? 'Documento único' : 'Documentos separados'}
                  </p>
                </div>
              </div>

              {client && (
                <div className="border rounded-lg p-4 bg-gray-50">
                  <h4 className="text-xs font-bold text-gray-500 uppercase mb-2">Cliente</h4>
                  <p className="text-sm font-medium">{client.name}</p>
                  <p className="text-xs text-gray-600">{client.entity} - {client.city}</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="mt-10 flex justify-between">
          <button
            onClick={() => setCurrentStep(prev => prev - 1)}
            disabled={currentStep === 1 || isSubmitting}
            className={`px-8 py-3 rounded-lg font-bold transition-all ${
              currentStep === 1 || isSubmitting
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
            }`}
          >
            Anterior
          </button>

          {currentStep < 4 ? (
            <button
              onClick={() => setCurrentStep(prev => prev + 1)}
              disabled={!canAdvance()}
              className={`px-10 py-3 rounded-lg font-bold shadow-lg transition-all ${
                !canAdvance()
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-quipux-blue text-white hover:bg-opacity-90'
              }`}
            >
              Siguiente
            </button>
          ) : (
            <button
              onClick={handleCreateProposal}
              disabled={!canAdvance() || isSubmitting}
              className={`px-10 py-3 rounded-lg font-bold shadow-lg transition-all ${
                !canAdvance() || isSubmitting
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-green-600 text-white hover:bg-green-700'
              }`}
            >
              {isSubmitting ? 'Creando...' : 'Crear Propuesta'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
