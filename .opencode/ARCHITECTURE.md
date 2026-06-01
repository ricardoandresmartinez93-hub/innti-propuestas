# Arquitectura de Reglas, Skills y Agents

Documento que describe la sinergia y armonía entre todos los componentes de gobernanza del proyecto.

---

## 📋 Jerarquía de Componentes

```
AGENTS.md (Constitución)
├─ Define: Stack, reglas, convenciones, flujos técnicos
├─ Scope: Enfoque técnico y arquitectónico
└─ Público: Todos los desarrolladores

SKILLS (Manuales Específicos)
├─ innti-domain: Contexto de negocio
├─ testing-workflow: Cómo ejecutar tests
├─ document-generation: Cómo generar documentos
└─ proposal-workflow-guide: Flujo de usuario

AGENTS (Orquestadores)
├─ proposal-workflow: Automatizar flujo propuesta
├─ pre-commit-validation: Validar antes de commit
└─ proposal-generation: Generar desde datos
```

---

## 🔄 Armonía y Sinergia

### AGENTS.md → Fuente de Verdad

AGENTS.md es la **"constitución" del proyecto**. Define:
- ✅ Enums exactos: `ProposalStatus`, `SchemeType`, `ApprovalRole`
- ✅ Stack tecnológico (FastAPI, React, SQLite, Innti)
- ✅ Convenciones de naming (snake_case Python, camelCase TS)
- ✅ Arquitectura (separación modelos/schemas, lógica en services)
- ✅ Flujo de aprobación y roles

### Skills → Amplificadores de AGENTS.md

Cada skill **amplifica un aspecto de AGENTS.md sin contradecirlo**:

| Skill | Amplifica | Propósito |
|-------|-----------|----------|
| **innti-domain** | Esquemas de pago, flujo de estados, roles | Entender el contexto de negocio |
| **testing-workflow** | Convención de testing, stack (pytest, vitest) | Saber cómo ejecutar tests |
| **document-generation** | Stack de documentos (python-docx, WeasyPrint) | Generar Word y PDF |
| **proposal-workflow-guide** | Flujo de usuario, estados, UI | Crear propuestas en la UI |

**Sinergia:** Los skills no duplican AGENTS.md, lo explican desde ángulos diferentes:
- AGENTS.md: "Usar `ProposalStatus.DRAFT`, `PENDING_REVIEW`, ..."
- innti-domain: "El flujo es DRAFT → PENDING_REVIEW → ... porque Ángela revisa primero"
- proposal-workflow-guide: "Haz click en 'Nueva propuesta' → selecciona cliente → crea"

### Agents → Ejecutores de los Skills

Cada agent **orquesta workflows usando los skills como referencia**:

| Agent | Usa Skills | Usa Servicios |
|-------|-----------|---------------|
| **proposal-workflow** | innti-domain, document-generation, proposal-workflow-guide | InntiService, DocumentGenerator, ApprovalService |
| **pre-commit-validation** | testing-workflow | pytest, npm test |
| **proposal-generation** | innti-domain, document-generation | InntiService, PortfolioService, DocumentGenerator |

---

## ❌ Sin Duplicados Críticos

Comparación de componentes:

### AGENTS.md vs innti-domain/SKILL.md
- ✅ AGENTS.md: Define enums y valores exactos (`"draft"`, `"pending_review"`, ...)
- ✅ innti-domain: Explica el contexto y por qué existen esos estados
- ➜ **Complementarios, no duplicados**

### testing-workflow/SKILL.md vs pre-commit-validation/AGENT.md
- ✅ testing-workflow: "Cómo ejecutar `pytest`"
- ✅ pre-commit-validation: "Qué validar antes de commit (usa pytest)"
- ➜ **Complementarios**: uno es "cómo", otro es "qué"

### proposal-workflow/AGENT.md vs proposal-workflow-guide/SKILL.md
- ✅ proposal-workflow (agent): Orquesta endpoints API automáticamente
- ✅ proposal-workflow-guide (skill): Explica paso a paso qué hace el usuario
- ➜ **Complementarios**: uno automatiza, otro educa

---

## ⚠️ Reglas No Obvias del Dominio

Estas son las cosas que son fáciles de equivocar si no se leyó el código real:

