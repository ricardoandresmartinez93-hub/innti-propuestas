---
name: document-generation
description: Explica cómo generar documentos Word y PDF para propuestas en Quipux. Usar cuando se trabaje con DocumentGenerator, endpoints de /documents, o se necesite entender la estructura del documento final.
---

# Document Generation Skill

## Clase principal: `DocumentGenerator`

Archivo: `app/services/document_generator.py`

Genera documentos Word (`.docx`) con la estructura estándar de propuestas Quipux.
La conversión a PDF se hace a través del router `app/routers/documents.py` usando WeasyPrint.

## Secciones del Documento

El documento final contiene estas secciones en orden:

| Sección | Campo en `Proposal` | Generado por |
|---------|---------------------|--------------|
| Carta de presentación | `letter_content` | `InntiService.generate_cover_letter()` |
| Contexto / Introducción | `context_content` | `InntiService.generate_context_section()` |
| Alcance | `scope_content` | `InntiService.generate_scope_section()` |
| Condiciones económicas | `economic_conditions` | Edición **manual** en el editor TipTap |
| Forma de pago | `payment_terms` | Edición manual |
| Servicios excluidos | `excluded_services` | Auto-completado según esquema |
| Propiedad intelectual | `ip_section` | Texto fijo según esquema |
| Confidencialidad y ética | `confidentiality` | Texto fijo (constante de empresa) |
| **Anexo técnico** | — | `DocumentGenerator` + `InntiService.enrich_product_description()` |

## Textos Fijos (Constantes)

`DocumentGenerator` contiene textos que **no deben modificarse sin aprobación jurídica**:
- `CONFIDENTIALITY_TEXT` — Cláusula de confidencialidad
- `ETHICS_TEXT` — Declaración de ética empresarial
- `EXCLUDED_SERVICES_LICENSING` — Lista para esquema de licenciamiento
- `EXCLUDED_SERVICES_SUPPORT` — Lista para esquema de soporte
- `IP_LICENSING` — Texto de propiedad intelectual para licenciamiento
- `IP_SERVICES` — Texto de propiedad intelectual para servicios

## Flujo de Generación

```
POST /proposals/{id}/generate
    └─► proposals router
        └─► InntiService (genera secciones de texto)
            └─► Actualiza campos en Proposal (DB)

GET /documents/{proposal_id}/word
    └─► documents router
        └─► DocumentGenerator.generate_proposal_docx(proposal, products)
            └─► Retorna archivo .docx como StreamingResponse

GET /documents/{proposal_id}/pdf
    └─► documents router
        └─► Genera .docx → convierte a PDF con WeasyPrint
            └─► Retorna archivo .pdf como StreamingResponse
```

## Modo `combine_schemes`

- `combine_schemes = True` (default): todos los esquemas se incluyen en **un solo documento**.
- `combine_schemes = False`: se genera un documento **separado** por esquema.

## Limitaciones y notas

- WeasyPrint requiere librerías del sistema (GTK en Windows). En tests, se mockea con `MagicMock`.
- Los documentos generados **no se almacenan en disco** — se generan en memoria (`BytesIO`) y se sirven directamente.
- Nunca subir documentos `.docx` o `.pdf` al repositorio — están en `.gitignore`.
