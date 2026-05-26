---
name: proposal-workflow
description: Orquestar el flujo completo de una propuesta (crear → generar → editar → aprobar → exportar)
trigger: manual
---

# Agent: Flujo de Propuesta Completo

Automatiza el ciclo de vida de una propuesta desde su creación hasta su exportación final.

## Flujo

1. **Crear propuesta** (estado: DRAFT)
   - Endpoint: `POST /proposals`
   - Datos: cliente, título, esquemas seleccionados, productos

2. **Generar contenido con Innti**
   - Endpoint: `POST /proposals/{id}/generate`
   - Genera: carta, contexto, alcance (usando `innti-domain` skill)

3. **Editar secciones manuales**
   - Editar: condiciones económicas, forma de pago (en el editor TipTap del frontend)

4. **Enviar a revisión**
   - Endpoint: `POST /proposals/{id}/submit-review`
   - Nuevo estado: PENDING_REVIEW (espera a Ángela)

5. **Aprobación Ángela**
   - Endpoint: `POST /proposals/{id}/approve` (role: REVIEWER)
   - Nuevo estado: REVIEWED → PENDING_VP

6. **Aprobación Juan Pablo**
   - Endpoint: `POST /proposals/{id}/approve` (role: VP)
   - Nuevo estado: APPROVED

7. **Exportar documento**
   - Endpoint: `GET /documents/{id}/word` o `/documents/{id}/pdf`
   - Retorna: archivo Word o PDF generado (usa `document-generation` skill)

## Uso

```bash
# Ver estado de una propuesta
curl http://localhost:8000/proposals/{proposal_id}

# Avanzar automáticamente a través del flujo
# (implementar en la CLI o UI con llamadas secuenciales a los endpoints)
```

**Referencia:** `innti-domain`, `document-generation`, `AGENTS.md` (flujo de estados).
