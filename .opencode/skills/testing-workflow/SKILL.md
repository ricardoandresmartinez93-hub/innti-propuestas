---
name: testing-workflow
description: Define el flujo correcto para ejecutar pruebas del backend (pytest) y frontend (vitest). Usar antes de commits o tras cambios significativos en backend o frontend.
---

# Testing Workflow Skill

## Backend (FastAPI + pytest)

> ⚠️ **Siempre ejecutar desde la carpeta `backend/`** con el virtualenv activado.

```powershell
# 1. Ir a la carpeta backend y activar el venv (Windows)
cd backend
.venv\Scripts\Activate.ps1

# 2. Ejecutar todas las pruebas
pytest

# 3. Ejecutar con reporte de cobertura
pytest --cov=app tests/

# 4. Ejecutar un archivo específico
pytest tests/test_approvals.py -v

# 5. Ejecutar con output detallado
pytest -v --tb=short
```

### Arquitectura de tests

- **BD de pruebas**: `sqlite:///./test_innti.db` — creada y destruida por `conftest.py` en cada test.
- **Fixture `db_session`**: sesión limpia por función, scope `function`.
- **Fixture `client`**: `TestClient` de FastAPI con la BD de test inyectada vía `dependency_overrides`.
- **Mocks de sistema**: `conftest.py` mockea `weasyprint` y `mammoth` con `MagicMock` antes de importar la app (necesario porque WeasyPrint requiere librerías del sistema).

### Archivos de test

| Archivo | Qué prueba |
|---------|------------|
| `test_proposals_api.py` | Endpoints CRUD de propuestas |
| `test_proposals_mvp.py` | Flujo completo MVP (crear → generar → aprobar) |
| `test_approvals.py` | Lógica de transiciones de estado |
| `test_portfolio.py` | Carga y lectura de `ListaPortafolio.xlsx` |
| `test_innti.py` | InntiService (con mock de la API) |
| `test_document_gen.py` | Generación de documentos Word |
| `test_proposal_code.py` | Generación de códigos de propuesta |
| `test_users.py` | Endpoints de usuarios |

### Estrategia de mocks para Innti
Usar `unittest.mock.patch` para no llamar a la API real en tests:

```python
from unittest.mock import patch, MagicMock

with patch("app.services.innti_service.InntiService.generate_text") as mock_gen:
    mock_gen.return_value = "Texto generado de prueba"
    # ... tu test aquí
```

## Frontend (React + Vitest)

> Ejecutar desde la carpeta `frontend/`.

```powershell
# Ir a la carpeta frontend
cd frontend

# Ejecutar todas las pruebas (una sola vez)
npm test

# Ejecutar en modo watch (re-ejecuta al guardar)
npm test -- --watch

# Ejecutar con cobertura
npm test -- --coverage
```

### Estándares de tests en Frontend
- **Framework**: Vitest + React Testing Library.
- **Ubicación**: `src/__tests__/` (o junto al componente como `*.test.tsx`).
- **Qué probar**:
  - Renderización correcta de componentes con Tailwind.
  - Manejo de estados de formularios.
  - Llamadas al API (`src/services/api.ts`) mockeadas con `vi.mock`.
- **Sin `any`**: Todos los mocks deben estar correctamente tipados.
