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

Estas secciones **deben ser editadas manualmente**:

| Sección | Descripción | Frecuencia |
|---------|------------|-----------|
| **Condiciones económicas** | Valores totales, metodología de pago, descuentos | Siempre |
| **Forma de pago** | Cronograma, cuenta de pago, vigencia | Siempre |
| **Servicios excluidos** | Qué NO se incluye en la propuesta | Auto-completado (editable) |
| **Propiedad intelectual** | Derechos de autor y licencias | Auto-completado (editable) |
| **Confidencialidad y ética** | Cláusulas legales | Auto-completado (no editar sin jurídica) |

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

**Ubicación UI:** ProposalEditor → "Descargar"

Disponible cuando la propuesta está en estado `APPROVED`:

- **Word (.docx)** → Descargar documento editable
- **PDF** → Descargar documento final para enviar al cliente

**Referencia:** Skill `document-generation` para detalles técnicos

## 7️⃣ Enviar al Cliente

**Ubicación UI:** ProposalEditor → "Enviar al cliente"

1. Asegurar que `status == APPROVED`
2. Ingresar **email del cliente** (o usar el registrado)
3. Click: **Enviar**
4. Estado: `SENT_TO_CLIENT` (final)
5. Email con PDF se envía automáticamente

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

**Referencia:** AGENTS.md para detalles técnicos de los enums
