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
| Flujo de aprobación | ✅ | ✅ | ✅ |
| Cómo crear propuesta | — | ✅ | ✅ |
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

