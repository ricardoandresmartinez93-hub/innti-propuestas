---
name: document-generation
description: Explica cómo generar documentos Word, PDF y Anexo Técnico para propuestas en Quipux. Usar cuando se trabaje con DocumentGenerator, endpoints de generación de documentos, o se necesite entender la estructura del documento final.
---

# Document Generation Skill

## Clase principal: `DocumentGenerator`

Archivo: `app/services/document_generator.py`

Genera documentos Word (`.docx`) con la estructura estándar de propuestas Quipux.
La conversión a PDF usa WeasyPrint, ejecutada desde `app/routers/documents.py`.

## Endpoints de Generación (prefijo: `/api/proposals`)

> ⚠️ Todos son **POST**, no GET. Todos incluyen el prefijo `/api/proposals/`.

| Endpoint | Descripción | Query param |
|----------|-------------|------------|
| `POST /api/proposals/{id}/generate-document` | Genera Word (.docx) y lo descarga | `use_innti=true/false` |
| `POST /api/proposals/{id}/generate-pdf` | Genera PDF y lo descarga | `use_innti=true/false` |
| `POST /api/proposals/{id}/generate-annex` | Genera Anexo Técnico (.docx) independiente | — |

- `use_innti=true` (default): genera texto con Innti si los campos están vacíos en la BD
- `use_innti=false`: usa sólo los textos ya guardados en la propuesta (o vacíos)

## Almacenamiento de Documentos

Los documentos se guardan en un **directorio temporal del sistema** antes de servirse:
```
tempfile.gettempdir() / "innti_docs" / propuesta_{id}.docx
                                      propuesta_{id}.pdf
                                      anexo_tecnico_{id}.docx
```
Se sirven como `FileResponse` de FastAPI (no como stream en memoria).

> ⚠️ Nunca subir documentos `.docx` o `.pdf` al repositorio — están en `.gitignore`.

## Secciones del Documento Principal

| # | Sección | Campo en `Proposal` | Generado por |
|---|---------|---------------------|--------------|
| — | Carta de presentación | `letter_content` | `InntiService.generate_cover_letter()` |
| 1 | Contexto | `context_content` | `InntiService.generate_context_section()` |
| 2 | Alcance General de la Propuesta | `scope_content` | `InntiService.generate_scope_section()` |
| 3 | **Plazo** | `validity_period` | Edición **manual** en TipTap (o texto por defecto) |
| 4 | Condiciones Económicas | `economic_conditions` | Tabla auto con productos; o edición manual |
| 4 | — Forma de pago | `payment_terms` | Edición manual |
| 5 | Servicios Excluidos | `excluded_services` | Lista fija de 10 items (editable) |
| 6.1 | Propiedad Intelectual | `ip_section` | Texto fijo unificado con nombre de cliente |
| 6.2 | Confidencialidad | `confidentiality` | Texto fijo con nombre de cliente |
| 6.3 | Principios de Prevención de Actividades Delictivas | — | Texto fijo con nombre de cliente |
| 6.4 | Cumplimiento Transparencia y Ética Empresarial | — | Texto fijo (`lineaetica@quipux.com`) |
| — | **Anexo técnico** | — | `DocumentGenerator.generate_technical_annex()` |

> ⚠️ La fecha de la carta se genera **automáticamente** con `datetime.date.today()` — no requiere edición manual.

> ℹ️ La nota de **indexación IPC** se agrega automáticamente para esquemas `services` y `support_maintenance`.

## Textos Fijos (Constantes en `DocumentGenerator`)

No modificar sin aprobación del área jurídica de Quipux:
- `EXCLUDED_SERVICES` — Lista única de 10 items de servicios excluidos (igual para todos los esquemas)
- `IP_TEXT` — Propiedad intelectual unificada (usa `{client_entity}`, reemplazado con nombre real)
- `CONFIDENTIALITY_TEXT` — Confidencialidad (usa `{client_entity}`)
- `CRIME_PREVENTION_TEXT` — Principios de prevención de actividades delictivas (usa `{client_entity}`)
- `ETHICS_TEXT` — Referencia a `lineaetica@quipux.com`
- `IPC_INDEXATION_TEXT` — Nota de indexación IPC (solo services/support_maintenance)
- `DEFAULT_VALIDITY_TEXT` — Texto de plazo cuando no se edita manualmente

## Modo `combine_schemes`

- `combine_schemes = True` (default): todos los esquemas se incluyen en **un solo documento**.
- `combine_schemes = False`: se genera un documento **separado** por esquema.

## Flujo Interno de Generación

```
POST /api/proposals/{id}/generate-document
    └─► documents router → _build_proposal_docx()
        ├─► Consulta Proposal + Client + ProposalProducts desde BD
        ├─► PortfolioService.get_by_names() → productos del portafolio
        ├─► (Si use_innti=true y campos vacíos) InntiService genera:
        │       - generate_cover_letter() → letter_content
        │       - generate_context_section() → context_content
        │       - generate_scope_section() → scope_content
        │       - Se persisten en BD automáticamente
        └─► DocumentGenerator.generate_proposal_docx(...) → FileResponse(.docx)

POST /api/proposals/{id}/generate-pdf
    └─► _build_proposal_docx() → .docx en /tmp/
        └─► DocumentGenerator.convert_docx_to_pdf() → FileResponse(.pdf)

POST /api/proposals/{id}/generate-annex
    └─► PortfolioService + DocumentGenerator.generate_technical_annex() → FileResponse(.docx)
```

## Limitaciones

- WeasyPrint requiere librerías del sistema (GTK en Windows). En tests se mockea con `MagicMock` desde `conftest.py`.
- Si Innti falla durante la generación, el sistema hace **fallback silencioso** y continúa con campos vacíos (no lanza error al usuario).
