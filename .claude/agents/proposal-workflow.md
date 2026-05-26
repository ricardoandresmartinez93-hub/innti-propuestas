---
name: proposal-workflow
description: Usar cuando se necesite entender o ejecutar el ciclo de vida completo de una propuesta comercial (crear → generar con Innti → editar → aprobar → exportar). Activar ante preguntas sobre flujo de estados, transiciones de aprobación, endpoints del flujo o al implementar cualquier parte del ciclo de vida de propuestas.
tools: [Read, Write, Edit, Bash, Glob, Grep, WebFetch]
---

# Agent: Flujo Completo de Propuesta

Ciclo de vida de una propuesta desde creación hasta entrega al cliente.
**Prefijo base de todos los endpoints:** `http://localhost:8000/api`

---

## Paso 1 — Crear Cliente (si no existe)

```http
POST /api/clients
{
  "name": "Andrés Barreneche Cano",
  "position": "Gerencia Financiera",
  "entity": "Consorcio ITS Medellín",
  "city": "Medellín",
  "email": "andres@example.com"
}
```
→ Retorna `{ "id": 1, ... }`

---

## Paso 2 — Crear Propuesta (estado: `DRAFT`)

```http
POST /api/proposals/
{
  "title": "Licenciamiento y Modernización de Soluciones",
  "client_id": 1,
  "combine_schemes": true,
  "schemes": [{ "scheme_type": "licensing", "payment_frequency": "unico" }],
  "products": [
    { "product_name": "Qx-Tránsito", "product_type": "Plataforma", "description": "...", "category": "modernización" }
  ]
}
```
→ Retorna propuesta con `status: "draft"`

---

## Paso 3 — Generar Documento (Innti genera el texto)

```http
POST /api/proposals/{id}/generate-document?use_innti=true
```
- Si los campos de texto están vacíos en BD, Innti los genera y persiste automáticamente.
- Retorna archivo `.docx` para descarga.
- **Alternativa:** `POST /api/proposals/{id}/generate-pdf` para PDF.

---

## Paso 4 — Editar Secciones Manuales

Usar `PATCH /api/proposals/{id}` para guardar las secciones que el usuario edita en TipTap:

```http
PATCH /api/proposals/{id}
{
  "economic_conditions": "<p>Valor total: $150.000.000 COP...</p>",
  "payment_terms": "<p>50% anticipo, 50% contra entrega...</p>"
}
```

---

## Paso 5 — Enviar a Revisión (DRAFT → PENDING_REVIEW)

```http
POST /api/proposals/{id}/submit-review
```
→ Estado cambia de `draft` a `pending_review`. Email enviado a Ángela.

---

## Paso 6 — Ángela Aprueba (PENDING_REVIEW → REVIEWED)

```http
POST /api/proposals/{id}/approve
{
  "approver_name": "Ángela García",
  "approver_email": "angela@quipux.com",
  "role": "reviewer",
  "action": "approved",
  "comments": "Revisado y aprobado"
}
```
→ Estado: `reviewed`. **Aún NO está en PENDING_VP.**

> ⚠️ Si Ángela **rechaza**: `POST /api/proposals/{id}/reject`
> ```json
> { "role": "reviewer", "approver_name": "Ángela García", "action": "rejected", "comments": "Motivo del rechazo (obligatorio)" }
> ```
> → Estado: `rejected` → puede volver a `draft` con otro `submit-review`.

---

## Paso 7 — Avanzar a VP (REVIEWED → PENDING_VP)

El mismo endpoint `submit-review` detecta que está en `reviewed` y avanza a `pending_vp`:

```http
POST /api/proposals/{id}/submit-review
```
→ Estado cambia de `reviewed` a `pending_vp`. Email enviado a Juan Pablo.

---

## Paso 8 — Juan Pablo Aprueba (PENDING_VP → APPROVED)

```http
POST /api/proposals/{id}/approve
{
  "approver_name": "Juan Pablo Ramírez Madrid",
  "approver_email": "juanpablo@quipux.com",
  "role": "vp",
  "action": "approved",
  "comments": "Aprobada para envío al cliente"
}
```
→ Estado: `approved`.

> ⚠️ Si Juan Pablo **rechaza**: `POST /api/proposals/{id}/reject`
> ```json
> { "role": "vp", "approver_name": "Juan Pablo Ramírez Madrid", "action": "rejected", "comments": "Motivo (obligatorio)" }
> ```
> → Estado: `rejected` → puede volver a `draft`.

---

## Paso 9 — Exportar Documento Final

```http
# Word editable
POST /api/proposals/{id}/generate-document

# PDF para el cliente
POST /api/proposals/{id}/generate-pdf

# Anexo técnico separado
POST /api/proposals/{id}/generate-annex
```

---

## Paso 10 — Marcar como Enviada al Cliente (APPROVED → SENT_TO_CLIENT)

```http
POST /api/proposals/{id}/submit-review
```
→ El endpoint detecta `approved` y ejecuta la transición a `sent_to_client` (estado final, no reversible).

---

## Resumen de Estados y Transiciones

```
DRAFT ──[submit-review]──► PENDING_REVIEW ──[approve REVIEWER]──► REVIEWED
  ▲                               │                                    │
  │                          [reject REVIEWER]              [submit-review]
  │                               │                                    ▼
  │                               ▼                              PENDING_VP ──[approve VP]──► APPROVED ──[submit-review]──► SENT_TO_CLIENT
  │                           REJECTED ◄──────────────────── [reject VP]        
  └───────────────────── [submit-review] ◄───────────────────────────┘
```

> `submit-review` es **multi-transición**: detecta el estado y ejecuta la transición correcta:
> - `DRAFT` → `PENDING_REVIEW`
> - `REVIEWED` → `PENDING_VP`
> - `APPROVED` → `SENT_TO_CLIENT`
> - `REJECTED` → `DRAFT`

---

## Referencias
- Skill: `innti-domain` — estados y roles
- Skill: `document-generation` — generación de documentos
- Skill: `proposal-workflow-guide` — flujo desde perspectiva de usuario/UI
- Reglas: `AGENTS.md` — enums y endpoints
