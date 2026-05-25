import React, { useState, useEffect } from 'react';
import { 
  SchemeType, 
  SCHEME_LABELS, 
  ProposalScheme 
} from '../types';

interface SchemeSelectorProps {
  onSchemesChanged: (schemes: Omit<ProposalScheme, 'id'>[], combineSchemes: boolean) => void;
  initialSchemes?: Omit<ProposalScheme, 'id'>[];
  initialCombine?: boolean;
}

const SCHEME_DESCRIPTIONS: Record<SchemeType, string> = {
  licensing: 'Concesión de derechos de uso de software o propiedad intelectual.',
  services: 'Prestación de servicios profesionales, consultoría o implementación.',
  support_maintenance: 'Servicios recurrentes para asegurar la continuidad y actualización.',
  concession_bpo: 'Externalización de procesos de negocio o concesión de servicios.',
  supply: 'Provisión de bienes físicos o consumibles necesarios.'
};

const PAYMENT_FREQUENCIES = [
  { value: 'Único', label: 'Único' },
  { value: 'Mensual', label: 'Mensual' },
  { value: 'Anual', label: 'Anual' }
];

const SchemeSelector: React.FC<SchemeSelectorProps> = ({ 
  onSchemesChanged, 
  initialSchemes = [], 
  initialCombine = true 
}) => {
  const [selectedSchemes, setSelectedSchemes] = useState<Record<SchemeType, boolean>>(() => {
    const initial: Partial<Record<SchemeType, boolean>> = {};
    (Object.keys(SCHEME_LABELS) as SchemeType[]).forEach(type => {
      initial[type] = initialSchemes.some(s => s.scheme_type === type);
    });
    return initial as Record<SchemeType, boolean>;
  });

  const [paymentFrequencies, setPaymentFrequencies] = useState<Record<SchemeType, string>>(() => {
    const initial: Partial<Record<SchemeType, string>> = {};
    (Object.keys(SCHEME_LABELS) as SchemeType[]).forEach(type => {
      const found = initialSchemes.find(s => s.scheme_type === type);
      initial[type] = found?.payment_frequency || 'Único';
    });
    return initial as Record<SchemeType, string>;
  });

  const [combineSchemes, setCombineSchemes] = useState(initialCombine);

  useEffect(() => {
    const schemes: Omit<ProposalScheme, 'id'>[] = (Object.keys(selectedSchemes) as SchemeType[])
      .filter(type => selectedSchemes[type])
      .map(type => ({
        scheme_type: type,
        payment_frequency: paymentFrequencies[type]
      }));
    
    onSchemesChanged(schemes, combineSchemes);
  }, [selectedSchemes, paymentFrequencies, combineSchemes]);

  const toggleScheme = (type: SchemeType) => {
    setSelectedSchemes(prev => ({
      ...prev,
      [type]: !prev[type]
    }));
  };

  const updateFrequency = (type: SchemeType, frequency: string) => {
    setPaymentFrequencies(prev => ({
      ...prev,
      [type]: frequency
    }));
  };

  const selectedCount = Object.values(selectedSchemes).filter(Boolean).length;

  return (
    <div className="space-y-6 bg-white p-6 rounded-lg border border-gray-200">
      <h3 className="text-lg font-medium text-gray-900">Esquemas de Propuesta</h3>
      
      <div className="grid gap-4">
        {(Object.keys(SCHEME_LABELS) as SchemeType[]).map((type) => (
          <div key={type} className="flex flex-col space-y-3 p-4 border rounded-md hover:bg-gray-50 transition-colors">
            <div className="flex items-start">
              <div className="flex items-center h-5">
                <input
                  id={`scheme-${type}`}
                  type="checkbox"
                  checked={selectedSchemes[type]}
                  onChange={() => toggleScheme(type)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
              </div>
              <div className="ml-3 text-sm">
                <label htmlFor={`scheme-${type}`} className="font-medium text-gray-700">
                  {SCHEME_LABELS[type]}
                </label>
                <p className="text-gray-500">{SCHEME_DESCRIPTIONS[type]}</p>
              </div>
            </div>

            {selectedSchemes[type] && (
              <div className="ml-7 pt-2 flex items-center space-x-4">
                <label className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                  Frecuencia de Pago:
                </label>
                <div className="flex space-x-2">
                  {PAYMENT_FREQUENCIES.map((freq) => (
                    <button
                      key={freq.value}
                      type="button"
                      onClick={() => updateFrequency(type, freq.value)}
                      className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                        paymentFrequencies[type] === freq.value
                          ? 'bg-blue-600 text-white border-blue-600'
                          : 'bg-white text-gray-600 border-gray-300 hover:border-blue-400'
                      }`}
                    >
                      {freq.label}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {selectedCount >= 2 && (
        <div className="mt-6 p-4 bg-blue-50 rounded-md border border-blue-100 flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-sm font-medium text-blue-900">Configuración de Documentos</span>
            <span className="text-xs text-blue-700">Has seleccionado {selectedCount} esquemas. ¿Cómo deseas generarlos?</span>
          </div>
          <div className="flex items-center bg-white p-1 rounded-lg border border-blue-200">
            <button
              type="button"
              onClick={() => setCombineSchemes(true)}
              className={`px-4 py-2 text-xs font-medium rounded-md transition-all ${
                combineSchemes 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Combinar en uno
            </button>
            <button
              type="button"
              onClick={() => setCombineSchemes(false)}
              className={`px-4 py-2 text-xs font-medium rounded-md transition-all ${
                !combineSchemes 
                  ? 'bg-blue-600 text-white shadow-sm' 
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Documentos separados
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SchemeSelector;
