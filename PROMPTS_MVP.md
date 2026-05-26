# Prompts para completar el MVP — Innti Propuestas

> **Cómo usar este archivo:**  
> Cada sección es un prompt listo para pegar en **Claude Code** (FleetView / Claude CLI).  
> Ejecutar **en orden**, uno por uno. Verificar que cada paso funcione antes de continuar.  
> Los prompts de Prioridad 1 son bloqueantes — sin ellos el flujo no es demostrable.

---

## PRIORIDAD 1 — Crítico (el flujo no funciona sin esto)

---

### PROMPT 1 — Tipos TypeScript de aprobación + funciones en api.ts

**Archivo afectado:** `frontend/src/types/index.ts` y `frontend/src/services/api.ts`

**Cuándo ejecutar:** Primero. Los demás prompts dependen de estos tipos y funciones.

```
En el proyecto innti-propuestas, necesito completar el cliente API de aprobaciones.

1. En `frontend/src/types/index.ts`, agrega al final estos tipos:

- `ApprovalRole`: union type `'reviewer' | 'vp'`
- `ApprovalAction`: union type `'approved' | 'rejected'`
- `Approval`: interface con campos:
  - id: number
  - proposal_id: number
  - role: ApprovalRole
  - approver_name: string
  - approver_email?: string
  - action: ApprovalAction
  - comments?: string
  - created_at: string
- `ApproveRequest`: interface con campos:
  - approver_name: string
  - approver_email?: string
  - role: ApprovalRole
  - action: ApprovalAction (siempre 'approved')
  - comments?: string
- `RejectRequest`: interface con campos:
  - approver_name: string
  - approver_email?: string
  - role: ApprovalRole
  - action: ApprovalAction (siempre 'rejected')
  - comments: string (obligatorio en rechazo)
- `ROLE_LABELS`: Record<ApprovalRole, string> con valores: reviewer → 'Revisora (Ángela)', vp → 'VP (Juan Pablo)'

2. En `frontend/src/services/api.ts`, agrega estas funciones a `proposalApi`:

- `approve(id: number, data: ApproveRequest)` → POST `/proposals/${id}/approve`
- `reject(id: number, data: RejectRequest)` → POST `/proposals/${id}/reject`
- `getApprovals(id: number)` → GET `/proposals/${id}/approvals` retorna `Approval[]`
- `markSentToClient(id: number)` → POST `/proposals/${id}/submit-review` (mismo endpoint, detecta estado APPROVED automáticamente en backend — revisar si existe endpoint dedicado o si aplica el mismo)

Importar los tipos nuevos en api.ts. No usar `any`. Respetar el estilo existente del archivo.
```

**Verificación:** `npm run build` en `frontend/` no debe tener errores TypeScript.

---

### PROMPT 2 — UI completa de aprobación en ProposalDetailPage

**Archivo afectado:** `frontend/src/pages/ProposalDetailPage.tsx`

**Cuándo ejecutar:** Después del Prompt 1.

