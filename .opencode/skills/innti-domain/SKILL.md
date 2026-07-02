---
name: innti-domain
description: Proporciona el contexto de negocio de Innti Propuestas (Quipux): esquemas de pago, flujo de aprobación, estados de propuesta y terminología clave. Usar cuando se trabaje con lógica de propuestas, aprobaciones o tipos de contrato.
---

# Innti Domain Skill

Contexto de negocio para operar sobre el sistema de propuestas comerciales de Quipux S.A.S.

## Esquemas de Pago — MVP

| Esquema | Enum (`SchemeType`) | Frecuencia |
|---------|---------------------|------------|
| Licenciamiento | `licensing` | Pago único (`unico`) |
| Prestación de Servicios | `services` | Mensual (`mensual`) |
| Soporte y Mantenimiento | `support_maintenance` | Anual (`anual`) |

> ⚠️ **Fase 2 — NO implementados en MVP:** `concession_bpo` (Concesión/BPO) y `supply` (Suministro).
> El modelo los define como enum pero **no se deben incluir en flujos del MVP**.
> Ver `app/models/proposal.py` → `MVP_SCHEME_TYPES`.

## Flujo Completo de Estados (`ProposalStatus`)

```
DRAFT ──► PENDING_REVIEW ──► REVIEWED ──► PENDING_VP ──► APPROVED ──► SENT_TO_CLIENT
               │                               │
               └──► REJECTED ◄────────────────┘
                        │
                        └──► DRAFT (puede retornar a borrador)
```

> ⚠️ **Regla crítica**: `REVIEWED` **solo puede avanzar a `PENDING_VP`** — no puede ir a `REJECTED`.
> Solo `PENDING_REVIEW` y `PENDING_VP` pueden rechazarse.
>
> La transición `REVIEWED → PENDING_VP` se dispara con el mismo endpoint `submit-review`
> (el servidor detecta el estado actual y ejecuta la transición correcta automáticamente).

### Tabla de estados

| Estado | Valor string | Descripción |
|--------|-------------|-------------|
| `DRAFT` | `"draft"` | Borrador — en edición por el comercial |
| `PENDING_REVIEW` | `"pending_review"` | Enviada a primera revisión (Ángela) |
| `REVIEWED` | `"reviewed"` | Aprobada por Ángela; pendiente aprobación VP |
| `PENDING_VP` | `"pending_vp"` | Enviada a Juan Pablo para aprobación final |
| `APPROVED` | `"approved"` | Aprobada por VP; lista para enviar al cliente |
| `REJECTED` | `"rejected"` | Rechazada; puede volver a `DRAFT` |
| `SENT_TO_CLIENT` | `"sent_to_client"` | Estado final — enviada formalmente al cliente |

### Roles de Aprobación (`ApprovalRole`)
- `REVIEWER` → **Ángela**: aprueba/rechaza la propuesta en estado `PENDING_REVIEW`
- `VP` → **Juan Pablo Ramírez Madrid** (Vicepresidente de Nuevos Negocios): aprueba/rechaza en estado `PENDING_VP`

El servicio `app/services/approval_service.py` contiene toda la lógica de transiciones válidas (`VALID_TRANSITIONS`).

## Servicio de IA — Innti

- Clase: `InntiService` en `app/services/innti_service.py`
- Usa el SDK de OpenAI apuntando a `litellm.quipux.com/v1` (LiteLLM de Quipux)
- Métodos disponibles:
  - `generate_context_section(client_entity, proposal_title)` — Sección de contexto/introducción
  - `generate_scope_section(products, scheme_type)` — Sección de alcance
  - `generate_cover_letter(client_name, position, entity, subject)` — Carta de presentación
  - `enrich_product_description(product_name, base_description)` — Enriquece descripción técnica para el anexo

## Relación Producto → Esquema (un esquema por producto)

Desde julio 2026, **cada producto de una propuesta tiene asignado exactamente UN
esquema** (`ProposalScheme.product_id`). Ya NO existe la intersección de esquemas
entre productos.

- **Contrato de creación**: en `POST /api/proposals/` cada producto embebe su
  esquema en el campo `scheme`. La lista `schemes` a nivel propuesta (contrato
  viejo) retorna 422.
- **Esquemas permitidos POR PRODUCTO**: columna 9 ("Esquemas Permitidos") del
  Excel, o todos los MVP schemes si está vacía. Método clave:
  `PortfolioService.get_allowed_schemes_for_product(product) -> List[str]`.
  `GET /api/portfolio/products` devuelve `allowed_schemes` ya resuelto.
- **Regla dura QloudSI**: los productos con `product_type` que contenga
  "QloudSI" (case-insensitive) NUNCA pueden tener el esquema `licensing`,
  aunque el Excel lo liste. Fuente de verdad:
  `is_qloudsi_product()` + `QLOUDSI_FORBIDDEN_SCHEMES` en
  `app/services/portfolio_service.py`. El backend valida con 422 y el
  portafolio excluye `licensing` de `allowed_schemes` para QloudSI.
- **Dos productos pueden compartir el mismo tipo de esquema** — cada uno
  mantiene su propia fila `ProposalScheme` con contenido independiente.

## Generación de documentos (`combine_schemes`)

- `combine_schemes=true` → **documento unificado**: 1 archivo con un bloque
  «PRODUCTO — ESQUEMA» por producto (alcance, plazo, condiciones económicas,
  forma de pago, exclusiones, PI de SU esquema).
- `combine_schemes=false` → **documentos separados**: un `.docx`/`.pdf` POR
  PRODUCTO (nombre con slug del producto), empaquetados en ZIP. Requiere ≥2
  productos (validado con 422 al crear).
- **Propuestas legadas**: esquemas con `product_id NULL` (previas a la
  migración `scripts/migrate_schemes_per_product.py`) conservan el
  comportamiento anterior: bloques y archivos POR ESQUEMA. El switch es
  `Proposal.uses_product_schemes`.

## Terminología Clave
- **Innti**: Motor de IA corporativa de Quipux (LiteLLM).
- **Portafolio**: Catálogo de productos/servicios de Quipux definido en `ListaPortafolio.xlsx`.
- **Propuesta**: Documento Word/PDF generado para el cliente que contiene carta, contexto, alcance, condiciones económicas y anexo técnico.
- **Esquema**: Modalidad comercial de la propuesta (licenciamiento, servicios, soporte).
- **Anexo técnico**: Sección de la propuesta con la descripción detallada de cada producto.
- **Ángela**: Revisora interna (rol `REVIEWER`).
- **Juan Pablo**: Vicepresidente de Nuevos Negocios (rol `VP`), aprueba la propuesta final.
