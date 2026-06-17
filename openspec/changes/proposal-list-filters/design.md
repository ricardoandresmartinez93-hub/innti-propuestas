# Design: Filtros y búsqueda en lista de propuestas

## Backend

### 1. Modelo `Proposal` — property `client_entity`

Agregar `@property client_entity` al modelo ORM. Pydantic v2 con
`from_attributes=True` lo serializa automáticamente sin cambiar el schema.

```python
# app/models/proposal.py
@property
def client_entity(self) -> Optional[str]:
    return self.client.entity if self.client else None
```

### 2. Schema `ProposalRead` — campo `client_entity`

```python
# app/schemas/proposal.py
client_entity: Optional[str] = None
```

### 3. Endpoint `list_proposals` — query params opcionales

```python
GET /api/proposals/
  ?status: Optional[ProposalStatus] = None
  ?q:      Optional[str]            = None   # búsqueda en title, code, client.entity, client.name
  ?skip:   int = 0
  ?limit:  int = 50
```

Join con `Client` (outer join para no excluir propuestas sin cliente).
`ilike` para búsqueda case-insensitive. Condiciones de filtro con `and_`/`or_`.

Imports adicionales: `or_` de `sqlalchemy`, `Client` model.

## Frontend

### 4. `proposalApi.list()` — nuevos params opcionales

```typescript
list: (skip = 0, limit = 50, status?: ProposalStatus, q?: string) => ...
```

Solo se envían los params presentes (no enviar `status=undefined`).

### 5. `ProposalListPage` — filter state + debounce

```typescript
const [statusFilter, setStatusFilter] = useState<ProposalStatus | ''>('')
const [searchText, setSearchText]     = useState('')
const [debouncedSearch, setDebouncedSearch] = useState('')
```

`useEffect` con `setTimeout(300ms)` sobre `searchText` → `debouncedSearch`.
`useEffect` sobre `[statusFilter, debouncedSearch]` → re-fetch.

### 6. UI de filtros

- `<input type="text">` — placeholder "Buscar por título, código o cliente…"
- `<select>` — opción vacía "Todos los estados" + 7 estados del enum
- Botón "Limpiar" — visible solo si hay algún filtro activo
- Badge contador: "N propuestas" (usa `proposals.length` del estado local)
- Nueva columna "Cliente" en la tabla mostrando `client_entity`

## Decisiones

| Decisión | Alternativa descartada | Razón |
|----------|------------------------|-------|
| Filtrado en backend | Filtrado en frontend (solo 50 items) | Correcto con cualquier volumen de datos |
| `@property` en el modelo | Schema `ProposalListRead` separado | Menos cambios; Pydantic v2 lo serializa sin extras |
| Debounce manual con setTimeout | Librería externa (use-debounce) | Dependencia innecesaria para un caso simple |
| Join outer | Subquery | Más simple; propuestas sin cliente (edge case) siguen apareciendo |