```
En el proyecto innti-propuestas, necesito completar el flujo de aprobación en `frontend/src/pages/ProposalDetailPage.tsx`.

El archivo actual solo tiene el botón "Enviar a Revisión" para estado 'draft'. Necesito agregar todo lo siguiente:

**1. Imports y estado nuevo:**
- Importar `Approval`, `ApproveRequest`, `RejectRequest`, `ROLE_LABELS` desde `../types`
- Estado: `approvals: Approval[]` (iniciar vacío, cargar con `proposalApi.getApprovals`)
- Estado: `showApprovalModal: boolean` (controla modal de aprobar/rechazar)
- Estado: `approvalForm: { approver_name: string; role: ApprovalRole; comments: string; action: 'approved' | 'rejected' }` 

**2. Cargar historial de aprobaciones:**
En el `useEffect` que carga la propuesta, también llamar `proposalApi.getApprovals(id)` y guardar en `approvals`.

**3. Función `handleApprovalAction(action: 'approved' | 'rejected')`:**
- Abre el modal con `action` pre-seteado
- Pre-rellena `role` según el estado actual:
  - `pending_review` → role = 'reviewer'
  - `pending_vp` → role = 'vp'

**4. Función `handleSubmitApproval()`:**
- Si `action === 'approved'`: llama `proposalApi.approve(...)` con los datos del form
- Si `action === 'rejected'`: llama `proposalApi.reject(...)` — requiere `comments` no vacío
- Tras éxito: recargar propuesta + aprobaciones, cerrar modal, mostrar mensaje

**5. Botones contextuales según estado (reemplazar el bloque del botón actual):**

- `status === 'draft'` → botón verde "Enviar a Revisión" (ya existe, mantener)
- `status === 'pending_review'` → dos botones: 
  - verde "✅ Aprobar (Ángela)" → `handleApprovalAction('approved')`
  - rojo "❌ Rechazar" → `handleApprovalAction('rejected')`
- `status === 'reviewed'` → botón azul "Enviar a VP →" → llama `proposalApi.submitForReview(id)` y recarga
- `status === 'pending_vp'` → dos botones:
  - verde "✅ Aprobar (Juan Pablo)" → `handleApprovalAction('approved')`
  - rojo "❌ Rechazar" → `handleApprovalAction('rejected')`
- `status === 'approved'` → botón naranja "📤 Marcar como Enviada al Cliente" → llama endpoint correspondiente y recarga
- `status === 'rejected'` → botón gris "↩ Volver a Borrador" → llama `proposalApi.submitForReview(id)` si ese endpoint maneja REJECTED→DRAFT, o mostrar instrucción

**6. Modal de aprobación/rechazo:**
Un modal superpuesto (overlay) con:
- Título: "Aprobar propuesta" o "Rechazar propuesta" según action
- Campo texto: "Nombre del aprobador" (obligatorio)
- Campo email: "Email del aprobador" (opcional)
- Campo textarea: "Comentarios" (obligatorio solo si action === 'rejected')
- Botones: "Cancelar" y "Confirmar"
- Usar Tailwind CSS para el estilo, sin librerías externas

**7. Sección "Historial de Aprobaciones":**
Debajo del editor, mostrar un card con la lista de `approvals`:
- Cada ítem: badge de role (`ROLE_LABELS`), nombre del aprobador, acción (✅/❌), fecha, comentarios si existen
- Si no hay aprobaciones: texto "Sin aprobaciones registradas"

Respetar las reglas de AGENTS.md: componentes funcionales, Tailwind CSS, sin `any`, mensajes en español.
```

**Verificación:** `npm run build` sin errores. Navegar a una propuesta y verificar que los botones aparecen según el estado.

---

### PROMPT 3 — Botón "Generar con Innti" en ProposalDetailPage

**Archivo afectado:** `frontend/src/pages/ProposalDetailPage.tsx`

**Cuándo ejecutar:** Después del Prompt 2.

```
En `frontend/src/pages/ProposalDetailPage.tsx`, necesito agregar un botón "✨ Generar con Innti" que popule el contenido del editor.

El problema actual: el botón "Generar Word" descarga un archivo pero no rellena las secciones del editor TipTap. Necesito una acción separada que genere el contenido con Innti y luego recargue la propuesta para que el editor muestre el contenido generado.

**Comportamiento esperado:**
1. Usuario hace click en "✨ Generar con Innti"
2. Se llama `POST /api/proposals/{id}/generate-document?use_innti=true` con `responseType: 'blob'` (ya existe en api.ts como `proposalApi.generateDocument(id, true)`)
3. El backend, al generar el documento, también guarda el contenido en los campos de la propuesta (`letter_content`, `context_content`, `scope_content`) via InntiService
4. Tras la llamada, hacer `proposalApi.get(id)` para recargar la propuesta completa
5. Pasar el contenido actualizado al `ProposalEditor` — el editor debe reflejar el nuevo contenido

**Cambios a implementar:**

1. Agregar estado `isGeneratingInnti: boolean`

2. Función `handleGenerateWithInnti()`:
   - Confirmar con el usuario: "¿Generar contenido con Innti? Esto sobreescribirá el contenido actual del editor."
   - Llamar `proposalApi.generateDocument(proposal.id, true)` (ignorar el blob retornado)
   - Recargar `proposalApi.get(proposal.id)` y actualizar `proposal` en el estado
   - Mostrar mensaje de éxito
   - Manejar error con mensaje descriptivo

3. Agregar el botón en la sección "Acciones de Documento" (panel derecho), **antes** de los botones de descarga:
   - Botón con fondo morado/indigo: "✨ Generar con Innti"
   - Solo visible cuando `status === 'draft'`
   - Separador visual antes de los botones de descarga

4. El componente `ProposalEditor` recibe `initialContent` como prop. Para que refleje el contenido nuevo tras la regeneración, convertir `initialContent` en un prop reactivo: cuando `proposal` cambie en el padre, el editor debe actualizarse.
   - En `ProposalEditor.tsx`, cambiar el `useEffect` que actualiza el contenido del editor para que responda a cambios en `initialContent` (usar una key prop o un efecto que detecte cambios externos)

Respetar reglas de AGENTS.md. No introducir `any`.
```

**Verificación:** Crear propuesta en estado DRAFT, hacer click "✨ Generar con Innti", verificar que las secciones del editor se pueblan.

---

## PRIORIDAD 2 — Importante (experiencia completa)

---

### PROMPT 4 — Secciones faltantes en ProposalEditor

