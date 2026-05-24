import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <div className="text-center py-16">
      <h2 className="text-3xl font-bold text-quipux-dark mb-4">
        Gestión de Propuestas Comerciales
      </h2>
      <p className="text-gray-600 mb-8 max-w-2xl mx-auto">
        Genera propuestas comerciales profesionales para Quipux de forma rápida y
        estandarizada. Selecciona productos del portafolio, elige el esquema de
        propuesta y genera documentos listos para enviar al cliente.
      </p>
      <div className="flex justify-center space-x-4">
        <Link
          to="/proposals/new"
          className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition-colors font-medium"
        >
          Crear Nueva Propuesta
        </Link>
        <Link
          to="/proposals"
          className="bg-white text-primary-600 border border-primary-600 px-6 py-3 rounded-lg hover:bg-primary-50 transition-colors font-medium"
        >
          Ver Propuestas
        </Link>
      </div>
    </div>
  )
}
