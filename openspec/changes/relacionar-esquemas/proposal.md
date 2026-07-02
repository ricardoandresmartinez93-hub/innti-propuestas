# Proposal: Relacionar esquemas por producto

**Change:** relacionar-esquemas
**Date:** 2026-07-02
**Status:** approved

## Intent

Hoy los esquemas comerciales se seleccionan a nivel de propuesta (checkboxes
globales) y la compatibilidad producto→esquema se calcula por intersección entre
todos los productos seleccionados. Las reglas de negocio reales son otras:

1. Cada producto/servicio de una propuesta tiene asignado exactamente UN esquema.
2. El usuario puede seleccionar varios productos; cada uno mantiene su esquema propio
   (dos productos pueden compartir el mismo tipo de esquema).
3. Los servicios QloudSI NUNCA pueden tener el esquema Licenciamiento (`licensing`) —
   regla dura de negocio que debe vivir en el backend, no solo en el Excel.
4. Documento unificado (`combine_schemes=True`): 1 documento con un bloque por producto.
5. Documentos separados (`combine_schemes=False`): un documento POR PRODUCTO (hoy se
   genera uno por esquema). Requiere ≥2 productos.

## Scope

- Modelo: vínculo `ProposalScheme.product_id` (1 esquema por producto).
- Regla QloudSI codificada en backend + reflejada en `allowed_schemes` del portafolio.
- Resolución de esquemas permitidos POR PRODUCTO; la intersección se elimina.
- Contrato de creación: cada producto viaja con su esquema embebido; se elimina la
  lista `schemes` top-level del payload.
- Generación de documentos por producto (unificado con bloques por producto;
  separado con un archivo por producto).
- Migración ligera SQLite con backfill best-effort; propuestas legadas conservan
  el comportamiento actual.
- UI: selector de esquema por producto (radio), sin aviso de intersección.

## Out of scope

- Esquemas Fase 2 (`concession_bpo`, `supply`).
- Cambios en el flujo de aprobación.
- Edición del esquema asignado a un producto después de creada la propuesta
  (se mantiene el PATCH de contenido por esquema existente).

## Approach

Backend: agregar `product_id` (FK nullable) a `ProposalScheme` con relación 1:1
desde `ProposalProduct`; la restricción "exactamente uno" se valida en la API.
Helper `is_qloudsi_product` + `QLOUDSI_FORBIDDEN_SCHEMES` como única fuente de
verdad de la regla QloudSI, aplicada al construir `allowed_schemes` por producto
y al validar la creación. Documentos: iterar productos en vez de esquemas cuando
la propuesta usa esquemas por producto (`uses_product_schemes`); las legadas
(esquemas sin `product_id`) conservan el flujo actual.

Frontend: `SchemeSelector` pasa de checkboxes globales a una tarjeta por producto
con radio buttons de sus esquemas permitidos (ya filtrados por el backend);
el payload de creación embebe el esquema en cada producto.
