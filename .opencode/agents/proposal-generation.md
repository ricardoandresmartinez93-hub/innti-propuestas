---
name: proposal-generation
description: Automatizar la generación completa de una propuesta desde datos básicos hasta documento Word/PDF
trigger: manual
---

# Agent: Generación Automática de Propuesta

Orquesta la generación de una propuesta desde cero: crea el registro, genera contenido con Innti, enriquece productos, y exporta el documento final.

## Requisitos de Entrada

```json
{
  "client": {
    "name": "Andrés Barreneche Cano",
    "position": "Gerencia Financiera",
    "entity": "Consorcio ITS Medellín",
    "city": "Medellín",
    "email": "andres@example.com"
  },
  "proposal": {
    "title": "Licenciamiento y Modernización",
    "products": [
      "Qx-Tránsito",
      "Servicios digitales para el ciudadano"
    ],
    "schemes": ["licensing"],
    "combine_schemes": true
  }
}
```

## Pasos Ejecutados

1. **Crear cliente** (si no existe)
   - `POST /clients`

2. **Crear propuesta**
   - `POST /proposals`
   - Asignar cliente, esquemas, productos

3. **Generar contenido con Innti**
   - `POST /proposals/{id}/generate`
   - Genera automáticamente:
     - Carta de presentación (firma Juan Pablo)
     - Contexto/introducción
     - Alcance

4. **Enriquecer descripciones de productos**
   - Para cada producto: `InntiService.enrich_product_description()`
   - Mejora la descripción del anexo técnico

5. **Completar secciones manuales**
   - Condiciones económicas (usa plantillas según esquema)
   - Forma de pago (referencia a tarifa estándar)
   - Servicios excluidos (auto-completado según esquema)
   - Propiedad intelectual (texto fijo según esquema)

6. **Exportar documento**
   - `GET /documents/{id}/word` → archivo `.docx`
   - `GET /documents/{id}/pdf` → archivo `.pdf`

## Salida

- Propuesta generada en estado `DRAFT`
- Archivo Word descargado: `{proposal_code}-{client_entity}.docx`
- Listo para edición manual si es necesario
- Listo para enviarse a revisión (Ángela)

## Integración con Skills

- **innti-domain** → Proporciona contexto de esquemas y aprobaciones
- **document-generation** → Controla la generación del documento Word/PDF
- **testing-workflow** → Tests para verificar que la generación no rompió nada

## Referencia

- Routers: `/proposals`, `/documents`, `/clients`
- Servicios: `InntiService`, `DocumentGenerator`, `ApprovalService`
- Modelos: `Proposal`, `ProposalScheme`, `ProposalProduct`, `Client`