1. **`REVIEWED` NO puede rechazarse.** Solo `PENDING_REVIEW` y `PENDING_VP` pueden ir a `REJECTED`.
2. **`submit-review` maneja 4 transiciones** según el estado actual: `DRAFT→PENDING_REVIEW`, `REVIEWED→PENDING_VP`, `APPROVED→SENT_TO_CLIENT`, `REJECTED→DRAFT`. El endpoint detecta el estado automáticamente.
3. **Los endpoints de documentos son POST, no GET**, y usan prefijo `/api/proposals/`, no `/documents/`.
4. **Concesión/BPO y Suministro son Fase 2** — están definidos en el enum pero no deben usarse en el MVP.
5. **Los documentos se guardan en `/tmp/innti_docs/`** (FileResponse), no se sirven desde memoria (StreamingResponse).
6. **No hay Alembic** — el esquema de BD se recrea con `Base.metadata.create_all` al iniciar.
7. **`action` es campo requerido** en los bodies de `/approve` y `/reject`: `"action": "approved"` o `"action": "rejected"`. No tiene valor por defecto en el schema Pydantic.
8. **ProposalEditor tiene 8 pestañas**: 5 editables siempre (contexto, alcance, plazo, condiciones económicas, forma de pago), 2 auto-completadas con texto fijo editable (servicios excluidos, propiedad intelectual), 1 solo lectura (carta de presentación). El botón Guardar funciona desde cualquier pestaña.
9. **`key={proposal.updated_at}` en ProposalEditor**: fuerza re-mount del componente TipTap cuando Innti regenera el contenido, evitando contenido obsoleto en el editor sin recargar la página.

---

## ✨ Puntos Fuertes de la Arquitectura

1. **Claridad**: Cada componente tiene un propósito único y bien definido
2. **Escalabilidad**: Fácil agregar nuevos skills/agents sin romper existentes
3. **Referencia cruzada**: Skills y agents referencian AGENTS.md como "fuente de verdad"
4. **Cobertura completa**:
   - 📖 AGENTS.md: Qué se hace (reglas)
   - 💡 Skills: Cómo se hace (procedimientos)
   - 🤖 Agents: Automatizar lo que se hace (orquestación)

---

## 📝 Matriz de Cobertura

| Aspecto | AGENTS.md | Skills | Agents |
|--------|-----------|--------|--------|
| Stack y arquitectura | ✅ | — | — |
| Flujo de aprobación (7 estados) | ✅ | ✅ | ✅ |
| `submit-review` multi-transición | ✅ | ✅ | ✅ |
| Cómo crear propuesta | — | ✅ | ✅ |
| Editor TipTap (8 tabs, readOnly) | — | ✅ | — |
| Testing | — | ✅ | ✅ |
| Generación de documentos | — | ✅ | ✅ |
| Validación pre-commit | — | — | ✅ |
| Automatización completa | — | — | ✅ |

---

## 🎯 Cómo Usar Esta Arquitectura

### Nuevo developer:
1. Lee `AGENTS.md` (reglas globales)
2. Lee el skill relevante (ej: `proposal-workflow-guide` si trabaja en UI)
3. Usa agents para automatizar flujos (ej: `proposal-generation` para tests)

### Código en production:
1. Verificar contra reglas en `AGENTS.md`
2. Si hay duda, revisar el skill relevante
3. Antes de commit, usar `pre-commit-validation` agent

### Cambios arquitectónicos:
1. Actualizar `AGENTS.md` (fuente de verdad)
2. Actualizar skills afectados
3. Actualizar agents si cambia el flujo

### ✅ Checklist de documentación — obligatorio tras cada cambio de código

Después de crear o modificar **cualquier archivo**, verificar cuáles de estos documentos deben actualizarse:

| Archivo | Actualizar cuando… |
|---------|-------------------|
| `AGENTS.md` | Cambia stack, reglas de desarrollo, convenciones o flujos técnicos |
| `.opencode/agents/*.md` | Cambia el comportamiento, prompts o herramientas de un agente |
| `.opencode/skills/document-generation/SKILL.md` | Cambia `DocumentGenerator`: secciones del doc, constantes, endpoints o flujo de generación |
| `.opencode/skills/innti-domain/SKILL.md` | Cambia esquemas, estados, roles, o métodos de `InntiService` |
| `.opencode/skills/proposal-workflow-guide/SKILL.md` | Cambia la UI: pestañas del editor, pasos del flujo, botones o campos visibles al usuario |
| `.opencode/skills/testing-workflow/SKILL.md` | Cambia cómo se ejecutan o estructuran los tests |
| `.opencode/ARCHITECTURE.md` | Cambia la arquitectura global, reglas no-obvias (#1–#9) o la matriz de cobertura |

---

## 📌 Referencias Internas

| Archivo | Propósito |
|---------|----------|
| `AGENTS.md` | Reglas y convenciones globales |
| `.opencode/skills/innti-domain/SKILL.md` | Contexto de negocio |
| `.opencode/skills/testing-workflow/SKILL.md` | Ejecución de tests |
| `.opencode/skills/document-generation/SKILL.md` | Generación de Word/PDF |
| `.opencode/skills/proposal-workflow-guide/SKILL.md` | Flujo de usuario |
| `.opencode/agents/proposal-workflow.md` | Orquestación de propuesta |
| `.opencode/agents/pre-commit-validation.md` | Validación pre-commit |
| `.opencode/agents/proposal-generation.md` | Generación automática |

