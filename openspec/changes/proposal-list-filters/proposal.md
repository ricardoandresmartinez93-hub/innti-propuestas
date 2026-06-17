# Proposal: Filtros y búsqueda en lista de propuestas

**Change:** proposal-list-filters
**Date:** 2026-06-17
**Status:** approved

## Intent

La tabla de propuestas actualmente carga hasta 50 registros sin ningún mecanismo
de filtrado. Con 50+ propuestas el usuario no puede localizar lo que busca.

## Scope

- Filtro por estado (`status`) — desplegable con todos los estados del enum.
- Búsqueda de texto libre (`q`) — por título, código o entidad/nombre del cliente.
- Ambos filtros se aplican en el backend (no solo en los 50 resultados cargados).
- La respuesta del listado incluirá `client_entity` para mostrar el cliente en la tabla.
- Contador de resultados visible ("X propuestas").

## Out of scope

- Filtro por rango de fechas (siguiente iteración).
- Paginación (siguiente iteración).
- Filtros persistidos en localStorage.

## Approach

Backend: query params opcionales `status` y `q` en `GET /api/proposals/`.
Join con tabla `clients` para búsqueda por entidad. Property `client_entity`
en el modelo ORM para que Pydantic la serialice automáticamente.

Frontend: estado de filtros en el componente, debounce de 300 ms en `q`,
re-fetch al cambiar cualquier filtro.
