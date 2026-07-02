# Spec: Relacionar esquemas por producto

**Change:** relacionar-esquemas

## R1 — Un esquema por producto

Cada producto incluido en una propuesta tiene asignado exactamente UN esquema.

- **E1.1** Dado un payload de creación donde cada producto incluye `scheme`,
  cuando se hace `POST /api/proposals/`, entonces responde 201 y cada
  `ProposalScheme` queda vinculado (`product_id`) a su producto.
- **E1.2** Dado un payload donde algún producto NO incluye `scheme`,
  entonces responde 422.
- **E1.3** Dado un payload con la lista `schemes` a nivel propuesta (contrato
  viejo), entonces responde 422 con mensaje que indica que el esquema va
  dentro de cada producto.

## R2 — Selección múltiple de productos con esquemas independientes

- **E2.1** Dado un payload con 3 productos con esquemas distintos (A, B, C),
  entonces responde 201 con 3 esquemas, cada uno vinculado a su producto.
- **E2.2** Dado un payload con 2 productos con el MISMO tipo de esquema,
  entonces responde 201 con 2 filas `ProposalScheme` independientes
  (no se fusionan).

## R3 — Excepción QloudSI

Productos con `product_type` que contenga "QloudSI" (case-insensitive) no pueden
tener el esquema `licensing`.

- **E3.1** Dado un producto con `product_type="Servicio QloudSI"` y
  `scheme.scheme_type="licensing"`, cuando se hace `POST /api/proposals/`
  (API directa, sin pasar por la UI), entonces responde 422 con mensaje claro.
- **E3.2** Dado el mismo producto con `scheme_type="services"`, entonces 201.
- **E3.3** Dado `GET /api/portfolio/products`, entonces los productos QloudSI
  NUNCA incluyen `licensing` en `allowed_schemes`, aunque el Excel lo liste.
- **E3.4** Los productos tipo "Plataforma" SÍ pueden tener `licensing`.

## R4 — Documento unificado

- **E4.1** Dada una propuesta con `combine_schemes=True` y N productos con
  esquema, cuando se genera el documento, entonces se produce 1 único `.docx`
  con un bloque por producto (encabezado «PRODUCTO — ESQUEMA») con las
  secciones de SU esquema.
- **E4.2** Dados 2 productos con el mismo tipo de esquema, el documento
  unificado contiene 2 bloques (uno por producto).

## R5 — Documentos separados

- **E5.1** Dada una propuesta con `combine_schemes=False` y N≥2 productos,
  cuando se genera el documento, entonces se produce un ZIP con N `.docx`
  (uno por producto, nombre con slug del producto). Ídem PDF.
- **E5.2** Dado un payload de creación con `combine_schemes=False` y 1 solo
  producto, entonces responde 422 (separado requiere ≥2 productos).

## R6 — Restricción columna 9 por producto (sin intersección)

- **E6.1** Dado un producto cuyo Excel (columna 9) restringe a `licensing`,
  y un payload que le asigna `services`, entonces responde 422.
- **E6.2** La resolución de `allowed_schemes` es POR PRODUCTO; el método de
  intersección `get_allowed_schemes_for_products` no existe más en el código.
- **E6.3** Producto sin restricción en columna 9 → todos los MVP schemes
  (menos `licensing` si es QloudSI).

## R7 — Propuestas legadas

- **E7.1** Dada una propuesta existente cuyos esquemas tienen `product_id NULL`
  (datos previos a la migración), la generación de documentos conserva el
  comportamiento anterior (bloques/archivos por esquema).
- **E7.2** El script de migración vincula los esquemas de propuestas con
  exactamente 1 producto; con 2+ productos deja NULL y lo reporta. Es idempotente.
