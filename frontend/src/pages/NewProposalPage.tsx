import { useState, useEffect } from 'react'
import { portfolioApi } from '../services/api'
import { SCHEME_LABELS } from '../types'
import type { PortfolioProduct, SchemeType } from '../types'

/**
 * Página para crear una nueva propuesta comercial.
 * Paso 1: Seleccionar productos del portafolio
 * Paso 2: Configurar esquema(s) de propuesta
 * Paso 3: Datos del cliente
 *
 * TODO: Implementar con Innti (prompts en archivo de prompts).
 */
export default function NewProposalPage() {
  const [products, setProducts] = useState<PortfolioProduct[]>([])
  const [selectedProducts, setSelectedProducts] = useState<Set<string>>(new Set())
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    portfolioApi.listProducts()
      .then((res) => setProducts(res.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filteredProducts = products.filter((p) =>
    p.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const toggleProduct = (name: string) => {
    setSelectedProducts((prev) => {
      const next = new Set(prev)
      if (next.has(name)) next.delete(name)
      else next.add(name)
      return next
    })
  }

  return (
    <div>
      <h2 className="text-2xl font-bold text-quipux-dark mb-6">
        Nueva Propuesta Comercial
      </h2>

      {/* Paso 1: Selección de productos */}
      <div className="bg-white rounded-lg border p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">
          Paso 1: Seleccionar Productos del Portafolio
        </h3>
        <p className="text-sm text-gray-500 mb-4">
          Selecciona los productos y servicios que se incluirán en la propuesta.
          ({selectedProducts.size} seleccionados)
        </p>

        <input
          type="text"
          placeholder="Buscar producto..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full border rounded px-3 py-2 mb-4 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        />

        {loading ? (
          <p className="text-gray-500">Cargando portafolio...</p>
        ) : (
          <div className="max-h-96 overflow-y-auto border rounded">
            {filteredProducts.map((p) => (
              <label
                key={p.name}
                className="flex items-start px-4 py-3 hover:bg-gray-50 cursor-pointer border-b last:border-b-0"
              >
                <input
                  type="checkbox"
                  checked={selectedProducts.has(p.name)}
                  onChange={() => toggleProduct(p.name)}
                  className="mt-1 mr-3"
                />
                <div>
                  <span className="font-medium text-sm">{p.name}</span>
                  <span className="ml-2 text-xs bg-gray-100 px-2 py-0.5 rounded">
                    {p.product_type}
                  </span>
                  {p.description && (
                    <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                      {p.description.substring(0, 150)}...
                    </p>
                  )}
                </div>
              </label>
            ))}
          </div>
        )}
      </div>

      {/* Paso 2: Esquema (placeholder para implementación con Innti) */}
      <div className="bg-white rounded-lg border p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">
          Paso 2: Seleccionar Esquema de Propuesta
        </h3>
        <p className="text-sm text-gray-400">
          [Pendiente de implementación - Ver prompts para Innti]
        </p>
        <div className="grid grid-cols-2 gap-3 mt-4">
          {(Object.entries(SCHEME_LABELS) as [SchemeType, string][]).map(
            ([key, label]) => (
              <label key={key} className="flex items-center p-3 border rounded hover:bg-gray-50 cursor-pointer">
                <input type="checkbox" className="mr-3" />
                <span className="text-sm">{label}</span>
              </label>
            )
          )}
        </div>
      </div>

      {/* Paso 3: Datos del cliente (placeholder) */}
      <div className="bg-white rounded-lg border p-6 mb-6">
        <h3 className="text-lg font-semibold mb-4">
          Paso 3: Datos del Cliente
        </h3>
        <p className="text-sm text-gray-400">
          [Pendiente de implementación - Ver prompts para Innti]
        </p>
      </div>
    </div>
  )
}
