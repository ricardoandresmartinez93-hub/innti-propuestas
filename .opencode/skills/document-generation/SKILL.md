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

> ⚠️ Desde el refactor de mayo 2026, el contenido se reparte entre **global** (Proposal)
> y **por esquema** (ProposalScheme). Ver `app/services/proposal_content_resolver.py`.

| # | Sección | Scope | Campo | Generado por |
|---|---------|-------|-------|--------------|
| — | Carta de presentación | global | `Proposal.letter_content` | `InntiService.generate_cover_letter()` |
| 1 | Contexto | global | `Proposal.context_content` | `InntiService.generate_context_section()` |
| 2 | Alcance General | **por esquema** | `ProposalScheme.scope_content` | `InntiService.generate_scope_section(scheme)` |
| 3 | Plazo | **por esquema** | `ProposalScheme.validity_period` | Manual o `InntiService.generate_validity_section(scheme)` |
| 4 | Condiciones Económicas | **por esquema** | `ProposalScheme.economic_conditions` | Tabla auto con productos según el esquema, o manual |
| 4 | — Forma de pago | **por esquema** | `ProposalScheme.payment_terms` | Manual o `InntiService.generate_payment_terms_section(scheme)` |
| 5 | Servicios Excluidos | **por esquema** | `ProposalScheme.excluded_services` | Default `EXCLUDED_SERVICES_BY_SCHEME` (vacío para SaaS) |
| 6.1 | Propiedad Intelectual | **por esquema** | `ProposalScheme.ip_section` | Default `IP_TEXT_BY_SCHEME[scheme_type]` |
| 6.2 | Confidencialidad | global | `Proposal.confidentiality` (o `CONFIDENTIALITY_TEXT`) | Texto fijo con nombre de cliente |
| 6.3 | Prevención de Actividades Delictivas | global | — | Texto fijo `CRIME_PREVENTION_TEXT` |
| 6.4 | Transparencia y Ética Empresarial | global | — | Texto fijo `ETHICS_TEXT` |
| — | **Anexo técnico** | global | — | `DocumentGenerator.generate_technical_annex()` |

> ⚠️ La fecha de la carta se genera **automáticamente** con `datetime.date.today()` — no requiere edición manual.

> ℹ️ La nota de **indexación IPC** se agrega automáticamente para esquemas `services` y `support_maintenance`.

## Textos Fijos (Constantes en `DocumentGenerator`)

No modificar sin aprobación del área jurídica de Quipux:
- `EXCLUDED_SERVICES_BY_SCHEME` — Dict `scheme_type → lista`. `licensing` y `support_maintenance` reciben la lista completa; **`services` queda vacío** (SaaS no excluye nada).
- `IP_TEXT_BY_SCHEME` — Dict `scheme_type → texto` con `{client_entity}` parametrizado. Cada esquema tiene su propia variante (regla del PDF de reunión).
- `IP_TEXT`, `EXCLUDED_SERVICES` — Aliases de retrocompatibilidad que apuntan al default de `licensing`.
- `CONFIDENTIALITY_TEXT` — Confidencialidad (usa `{client_entity}`)
- `CRIME_PREVENTION_TEXT` — Principios de prevención de actividades delictivas (usa `{client_entity}`)
- `ETHICS_TEXT` — Referencia a `lineaetica@quipux.com`
- `IPC_INDEXATION_TEXT` — Nota de indexación IPC (solo services/support_maintenance)
- `DEFAULT_VALIDITY_TEXT` — Texto de plazo cuando no se edita manualmente

Acceso preferido: `DocumentGenerator.get_ip_text(scheme_type)` y `DocumentGenerator.get_excluded_services(scheme_type)`.

## Modo `combine_schemes`

- `combine_schemes = True` (default): un único documento generado por `generate_combined_proposal_docx`, con un bloque "ESQUEMA: …" por cada esquema (contenido distinto por esquema en alcance, plazo, condiciones, IP, exclusiones).
- `combine_schemes = False`: ZIP con un documento por esquema, cada uno con SU contenido específico vía `resolve_scheme_content`. **Requiere ≥ 2 esquemas** (el validator de `ProposalCreate` rechaza con 422 si hay menos).

## Flujo Interno de Generación

```
POST /api/proposals/{id}/generate-document
    ├─► (combine_schemes=False y >=2 esquemas)
    │       └─► _build_separate_docx_files()
    │           ├─► _ensure_content_ready() — si use_innti=True, genera por esquema individual
    │           │   y persiste en ProposalScheme.<campo>
    │           ├─► loop esquemas → resolve_scheme_content(proposal, scheme)
    │           │   └─► DocumentGenerator.generate_proposal_docx(...) → un .docx por esquema
    │           └─► _pack_zip(...) → FileResponse(.zip)
    │
    └─► (combine_schemes=True o un solo esquema)
            └─► _build_combined_docx()
                ├─► _ensure_content_ready() — si use_innti=True, genera todo
                ├─► resolve_combined_content(proposal)
                └─► DocumentGenerator.generate_combined_proposal_docx(...) → FileResponse(.docx)

POST /api/proposals/{id}/generate-pdf
    └─► igual pero con convert_docx_to_pdf() después de cada generación

POST /api/proposals/{id}/generate-annex
    └─► PortfolioService + DocumentGenerator.generate_technical_annex() → FileResponse(.docx)
```

## Limitaciones

- WeasyPrint requiere librerías del sistema (GTK en Windows). En tests se mockea con `MagicMock` desde `conftest.py`.
- Si Innti falla durante la generación, el sistema hace **fallback silencioso** y continúa con campos vacíos (no lanza error al usuario).