**Archivo afectado:** `frontend/src/components/ProposalEditor.tsx`

**Cuándo ejecutar:** Después del Prompt 3.

```
En `frontend/src/components/ProposalEditor.tsx`, el editor TipTap solo muestra 4 secciones. Necesito agregar las que faltan según el modelo de datos de la propuesta.

**Secciones actuales (mantener):**
- context_content → "Contexto"
- scope_content → "Alcance"
- economic_conditions → "Condiciones Económicas"
- payment_terms → "Forma de Pago"

**Secciones a agregar:**
1. `excluded_services` → "Servicios Excluidos" — editable con TipTap (igual que las existentes)
2. `ip_section` → "Propiedad Intelectual" — editable con TipTap
3. `letter_content` → "Carta de Presentación" — **SOLO LECTURA** (auto-generada por Innti, no editar)

**Implementación:**

1. Agregar las 3 secciones al array `SECTIONS`:
   ```typescript
   { id: 'excluded_services', label: 'Servicios Excluidos', readOnly: false },
   { id: 'ip_section', label: 'Propiedad Intelectual', readOnly: false },
   { id: 'letter_content', label: 'Carta de Presentación', readOnly: true },
   ```
   Actualizar el tipo del array para incluir el campo `readOnly: boolean`.

2. Cuando `activeTab` es una sección con `readOnly: true`:
   - El editor TipTap debe estar en modo `editable: false`
   - Mostrar un banner amarillo encima del editor: "⚠️ Esta sección es generada automáticamente por Innti. No se puede editar manualmente."
   - El botón "Guardar" debe estar deshabilitado

3. El `useEffect` que actualiza el editor al cambiar de tab debe también cambiar `editor.setEditable(false/true)` según `readOnly` del tab activo.

4. La prop `initialContent` ya incluye estos campos (vienen del tipo `Proposal` en `types/index.ts`): `excluded_services`, `ip_section`, `letter_content`. Asegurarse de que el componente los reciba correctamente desde `ProposalDetailPage.tsx`.

5. En `ProposalDetailPage.tsx`, actualizar el objeto `initialContent` que se pasa a `ProposalEditor` para incluir los 3 campos nuevos:
   ```typescript
   excluded_services: proposal.excluded_services || '',
   ip_section: proposal.ip_section || '',
   letter_content: proposal.letter_content || '',
   ```

Respetar AGENTS.md: sin `any`, Tailwind CSS, componentes funcionales.
```

**Verificación:** Abrir el editor de una propuesta y verificar que aparecen las 7 pestañas, que "Carta de Presentación" es solo lectura con el banner de advertencia.

---

### PROMPT 5 — Crear CLAUDE.md en la raíz del proyecto

**Archivo afectado:** `CLAUDE.md` (crear nuevo)

**Cuándo ejecutar:** Independiente, puede ejecutarse en cualquier momento.

```
En la raíz del proyecto `innti-propuestas`, crea un archivo `CLAUDE.md` para que Claude Code CLI cargue automáticamente el contexto del proyecto.

El archivo debe:

1. Incluir una sección "Stack Tecnológico" resumida (igual que AGENTS.md)
2. Incluir la instrucción: `@AGENTS.md` para que Claude Code cargue el archivo completo de reglas (si soporta referencias)
3. Como fallback (en caso de que no soporte @-referencias), copiar directamente el contenido de `AGENTS.md` en `CLAUDE.md`
4. Agregar una sección al inicio que explique: "Este proyecto usa OpenCode (`.opencode/`) y Claude Code (`.claude/`). Las reglas maestras están en `AGENTS.md`. Los agents y skills están en `.opencode/agents/` y `.opencode/skills/`."
5. Agregar una sección "Comandos rápidos" con:
   - Iniciar backend: `cd backend && .venv\Scripts\Activate.ps1 && uvicorn app.main:app --reload --port 8000`
   - Iniciar frontend: `cd frontend && npm run dev`
   - Ejecutar tests backend: `cd backend && pytest tests/ -v`
   - Ejecutar tests frontend: `cd frontend && npm test`

El archivo debe ser conciso pero completo. No duplicar información que ya está en AGENTS.md si puedes referenciarla.
```

**Verificación:** Abrir Claude Code CLI en el proyecto y verificar que carga el contexto del proyecto automáticamente.

---

## PRIORIDAD 3 — Nice to have

---

### PROMPT 6 — Verificar endpoint SENT_TO_CLIENT en backend

**Archivos afectados:** `backend/app/routers/proposals.py` y `backend/app/services/approval_service.py`

**Cuándo ejecutar:** Después de los prompts de Prioridad 1.

