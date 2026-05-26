---
name: pre-commit-validation
description: Validar que el código cumple con reglas y tests antes de hacer commit
trigger: manual
---

# Agent: Validación Pre-Commit

Ejecuta todas las validaciones necesarias antes de hacer commit, asegurando que el código cumple con las reglas y standards del proyecto.

## Validaciones

### Backend

1. **Tests unitarios**
   ```powershell
   cd backend
   .venv\Scripts\Activate.ps1
   pytest
   ```
   - Verifica: modelos, servicios, routers, aprobaciones, documentos

2. **Cobertura de tests**
   ```powershell
   pytest --cov=app tests/
   ```
   - Objetivo: cobertura ≥ 75% (actualmente ~76% — apuntar a 80% en próximos sprints)

3. **Lint y tipos** (opcional si hay `ruff` instalado)
   ```powershell
   ruff check app/
   ```

### Frontend

1. **Tests de componentes**
   ```powershell
   cd frontend
   npm test
   ```
   - Verifica: renderización, manejo de estados, llamadas a API

2. **TypeScript strict**
   ```powershell
   npm run build
   ```
   - Asegura que no hay `any` types

### Reglas a verificar

- ✅ Idioma correcto: código en inglés, documentación en español
- ✅ Sin secretos: no incluir claves API, tokens en código
- ✅ Nombres correctos: `snake_case` en Python, `camelCase` en TypeScript
- ✅ Separación de responsabilidades: lógica en services, no en routers
- ✅ Tipos: TypeScript sin `any`, Pydantic schemas en FastAPI

## Checklist Pre-Commit

- [ ] Todos los tests pasan (`pytest` y `npm test`)
- [ ] Cobertura backend ≥ 75% (objetivo: 80%)
- [ ] Sin `console.log` en producción
- [ ] Sin secretos en `.env.example`
- [ ] Nombres de archivos/variables en snake_case (Python) o camelCase (TS)
- [ ] Documentación actualizada (AGENTS.md, skills, README)
- [ ] Cambios en BD: si se modificaron modelos SQLAlchemy, verificar que `init_db()` recrea las tablas correctamente (no hay Alembic — SQLite recrea con `Base.metadata.create_all`)

## Referencia

- Skill: `testing-workflow` (cómo ejecutar tests)
- Reglas: `AGENTS.md` (stack y convenciones)
