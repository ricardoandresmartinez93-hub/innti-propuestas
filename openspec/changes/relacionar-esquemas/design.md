# Design: Relacionar esquemas por producto

**Change:** relacionar-esquemas

## D1 — Modelo: vínculo esquema→producto

`ProposalScheme` gana `product_id` (Integer, `ForeignKey("proposal_products.id")`,
`nullable=True`, index). Relación 1:1 `ProposalProduct.scheme` (`uselist=False`).
Se conserva `proposal_id` para no romper `proposal.schemes` (consultas, resolver,
detalle). La restricción "exactamente 1 esquema por producto" se aplica a nivel
de API (Pydantic + router), NO como unique constraint en BD, para que las filas
legadas (`product_id NULL`) sigan siendo válidas.

Se agrega la propiedad `Proposal.uses_product_schemes`: True si la propuesta
tiene esquemas y TODOS tienen `product_id`. Es el switch entre el flujo nuevo
(por producto) y el legado (por esquema).

Alternativa descartada: fusionar los campos del esquema dentro de
`ProposalProduct` — infla el modelo, rompe resolver/generador en muchos más
puntos y pierde la separación producto ("qué se vende") / esquema ("cómo se cobra").

## D2 — Regla QloudSI

En `backend/app/services/portfolio_service.py`:

- `is_qloudsi_product(product_type: Optional[str]) -> bool` —
  `"qloudsi" in (product_type or "").lower()`.
- `QLOUDSI_FORBIDDEN_SCHEMES = {"licensing"}`.

Única fuente de verdad. La UI no duplica la regla: consume `allowed_schemes`
ya filtrado por el backend.

## D3 — Esquemas permitidos por producto

`PortfolioService.get_allowed_schemes_for_product(product) -> List[str]`:
(columna 9 del Excel, o todos los MVP si está vacía) menos
`QLOUDSI_FORBIDDEN_SCHEMES` cuando `is_qloudsi_product(product.product_type)`.

`GET /api/portfolio/products` pobla `allowed_schemes` con este método.
El método de intersección `get_allowed_schemes_for_products` se ELIMINA
junto con sus usos y tests.

## D4 — Contrato de creación

- `ProposalProductCreate.scheme: ProposalSchemeCreate` (obligatorio).
- `ProposalCreate` pierde el campo `schemes`; enviar `schemes` top-level → 422
  con mensaje explícito (validador que rechaza el contrato viejo).
- Validadores: (a) cada producto trae exactamente 1 esquema (campo requerido);
  (b) `combine_schemes=False` requiere ≥2 productos; (c) QloudSI + `licensing`
  → 422 en el router (usa `product_type` del payload y, si viene vacío, lo
  resuelve desde el portafolio por nombre); (d) columna 9 por producto → 422.
- `ProposalProductRead.scheme: Optional[ProposalSchemeRead]`. `ProposalRead`
  conserva la lista `schemes` para lectura (compatibilidad con la página de
  detalle y flujos existentes).

## D5 — Documentos

- Unificado (`combine_schemes=True`) con `uses_product_schemes`: los bloques se
  construyen iterando `proposal.products`; cada bloque lleva encabezado
  «PRODUCTO — ESQUEMA» y las secciones de SU esquema; el alcance del bloque
  lista solo su producto. Dos productos con el mismo esquema → dos bloques.
- Separado (`combine_schemes=False`, ≥2 productos) con `uses_product_schemes`:
  un `.docx` por PRODUCTO (`propuesta_{id}_{slug-producto}_{uid}.docx`),
  empaquetados en ZIP. Ídem PDF.
- Generación con Innti IA por esquema: recibe solo el nombre del producto
  vinculado, no todos los productos de la propuesta.
- Legadas (`uses_product_schemes=False`): flujo actual sin cambios.

Implementación: cada item de `schemes_payload` puede llevar `block_heading`
y `products` (subconjunto para ese bloque); `DocumentGenerator` los usa si
están presentes y cae al comportamiento actual si no.

## D6 — Migración

`backend/scripts/migrate_schemes_per_product.py` (patrón de
`migrate_scheme_content.py`):

1. `ALTER TABLE proposal_schemes ADD COLUMN product_id` si falta.
2. Backfill: propuesta con exactamente 1 producto → vincula sus esquemas;
   con 2+ productos → deja NULL y reporta por consola como legada.
3. Idempotente.
