# Spec: Filtros y búsqueda en lista de propuestas

## Escenarios de backend

**B-1 — Sin filtros:** `GET /api/proposals/` devuelve todas las propuestas
ordenadas por `updated_at` desc, igual que hoy.

**B-2 — Filtro por estado:** `GET /api/proposals/?status=draft` devuelve
solo propuestas en estado `draft`.

**B-3 — Búsqueda por texto:** `GET /api/proposals/?q=mun` devuelve propuestas
cuyo `title`, `code`, `client.entity` o `client.name` contengan "mun"
(case-insensitive, LIKE `%mun%`).

**B-4 — Filtros combinados:** `GET /api/proposals/?status=approved&q=mun`
aplica ambas condiciones (AND).

**B-5 — Respuesta incluye cliente:** Cada propuesta en el listado expone
`client_entity: Optional[str]` con la entidad del cliente asociado.

## Escenarios de frontend

**F-1 — UI inicial:** Al entrar a `/proposals` se ve un campo de búsqueda
de texto y un desplegable de estado. Sin filtros activos, muestra todas las
propuestas y el contador "X propuestas".

**F-2 — Filtro por estado:** Al seleccionar un estado en el desplegable,
la tabla se actualiza mostrando solo propuestas en ese estado.

**F-3 — Búsqueda de texto:** Al escribir en el campo de búsqueda, se espera
300 ms (debounce) y se re-fetcha con `q=<texto>`.

**F-4 — Limpiar filtros:** El botón "Limpiar" (visible solo con filtros activos)
restaura ambos filtros a vacío y re-fetcha.

**F-5 — Columna cliente:** La tabla muestra una columna "Cliente" con
`client_entity` de la propuesta.

**F-6 — Estado vacío filtrado:** Si la combinación de filtros no devuelve
resultados, se muestra "No hay propuestas para los filtros aplicados."

## Requerimientos no funcionales

- Debounce de 300 ms en el campo de texto para no hacer fetch en cada tecla.
- El listado sigue ordenado por `updated_at` desc después de filtrar.
- Tests obligatorios: backend (4 nuevos) + frontend (5 nuevos).
