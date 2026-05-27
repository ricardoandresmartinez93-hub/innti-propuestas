# Reglas de Desarrollo - Innti Propuestas

## Stack Tecnológico
- **Backend:** FastAPI, SQLAlchemy (SQLite), Pydantic v2, pydantic-settings.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TipTap (rich text editor).
- **Documentos:** python-docx (Word .docx), WeasyPrint (PDF).
- **IA:** Innti vía LiteLLM (API compatible con OpenAI SDK) — `app/services/innti_service.py`.

## Reglas Generales
- **Idiomas:** Código y comentarios técnicos en inglés. Documentación de usuario, mensajes de error para el cliente y contenido de propuestas en **español**.
- **Commits:** Los mensajes de commit (título, descripción y cualquier anotación) deben estar **siempre en español**.
- **Seguridad:** Nunca incluir secretos en el código. Usar `.env` (jamás subirlo). Revisar `.gitignore` antes de hacer commit.
- **Permisos de bash:** `pytest*` y `npm test*` se ejecutan sin preguntar; `uvicorn`, `npm run dev`, instalaciones requieren confirmación.
- **Pruebas unitarias obligatorias:** Todo código nuevo — tanto en Backend como en Frontend — **debe** ir acompañado de pruebas unitarias en el mismo PR/commit. No se considera completa ninguna funcionalidad sin su cobertura de tests. Ver sección [Testing](#testing) para las convenciones de cada capa.
- **Documentación siempre actualizada:** Después de crear o modificar **cualquier** archivo de código, revisar y actualizar la documentación del proyecto para que refleje los cambios. Los archivos a verificar son:
  - `AGENTS.md` — si cambia stack, reglas, convenciones o flujos técnicos
  - `.claude/agents/*.md` y `.opencode/agents/*.md` — si cambia el comportamiento de un agente
  - `.opencode/skills/*.md` — si cambia la API pública de un servicio, estructura de documento, esquemas o terminología
  - `.opencode/ARCHITECTURE.md` — si cambia la arquitectura, número de pestañas del editor, reglas no-obvias del dominio o la matriz de cobertura
  - `CLAUDE.md` — si se agregan nuevos agents, skills o comandos rápidos

## Backend (FastAPI)
- **Modelos vs Schemas:** Separación clara entre modelos de BD (`app/models/`) y schemas Pydantic (`app/schemas/`).
- **Lógica de negocio:** Los routers deben ser delgados. Toda lógica compleja reside en `app/services/`.
- **Naming:** snake_case para archivos Python y variables.
- **Configuración:** Siempre usar `get_settings()` de `app/config.py` (Singleton con `lru_cache`).
- **DB:** Usar `get_db` de `app/database.py` como dependencia en los routers; nunca instanciar Session directamente.

## Frontend (React + TypeScript)
- **Componentes:** Solo componentes funcionales con Hooks.
- **Estilos:** Priorizar Tailwind CSS. Evitar CSS inline salvo casos TipTap.
- **Tipado:** Sin `any`. Todas las interfaces en `src/types/index.ts`.
- **API calls:** Centralizar en `src/services/api.ts`.

## Dominio de Propuestas

### Esquemas de Pago (MVP)
| Esquema (`SchemeType`) | Valor enum | Frecuencia de pago |
|------------------------|------------|-------------------|
| Licenciamiento | `licensing` | Pago único |
| Prestación de Servicios | `services` | Mensual |
| Soporte y Mantenimiento | `support_maintenance` | Anual |

> **Fase 2 (no disponibles en MVP):** `concession_bpo` y `supply`. No implementar lógica para estos esquemas.

### Flujo de Estados de Propuesta
Los nombres de estado son **valores del enum `ProposalStatus`** (usar siempre estas cadenas exactas):

```
DRAFT ──► PENDING_REVIEW ──► REVIEWED ──► PENDING_VP ──► APPROVED ──► SENT_TO_CLIENT
               │                                │
               └──► REJECTED ◄─────────────────┘
                        │
                        └──► DRAFT (puede volver a borrador)
```

> ⚠️ Solo `PENDING_REVIEW` y `PENDING_VP` pueden ir a `REJECTED`.
> `REVIEWED` **únicamente** avanza a `PENDING_VP` — no puede rechazarse en ese estado.

> **`submit-review` es multi-transición:** detecta el estado actual y avanza en consecuencia:
> `DRAFT → PENDING_REVIEW` · `REVIEWED → PENDING_VP` · `APPROVED → SENT_TO_CLIENT` · `REJECTED → DRAFT`

| Estado (`ProposalStatus`) | Valor | Descripción |
|---------------------------|-------|-------------|
| `DRAFT` | `"draft"` | En edición |
| `PENDING_REVIEW` | `"pending_review"` | Enviada a revisión (Ángela) |
| `REVIEWED` | `"reviewed"` | Aprobada por Ángela, pendiente VP |
| `PENDING_VP` | `"pending_vp"` | Enviada a VP (Juan Pablo) |
| `APPROVED` | `"approved"` | Aprobada por VP |
| `REJECTED` | `"rejected"` | Rechazada (cualquier etapa); puede volver a DRAFT |
| `SENT_TO_CLIENT` | `"sent_to_client"` | Estado final — enviada al cliente |

### Roles de Aprobación (`ApprovalRole`)
- `REVIEWER` → Ángela (primera revisión): aprueba `PENDING_REVIEW` → `REVIEWED`; o rechaza → `REJECTED`
- `VP` → Juan Pablo (aprobación final): aprueba `PENDING_VP` → `APPROVED`; o rechaza → `REJECTED`

### Endpoints de Aprobación (prefijo real: `/api/proposals`)
| Endpoint | Acción |
|----------|--------|
| `POST /api/proposals/{id}/submit-review` | Detecta estado actual y avanza: DRAFT→PENDING_REVIEW · REVIEWED→PENDING_VP · APPROVED→SENT_TO_CLIENT · REJECTED→DRAFT |
| `POST /api/proposals/{id}/approve` | Registra aprobación (body: `role`, `approver_name`, `action: "approved"`, `comments?`) |
| `POST /api/proposals/{id}/reject` | Registra rechazo (body: `role`, `approver_name`, `action: "rejected"`, `comments` obligatorio) |
| `POST /api/proposals/{id}/generate-document` | Genera y descarga el Word (usa Innti si `use_innti=true`) |
| `POST /api/proposals/{id}/generate-pdf` | Genera y descarga el PDF |
| `POST /api/proposals/{id}/generate-annex` | Genera y descarga el Anexo Técnico (.docx) |

### Portafolio
- Fuente de verdad: `ListaPortafolio.xlsx` (raíz del proyecto).
- Servicio: `app/services/portfolio_service.py` → clase `PortfolioService`.
- El campo `portfolio_file_path` en `config.py` apunta a este archivo.

## Testing

> ⚠️ **Regla de cobertura:** Todo código nuevo (servicio, router, componente, hook, utilidad) **debe** incluir pruebas unitarias en el mismo entregable. El agente `pre-commit-validation` verifica esto antes de cada commit.

### Backend (pytest)
- Ejecutar desde `backend/` con el venv activado: `pytest tests/ -v`
- BD de pruebas: `sqlite:///./test_innti.db` (creada/destruida por `conftest.py`).
- `conftest.py` mockea `weasyprint` y `mammoth` con `unittest.mock.MagicMock`.
- Fixtures principales: `db_session`, `client` (TestClient), `sample_client_data`, `sample_proposal_data`.
- **Qué testear:** cada función en `app/services/`, cada endpoint en `app/routers/`, y cualquier utilidad nueva.
- **Convención de archivos:** `tests/test_<módulo>.py` (ej. `tests/test_proposal_service.py`).
- **Mocks:** usar `unittest.mock.patch` para aislar dependencias externas (Innti, WeasyPrint, sistema de archivos).

### Frontend (Vitest + Testing Library)
- Ejecutar desde `frontend/`: `npm test`
- **Qué testear:** cada componente React nuevo, cada custom hook, y las funciones de `src/services/api.ts`.
- **Convención de archivos:** colocar el test junto al componente como `ComponentName.test.tsx` o en `src/__tests__/`.
- **Mocks:** usar `vi.mock` para las llamadas a la API (`src/services/api.ts`) y para módulos de terceros.
- **No usar `any`** en los tests — respetar el tipado igual que en el código de producción.