```
En el proyecto innti-propuestas, necesito verificar si existe un endpoint para marcar una propuesta como SENT_TO_CLIENT y, si no existe, crearlo.

1. Revisar `backend/app/routers/proposals.py` — buscar si hay algún endpoint o lógica para la transición APPROVED → SENT_TO_CLIENT.

2. Revisar `backend/app/services/approval_service.py` — verificar si `submit_for_review()` maneja el estado APPROVED.

3. Si no existe:
   - En `approval_service.py`, agregar método `mark_sent_to_client(proposal_id, db)`:
     - Valida que el estado sea APPROVED (lanza HTTPException 409 si no)
     - Cambia status a SENT_TO_CLIENT
     - Retorna la propuesta actualizada
   - En `proposals.py` (router), agregar:
     ```python
     POST /api/proposals/{id}/send-to-client
     ```
     Llama a `approval_service.mark_sent_to_client()`

4. Si ya existe en `submit-review` (detecta APPROVED automáticamente):
   - Documentar el comportamiento en un comentario en el router
   - En frontend, el botón "Enviado al Cliente" puede usar `proposalApi.submitForReview(id)` directamente

5. Agregar un test en `backend/tests/test_approvals.py` que valide la transición APPROVED → SENT_TO_CLIENT.

Respetar AGENTS.md: lógica en services, routers delgados, snake_case, get_db como dependencia.
```

**Verificación:** `pytest tests/test_approvals.py -v` — todos los tests pasan.

---

### PROMPT 7 — Tests de frontend para el flujo de aprobación

**Archivos afectados:** `frontend/src/__tests__/`

**Cuándo ejecutar:** Al final, cuando todo lo anterior funciona.

```
En el proyecto innti-propuestas, necesito agregar tests de frontend para el flujo de aprobación.

Crear `frontend/src/__tests__/ProposalDetailPage.test.tsx` con los siguientes casos de prueba usando Vitest + React Testing Library:

1. **Renderiza botón "Enviar a Revisión" en estado DRAFT:**
   - Mock de `proposalApi.get` retorna propuesta con `status: 'draft'`
   - Mock de `proposalApi.getApprovals` retorna array vacío
   - Verificar que el botón "Enviar a Revisión" existe en el DOM

2. **Renderiza botones de aprobación en estado PENDING_REVIEW:**
   - Mock con `status: 'pending_review'`
   - Verificar que existe botón "Aprobar (Ángela)" y botón "Rechazar"

3. **Renderiza botón "Enviar a VP" en estado REVIEWED:**
   - Mock con `status: 'reviewed'`
   - Verificar que existe botón "Enviar a VP"

4. **Renderiza botones de aprobación en estado PENDING_VP:**
   - Mock con `status: 'pending_vp'`
   - Verificar que existe botón "Aprobar (Juan Pablo)" y botón "Rechazar"

5. **Modal de rechazo se abre al hacer click en "Rechazar":**
   - Estado `pending_review`
   - Click en botón "Rechazar"
   - Verificar que el modal aparece con campo de comentarios

6. **Historial de aprobaciones muestra datos:**
   - Mock de `getApprovals` retorna un array con una aprobación
   - Verificar que el nombre del aprobador aparece en el DOM

Usar los patrones de mocking existentes en el proyecto (ver `frontend/src/__tests__/` para convenciones).
Todas las interfaces deben estar tipadas, sin `any`.
```

**Verificación:** `npm test` — todos los tests pasan sin errores.

---

## Resumen de ejecución

| # | Prompt | Archivos | Prioridad | Tiempo estimado |
|---|--------|----------|-----------|-----------------|
| 1 | Tipos + api.ts aprobación | `types/index.ts`, `api.ts` | 🔴 Crítico | 5 min |
| 2 | UI aprobación completa | `ProposalDetailPage.tsx` | 🔴 Crítico | 15 min |
| 3 | Botón Generar con Innti | `ProposalDetailPage.tsx`, `ProposalEditor.tsx` | 🔴 Crítico | 10 min |
| 4 | Secciones faltantes editor | `ProposalEditor.tsx`, `ProposalDetailPage.tsx` | 🟡 Importante | 10 min |
| 5 | CLAUDE.md | `CLAUDE.md` (nuevo) | 🟡 Importante | 5 min |
| 6 | Endpoint SENT_TO_CLIENT | `proposals.py`, `approval_service.py` | 🟢 Nice to have | 15 min |
| 7 | Tests frontend | `ProposalDetailPage.test.tsx` | 🟢 Nice to have | 20 min |

**Flujo completo verificable tras ejecutar prompts 1-3:**
```
Nueva propuesta → ✨ Generar con Innti → Editar → Enviar a Revisión
→ Aprobar (Ángela) → Enviar a VP → Aprobar (Juan Pablo) → Descargar Word/PDF
```
