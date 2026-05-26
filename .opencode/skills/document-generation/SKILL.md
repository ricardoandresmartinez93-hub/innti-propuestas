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

| Sección | Campo en `Proposal` | Generado por |
|---------|---------------------|--------------|
| Carta de presentación | `letter_content` | `InntiService.generate_cover_letter()` |
| Contexto / Introducción | `context_content` | `InntiService.generate_context_section()` |
| Alcance | `scope_content` | `InntiService.generate_scope_section()` |
| Condiciones económicas | `economic_conditions` | Edición **manual** en TipTap |
| Forma de pago | `payment_terms` | Edición manual |
| Servicios excluidos | `excluded_services` | Auto-completado según esquema (editable) |
| Propiedad intelectual | `ip_section` | Texto fijo según esquema (editable) |
| Confidencialidad y ética | `confidentiality` | Texto fijo — **no editar sin jurídica** |
| **Anexo técnico** | — | `DocumentGenerator.generate_technical_annex()` |

## Textos Fijos (Constantes en `DocumentGenerator`)

No modificar sin aprobación del área jurídica de Quipux:
- `CONFIDENTIALITY_TEXT` — Cláusula de confidencialidad
- `ETHICS_TEXT` — Declaración de ética empresarial
- `EXCLUDED_SERVICES_LICENSING` — Exclusiones para licenciamiento
- `EXCLUDED_SERVICES_SUPPORT` — Exclusiones para soporte y mantenimiento
- `IP_LICENSING` — Texto de propiedad intelectual para licenciamiento
- `IP_SERVICES` — Texto de propiedad intelectual para servicios

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
