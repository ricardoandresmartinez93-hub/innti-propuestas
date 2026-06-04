---
name: proposal-workflow-guide
description: Guía paso a paso del flujo de creación, edición y aprobación de propuestas en la UI. Usar cuando se trabaje en componentes del frontend o se necesite entender el flujo de usuario.
---

# Proposal Workflow Guide

Flujo de usuario completo para crear y gestionar propuestas en Innti Propuestas.

## 1️⃣ Crear Nueva Propuesta

**Ubicación UI:** HomePage → "Nueva Propuesta"  
**Flujo en 4 pasos** (`NewProposalPage`):

1. **Paso 1 — Productos:** Seleccionar productos del portafolio (ListaPortafolio.xlsx)
2. **Paso 2 — Esquemas:** Seleccionar esquema(s) comerciales (puede ser combinado):
   - Solo se muestran los esquemas **permitidos para los productos seleccionados** en el paso 1.
   - El selector muestra un badge "Filtrado por productos seleccionados" cuando hay restricciones.
   - Si ningún producto tiene restricción, aparecen los 3 MVP schemes: Licenciamiento, Prestación de Servicios, Soporte y Mantenimiento.
   - ⚠️ NO disponibles nunca: Concesión/BPO, Suministro (Fase 2)
3. **Paso 3 — Cliente:** Seleccionar cliente existente o crear uno nuevo
4. **Paso 4 — Resumen:** Ingresar **código** y **título** de la propuesta

**Campo Código (obligatorio en Paso 4):**
- Formato: `XXXX-MMYY` donde `XXXX` es el consecutivo del archivo de seguimiento de oportunidades del repositorio y `MMYY` es el mes+año de elaboración (ej: `3018-0526` = consecutivo 3018, mayo 2026)
- El sistema muestra el sufijo de fecha actual como referencia
- El usuario ingresa el consecutivo consultando el archivo de seguimiento

5. Click: **Crear Propuesta** → Propuesta en estado `DRAFT`

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

El editor tiene **8 pestañas**, divididas en dos grupos:

**Pestañas globales (1 sola versión para toda la propuesta):**
| Pestaña | Campo | Editable | Generada por |
|---------|-------|----------|--------------|
| Contexto | `Proposal.context_content` | ✅ Sí | Innti (editable post-gen) |
| Carta de Presentación | `Proposal.letter_content` | ❌ Solo lectura | Innti (banner amarillo ⚠️) |

**Pestañas por esquema (1 versión por cada esquema seleccionado):**
| Pestaña | Campo | Editable | Generada por |
|---------|-------|----------|--------------|
| Alcance | `ProposalScheme.scope_content` | ✅ Sí | Innti por esquema (editable post-gen) |
| Plazo | `ProposalScheme.validity_period` | ✅ Sí | Texto por defecto por esquema (editable) |
| Condiciones Económicas | `ProposalScheme.economic_conditions` | ✅ Sí | Manual (obligatorio por esquema) |
| Forma de Pago | `ProposalScheme.payment_terms` | ✅ Sí | Manual (obligatorio por esquema) |
| Servicios Excluidos | `ProposalScheme.excluded_services` | ✅ Sí | Default por esquema (vacío para SaaS) |
| Propiedad Intelectual | `ProposalScheme.ip_section` | ✅ Sí | Default por esquema (varía por tipo) |

> Cuando hay ≥ 2 esquemas, sobre el editor aparece un selector "Esquema: [Licenciamiento] [Servicios] [Soporte]" que permite cambiar entre las versiones por esquema. Las pestañas globales no muestran este selector.

> El botón **Guardar** persiste cambios globales vía `PATCH /api/proposals/{id}` y cambios por esquema vía `PATCH /api/proposals/{id}/schemes/{scheme_id}`. Funciona desde cualquier pestaña/sub-tab.

### Barra de herramientas del editor (TipTap)

Sobre el área editable hay una toolbar agrupada (cada grupo separado por una línea vertical sutil). Todos los botones se deshabilitan cuando la pestaña activa es de solo lectura (`readOnly: true`, p.ej. Carta de Presentación).

| Grupo | Botones |
|-------|---------|
| Texto | `B` (negrita), `I` (cursiva), `U` (subrayado), `S` (tachado), `x²` (superíndice), `x₂` (subíndice) |
| Encabezados | `H1`, `H2`, `H3`, `¶` (volver a párrafo normal) |
| Alineación | `Izq`, `Cen`, `Der`, `Just` |
| Listas y bloques | `• List`, `1. List`, `❝` (cita), `</>` (código en línea), `Code` (bloque de código), `—` (línea horizontal) |
| Enlace y color | `Link` (prompt para URL), `Color` (input nativo de color de texto), `Marca` (input nativo de color de resaltado) |
| Tabla | `Tabla` (inserta tabla 3×3 con encabezado) |
| Historia y limpieza | `↶` (deshacer), `↷` (rehacer), `Limpiar` (elimina todas las marcas y vuelve a párrafo) |

Las marcas inline (bold, italic, underline, strike, sup/sub, color, highlight, link), los bloques (heading, blockquote, listas, alineación, hr) y los hyperlinks se **preservan en el Word/PDF generado** gracias al parser `_HtmlToDocxParser` en `document_generator.py`.

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
