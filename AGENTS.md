# Reglas de Desarrollo - Innti Propuestas

## Stack Tecnológico
- **Backend:** FastAPI, SQLAlchemy (SQLite), Pydantic v2, pydantic-settings.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS, TipTap (rich text editor).
- **Documentos:** python-docx (Word .docx), WeasyPrint (PDF).
- **IA:** Innti vía LiteLLM (API compatible con OpenAI SDK) — `app/services/innti_service.py`.

## Reglas Generales
- **Idiomas:** Código y comentarios técnicos en inglés. Documentación de usuario, mensajes de error para el cliente y contenido de propuestas en **español**.
- **Seguridad:** Nunca incluir secretos en el código. Usar `.env` (jamás subirlo). Revisar `.gitignore` antes de hacer commit.
- **Permisos de bash:** `pytest*` y `npm test*` se ejecutan sin preguntar; `uvicorn`, `npm run dev`, instalaciones requieren confirmación.

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
DRAFT → PENDING_REVIEW → REVIEWED → PENDING_VP → APPROVED → SENT_TO_CLIENT
                ↓               ↓          ↓
            REJECTED        REJECTED   REJECTED
                ↓
             DRAFT (puede volver a borrador)
```

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
- `REVIEWER` → Ángela (primera revisión): aprueba de `PENDING_REVIEW` a `REVIEWED`
- `VP` → Juan Pablo (aprobación final): aprueba de `PENDING_VP` a `APPROVED`

### Portafolio
- Fuente de verdad: `ListaPortafolio.xlsx` (raíz del proyecto).
- Servicio: `app/services/portfolio_service.py` → clase `PortfolioService`.
- El campo `portfolio_file_path` en `config.py` apunta a este archivo.

## Testing
- Ejecutar desde `backend/` con el venv activado.
- BD de pruebas: `sqlite:///./test_innti.db` (creada/destruida por `conftest.py`).
- `conftest.py` mockea `weasyprint` y `mammoth` con `unittest.mock.MagicMock`.
- Fixtures principales: `db_session`, `client` (TestClient), `sample_client_data`, `sample_proposal_data`.
