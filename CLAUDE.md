@AGENTS.md

## Comandos rápidos

```powershell
# Backend (FastAPI — puerto 8000)
cd backend
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# Frontend (React + Vite — puerto 5173)
cd frontend
npm run dev

# Tests backend
cd backend && .venv\Scripts\Activate.ps1 && pytest tests/ -v

# Tests frontend
cd frontend && npm test

# Build TypeScript (verificar tipos)
cd frontend && npm run build
```

## Agents disponibles

Los agents están en `.claude/agents/` y se activan automáticamente según el contexto:

| Agent | Cuándo se activa |
|---|---|
| `proposal-workflow` | Ciclo de vida completo de una propuesta |
| `proposal-generation` | Generar propuesta desde cero con Innti |
| `pre-commit-validation` | Antes de hacer commit |

## Skills disponibles (`.opencode/skills/`)

| Skill | Archivo | Contenido |
|---|---|---|
| `innti-domain` | [SKILL.md](.opencode/skills/innti-domain/SKILL.md) | Estados, roles, enums, flujo de aprobación |
| `document-generation` | [SKILL.md](.opencode/skills/document-generation/SKILL.md) | Generación Word / PDF / Anexo Técnico |
| `proposal-workflow-guide` | [SKILL.md](.opencode/skills/proposal-workflow-guide/SKILL.md) | Flujo desde perspectiva del usuario |
| `testing-workflow` | [SKILL.md](.opencode/skills/testing-workflow/SKILL.md) | Cómo ejecutar tests backend y frontend |

## Arquitectura de reglas y sinergia

Ver [.opencode/ARCHITECTURE.md](.opencode/ARCHITECTURE.md) para la jerarquía completa de AGENTS.md → Skills → Agents y las **9 reglas no-obvias del dominio** (estados, transiciones, endpoints).
