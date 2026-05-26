---
name: proposal-workflow-guide
description: Guía paso a paso del flujo de creación, edición y aprobación de propuestas en la UI. Usar cuando se trabaje en componentes del frontend o se necesite entender el flujo de usuario.
---

# Proposal Workflow Guide

Flujo de usuario completo para crear y gestionar propuestas en Innti Propuestas.

## 1️⃣ Crear Nueva Propuesta

**Ubicación UI:** HomePage → "Nueva Propuesta"

1. Seleccionar **cliente** de la lista (o crear uno nuevo)
2. Ingresar **título** de la propuesta
3. Seleccionar **esquema(s)** (puede ser combinado):
   - ☑️ Licenciamiento (pago único)
   - ☑️ Prestación de Servicios (mensual)
   - ☑️ Soporte y Mantenimiento (anual)
   - ⚠️ NO disponibles: Concesión/BPO, Suministro (Fase 2)
4. Seleccionar **productos** del portafolio (ListaPortafolio.xlsx)
5. Click: **Crear** → Propuesta en estado `DRAFT`

**Referencia:** Skill `innti-domain` para entender esquemas

## 2️⃣ Generar Contenido Automático

**Ubicación UI:** ProposalEditor → "Generar con Innti"

1. Asegurar que la propuesta tenga:
   - Título ✅
   - Cliente ✅
   - Esquemas ✅
   - Productos ✅

2. Click: **Generar** → Innti genera automáticamente:
   - 📝 Carta de presentación (firma Juan Pablo)
   - 📝 Sección de contexto/introducción
   - 📝 Sección de alcance
   - 🔗 Descripciones técnicas enriquecidas (anexo técnico)

**Nota:** Las descripciones técnicas se toman de `ListaPortafolio.xlsx` y se enriquecen usando `InntiService.enrich_product_description()`.

**Referencia:** Skill `innti-domain` para métodos de Innti

## 3️⃣ Editar Secciones Manuales

**Ubicación UI:** ProposalEditor → TipTap rich text editor

El editor tiene **7 pestañas**. Comportamiento por pestaña:

| Pestaña | Campo | Editable | Generada por |
|---------|-------|----------|--------------|
| Contexto | `context_content` | ✅ Sí | Innti (editable post-gen) |
| Alcance | `scope_content` | ✅ Sí | Innti (editable post-gen) |
| Condiciones Económicas | `economic_conditions` | ✅ Sí | Manual (obligatorio) |
| Forma de Pago | `payment_terms` | ✅ Sí | Manual (obligatorio) |
| Servicios Excluidos | `excluded_services` | ✅ Sí | Auto-completado según esquema |
| Propiedad Intelectual | `ip_section` | ✅ Sí | Auto-completado según esquema |
| Carta de Presentación | `letter_content` | ❌ Solo lectura | Innti (banner amarillo ⚠️) |

> El botón **Guardar** persiste todos los campos mediante `PATCH /api/proposals/{id}`.
> Funciona desde cualquier pestaña (incluso estando en Carta de Presentación).

**Referencia:** Skill `document-generation` para textos fijos

## 4️⃣ Enviar a Revisión

**Ubicación UI:** ProposalEditor → "Enviar a revisión"

1. Verificar que TODAS las secciones estén completas
2. Click: **Enviar a revisión**
3. Estado cambia a `PENDING_REVIEW` (espera a Ángela)
4. Email se envía a Ángela (revisora)

## 5️⃣ Flujo de Aprobación

### Estado: `PENDING_REVIEW` (Ángela revisa)

**Ángela puede:**
- ✅ **Aprobar** → Estado: `REVIEWED` ← la propuesta queda en revisado, **aún no pasa a VP**
- ❌ **Rechazar** → Estado: `REJECTED` → Vuelve a `DRAFT` para correcciones

### ⚠️ Paso intermedio: Enviar a VP (REVIEWED → PENDING_VP)

Después de que Ángela aprueba, el comercial (no Ángela) debe presionar **"Enviar a VP"**
para avanzar de `REVIEWED` a `PENDING_VP`. Este paso usa el mismo botón/endpoint de "Enviar".

> El sistema detecta automáticamente el estado actual: si es `REVIEWED`, avanza a `PENDING_VP`.

### Estado: `PENDING_VP` (Juan Pablo revisa)

**Juan Pablo (VP) puede:**
- ✅ **Aprobar** → Estado: `APPROVED` → Propuesta lista para exportar
- ❌ **Rechazar** → Estado: `REJECTED` → Vuelve a `DRAFT` para correcciones

## 6️⃣ Exportar Documento

**Ubicación UI:** Panel lateral derecho → "Acciones de Documento"

Disponible en **cualquier estado** (DRAFT, PENDING_REVIEW, APPROVED, etc.):

- **Word (.docx)** → Documento editable para revisión interna
- **PDF** → Documento final para el cliente
- **Anexo Técnico (.docx)** → Detalle técnico de productos (independiente)

**Referencia:** Skill `document-generation` para detalles técnicos

## 7️⃣ Enviar al Cliente

**Ubicación UI:** Botón de acción contextual cuando `status == APPROVED`

1. Asegurar que `status == APPROVED` (aprobada por Juan Pablo)
2. Click: **📤 Marcar como Enviada al Cliente**
3. Estado: `SENT_TO_CLIENT` (estado final — no reversible)

> No requiere ingresar email: marca el estado en BD vía `POST /api/proposals/{id}/submit-review`
> (el endpoint detecta `APPROVED` y ejecuta la transición a `SENT_TO_CLIENT`).

---

## Diagrama Completo (Estados)

```
Crear (DRAFT)
    ↓
Generar contenido (DRAFT + contenido)
    ↓
Editar manual (DRAFT + secciones editadas)
    ↓
"Enviar a revisión" → PENDING_REVIEW
    ↓
Ángela aprueba → REVIEWED     (Ángela rechaza → REJECTED → DRAFT)
    ↓
"Enviar a VP" → PENDING_VP    ← paso explícito, mismo botón/endpoint
    ↓
Juan Pablo aprueba → APPROVED  (Juan Pablo rechaza → REJECTED → DRAFT)
    ↓
Exportar Word/PDF → SENT_TO_CLIENT (estado final)
```

**Referencia:** AGENTS.md para detalles técnicos de los enums y endpoints.
