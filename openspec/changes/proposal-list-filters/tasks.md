# Tasks: Filtros y búsqueda en lista de propuestas

## Backend

- [ ] T1 — `app/models/proposal.py`: agregar `@property client_entity`
- [ ] T2 — `app/schemas/proposal.py`: agregar `client_entity: Optional[str] = None` a `ProposalRead`
- [ ] T3 — `app/routers/proposals.py`: agregar params `status` y `q` al endpoint list; join con Client; filtros con `or_`/`ilike`
- [ ] T4 — `backend/tests/test_proposals_api.py`: 4 tests nuevos (B-2, B-3, B-4, B-5)

## Frontend

- [ ] T5 — `src/services/api.ts`: actualizar `proposalApi.list()` con params opcionales `status` y `q`
- [ ] T6 — `src/types/index.ts`: agregar `client_entity?: string` a `Proposal`
- [ ] T7 — `src/pages/ProposalListPage.tsx`: filter state, debounce, re-fetch, UI de filtros, columna cliente
- [ ] T8 — `src/__tests__/ProposalListPage.test.tsx`: 5 tests nuevos (F-1 a F-5)

## Documentación

- [ ] T9 — `.opencode/ARCHITECTURE.md`: actualizar matriz de cobertura si aplica
- [ ] T10 — `openspec/changes/proposal-list-filters/state.yaml`: marcar como applied
