import React, { useEffect, useState } from 'react';
import { SchemeType, SCHEME_LABELS } from '../types';
import type { PortfolioProduct, ProposalScheme } from '../types';

/** Scheme assignment per product, keyed by product name. */
export type SchemeAssignments = Record<string, Omit<ProposalScheme, 'id' | 'product_id'>>;

interface SchemeSelectorProps {
  /** Selected products; allowed_schemes comes already resolved by the backend
   *  (Excel column 9 or all MVP schemes, minus Licenciamiento for QloudSI). */
  products: PortfolioProduct[];
  onSelectionChanged: (
    assignments: SchemeAssignments,
    combineSchemes: boolean,
    isComplete: boolean,
  ) => void;
  initialAssignments?: SchemeAssignments;
  initialCombine?: boolean;
}

const MVP_SCHEME_TYPES: SchemeType[] = ['licensing', 'services', 'support_maintenance'];

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

function isQloudsiProduct(productType?: string): boolean {
  return (productType || '').toLowerCase().includes('qloudsi');
}

/** Schemes selectable for a product. The backend already resolves the list;
 *  the QloudSI filter here is only a defensive fallback when allowed_schemes
 *  is missing (the API rejects the combination anyway). */
function allowedSchemesFor(product: PortfolioProduct): SchemeType[] {
  const base =
    product.allowed_schemes && product.allowed_schemes.length > 0
      ? MVP_SCHEME_TYPES.filter((t) => product.allowed_schemes!.includes(t))
      : MVP_SCHEME_TYPES;
  if (isQloudsiProduct(product.product_type)) {
    return base.filter((t) => t !== 'licensing');
  }
  return base;
}

const SchemeSelector: React.FC<SchemeSelectorProps> = ({
  products,
  onSelectionChanged,
  initialAssignments = {},
  initialCombine = true,
}) => {
  const [assignments, setAssignments] = useState<SchemeAssignments>(initialAssignments);
  const [combineSchemes, setCombineSchemes] = useState(initialCombine);

  useEffect(() => {
    // Drop assignments of products no longer selected
    const names = new Set(products.map((p) => p.name));
    const pruned: SchemeAssignments = {};
    for (const [name, scheme] of Object.entries(assignments)) {
      if (names.has(name)) pruned[name] = scheme;
    }
    const isComplete = products.length > 0 && products.every((p) => pruned[p.name]);
    onSelectionChanged(pruned, products.length < 2 ? true : combineSchemes, isComplete);
  }, [assignments, combineSchemes, products]);

  const assignScheme = (productName: string, type: SchemeType) => {
    setAssignments((prev) => ({
      ...prev,
      [productName]: {
        scheme_type: type,
        payment_frequency: prev[productName]?.payment_frequency || 'Único',
      },
    }));
  };

  const updateFrequency = (productName: string, frequency: string) => {
    setAssignments((prev) => {
      const current = prev[productName];
      if (!current) return prev;
      return { ...prev, [productName]: { ...current, payment_frequency: frequency } };
    });
  };

  const assignedCount = products.filter((p) => assignments[p.name]).length;

  return (
    <div className="space-y-6 bg-white p-6 rounded-lg border border-gray-200">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Esquema por producto</h3>
        <span className="text-xs text-gray-500">
          {assignedCount}/{products.length} productos con esquema
        </span>
      </div>

      {products.length === 0 ? (
        <div className="rounded-md bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
          No hay productos seleccionados. Vuelve al paso anterior y selecciona al menos uno.
        </div>
      ) : (
        <div className="grid gap-4">
          {products.map((product) => {
            const allowed = allowedSchemesFor(product);
            const selected = assignments[product.name];
            const qloudsi = isQloudsiProduct(product.product_type);

            return (
              <div
                key={product.name}
                className="p-4 border rounded-md space-y-3"
                data-testid={`product-card-${product.name}`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-bold text-gray-900">{product.name}</span>
                  <span className="text-xs font-semibold bg-gray-100 text-gray-600 px-2.5 py-1 rounded-full uppercase tracking-wider">
                    {product.product_type}
                  </span>
                </div>

                {qloudsi && (
                  <p className="text-xs text-amber-700 bg-amber-50 border border-amber-200 rounded px-3 py-1.5">
                    Licenciamiento no disponible para servicios QloudSI
                  </p>
                )}

                <div className="grid gap-2">
                  {allowed.map((type) => (
                    <label
                      key={type}
                      className="flex items-start p-2 rounded hover:bg-gray-50 cursor-pointer transition-colors"
                    >
                      <input
                        type="radio"
                        name={`scheme-${product.name}`}
                        value={type}
                        checked={selected?.scheme_type === type}
                        onChange={() => assignScheme(product.name, type)}
                        className="mt-0.5 h-4 w-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                      />
                      <span className="ml-3 text-sm">
                        <span className="font-medium text-gray-700">{SCHEME_LABELS[type]}</span>
                        <span className="block text-gray-500">{SCHEME_DESCRIPTIONS[type]}</span>
                      </span>
                    </label>
                  ))}
                </div>

                {selected && (
                  <div className="pt-2 flex items-center space-x-4">
                    <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">
                      Frecuencia de Pago:
                    </span>
                    <div className="flex space-x-2">
                      {PAYMENT_FREQUENCIES.map((freq) => (
                        <button
                          key={freq.value}
                          type="button"
                          onClick={() => updateFrequency(product.name, freq.value)}
                          className={`px-3 py-1 text-xs rounded-full border transition-colors ${
                            selected.payment_frequency === freq.value
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
            );
          })}
        </div>
      )}

      {products.length >= 2 && (
        <div className="mt-6 p-4 bg-blue-50 rounded-md border border-blue-100 flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-sm font-medium text-blue-900">Configuración de Documentos</span>
            <span className="text-xs text-blue-700">
              Hay {products.length} productos seleccionados. ¿Cómo deseas generar los documentos?
            </span>
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
              Documento unificado
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
