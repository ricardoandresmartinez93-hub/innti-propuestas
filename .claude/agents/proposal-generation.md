---
name: proposal-generation
description: Usar cuando se necesite crear una propuesta comercial nueva desde cero, generar contenido automático con Innti, o entender cómo funciona la generación de documentos Word/PDF. Activar ante peticiones como "crea una propuesta para...", "genera una propuesta con los productos...", o al implementar/depurar la integración con InntiService.
tools: [Read, Write, Edit, Bash, Glob, Grep, WebFetch]
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

> **Prefijo base:** `http://localhost:8000/api`

1. **Crear cliente** (si no existe)
   - `POST /api/clients`

2. **Crear propuesta**
   - `POST /api/proposals/`
   - Asignar `client_id`, esquemas MVP (`licensing`, `services`, `support_maintenance`), productos

3. **Generar contenido con Innti**
   - `POST /api/proposals/{id}/generate-document?use_innti=true`
   - Si los campos de texto están vacíos, Innti genera y persiste automáticamente:
     - Carta de presentación (firma Juan Pablo Ramírez Madrid)
     - Contexto/introducción
     - Alcance
   - Retorna el `.docx` generado como `FileResponse`

4. **Editar secciones manuales**
   - `PATCH /api/proposals/{id}` — condiciones económicas, forma de pago
   - Servicios excluidos y propiedad intelectual: auto-completados según esquema (editables)

5. **Flujo de aprobación** (si aplica)
   - `POST /api/proposals/{id}/submit-review` → PENDING_REVIEW (Ángela)
   - `POST /api/proposals/{id}/approve` body: `{ role: "reviewer", action: "approved", approver_name, comments? }` → REVIEWED
   - `POST /api/proposals/{id}/submit-review` → PENDING_VP (Juan Pablo)
   - `POST /api/proposals/{id}/approve` body: `{ role: "vp", action: "approved", approver_name, comments? }` → APPROVED
   - `POST /api/proposals/{id}/submit-review` → SENT_TO_CLIENT (estado final)

6. **Exportar documento final**
   - `POST /api/proposals/{id}/generate-document` → Word (.docx)
   - `POST /api/proposals/{id}/generate-pdf` → PDF
   - `POST /api/proposals/{id}/generate-annex` → Anexo Técnico (.docx)

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

- Routers: `app/routers/proposals.py`, `app/routers/documents.py`, `app/routers/clients.py`, `app/routers/approvals.py`
- Servicios: `InntiService`, `DocumentGenerator`, `PortfolioService`, `ApprovalService`
- Modelos: `Proposal`, `ProposalScheme`, `ProposalProduct`, `Client`
- Skills: `innti-domain`, `document-generation`, `proposal-workflow`
