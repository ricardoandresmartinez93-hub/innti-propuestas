import React, { useState } from 'react'
import { Client, ClientCreate } from '../types'
import { clientApi } from '../services/api'
import { COUNTRIES, getDepartments, getCities } from '../utils/locationData'

interface ClientFormProps {
  onClientCreated: (client: Client) => void
}

const ClientForm: React.FC<ClientFormProps> = ({ onClientCreated }) => {
  const [formData, setFormData] = useState<ClientCreate>({
    name: '',
    position: '',
    entity: '',
    country: '',
    department: '',
    city: '',
    email: '',
  })

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
  }

  const handleCountryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const country = e.target.value
    setFormData((prev) => ({ ...prev, country, department: '', city: '' }))
  }

  const handleDepartmentChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const department = e.target.value
    setFormData((prev) => ({ ...prev, department, city: '' }))
  }

  const handleCityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setFormData((prev) => ({ ...prev, city: e.target.value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!formData.name || !formData.entity) {
      setError('Nombre y Entidad son campos obligatorios.')
      return
    }

    setLoading(true)
    try {
      const response = await clientApi.create(formData)
      onClientCreated(response.data)
      setFormData({
        name: '',
        position: '',
        entity: '',
        country: '',
        department: '',
        city: '',
        email: '',
      })
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error al guardar el cliente.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4 bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-bold mb-4">Datos del Cliente</h2>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-2 rounded relative">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Nombre *</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-quipux-blue focus:ring-quipux-blue sm:text-sm border p-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Cargo</label>
          <input
            type="text"
            name="position"
            value={formData.position}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-quipux-blue focus:ring-quipux-blue sm:text-sm border p-2"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Entidad *</label>
          <input
            type="text"
            name="entity"
            value={formData.entity}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-quipux-blue focus:ring-quipux-blue sm:text-sm border p-2"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">País</label>
          <select
            name="country"
            value={formData.country}
            onChange={handleCountryChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-quipux-blue focus:ring-quipux-blue sm:text-sm border p-2 bg-white"
          >
            <option value="">Seleccione un país</option>
            {COUNTRIES.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Departamento</label>
          <select
            name="department"
            value={formData.department}
            onChange={handleDepartmentChange}
            disabled={!formData.country}
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm border p-2 bg-white ${
              !formData.country
                ? 'opacity-50 cursor-not-allowed'
                : 'focus:border-quipux-blue focus:ring-quipux-blue'
            }`}
          >
            <option value="">
              {formData.country ? 'Seleccione un departamento' : 'Primero seleccione un país'}
            </option>
            {getDepartments(formData.country ?? '').map((d) => (
              <option key={d} value={d}>{d}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Ciudad</label>
          <select
            name="city"
            value={formData.city}
            onChange={handleCityChange}
            disabled={!formData.department}
            className={`mt-1 block w-full rounded-md border-gray-300 shadow-sm sm:text-sm border p-2 bg-white ${
              !formData.department
                ? 'opacity-50 cursor-not-allowed'
                : 'focus:border-quipux-blue focus:ring-quipux-blue'
            }`}
          >
            <option value="">
              {formData.department ? 'Seleccione una ciudad' : 'Primero seleccione un departamento'}
            </option>
            {getCities(formData.country ?? '', formData.department ?? '').map((city) => (
              <option key={city} value={city}>{city}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-quipux-blue focus:ring-quipux-blue sm:text-sm border p-2"
          />
        </div>
      </div>

      <div className="pt-4">
        <button
          type="submit"
          disabled={loading}
          className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
            loading ? 'bg-quipux-blue opacity-70' : 'bg-quipux-blue hover:bg-blue-700'
          } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-quipux-blue`}
        >
          {loading ? 'Guardando...' : 'Guardar Cliente'}
        </button>
      </div>
    </form>
  )
}

export default ClientForm
