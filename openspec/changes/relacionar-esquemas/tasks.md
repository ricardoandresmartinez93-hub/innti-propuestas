# Tasks: Relacionar esquemas por producto

**Change:** relacionar-esquemas

## Backend

- [x] T1. Modelo: `ProposalScheme.product_id` (FK nullable, index) + relación
  `ProposalProduct.scheme` (uselist=False) + propiedad
  `Proposal.uses_product_schemes`. Tests de modelo.
- [x] T2. Regla QloudSI: `is_qloudsi_product` + `QLOUDSI_FORBIDDEN_SCHEMES` en
  `portfolio_service.py`. Tests (variantes de casing, None, vacío, Plataforma).
- [x] T3. `PortfolioService.get_allowed_schemes_for_product` (columna 9 ∪ MVP,
  menos QloudSI). Eliminar `get_allowed_schemes_for_products` y sus usos/tests.
  Router portafolio pobla `allowed_schemes` con el método nuevo. Tests.
- [x] T4. Schemas: `ProposalProductCreate.scheme` obligatorio; `ProposalCreate`
  sin `schemes` top-level (422 explícito); validador separado ≥2 productos;
  `ProposalProductRead.scheme`. Tests.
- [x] T5. Router create: validación MVP por producto, QloudSI→422, columna 9
  por producto→422; crear esquemas con `product_id`. Tests (feliz multi-producto,
  QloudSI+licensing 422, QloudSI+services 201, separado 1 producto 422,
  payload viejo 422).
- [x] T6. Documentos: unificado con bloques por producto («PRODUCTO — ESQUEMA»),
  separado un archivo por producto (slug), Innti IA con producto vinculado,
  legadas intactas. Tests (2 productos mismo esquema → 2 bloques; 3 productos →
  ZIP de 3; legada → comportamiento anterior).
- [x] T7. Migración `migrate_schemes_per_product.py` idempotente con backfill
  1-producto y reporte de legadas. Test con BD temporal. Correr contra BD dev.

## Frontend

- [x] T8. `types/index.ts`: producto con `scheme` embebido; payload de creación
  sin `schemes` top-level. `api.ts` adaptado.
- [x] T9. `SchemeSelector`: tarjeta por producto, radio de esquemas permitidos,
  nota QloudSI, frecuencia por producto, toggle unificado/separado con ≥2
  productos, emitir solo cuando todos tienen esquema. Reescribir tests.
- [x] T10. `NewProposalPage`: eliminar intersección, payload nuevo, no avanzar
  sin esquemas completos. `ProposalDetailPage`: rótulo «Producto — Esquema»
  (legadas conservan rótulo actual). Tests.

## Docs

- [x] T11. `.opencode/skills/innti-domain/SKILL.md` (sección Restricción
  Producto→Esquemas reescrita), `docs/API.md`, `README.md`.
- [x] T12. Verificación spec escenario por escenario + suites completas.
