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

13. **Relación Producto → Esquemas (desde junio 2026):** Los esquemas disponibles en el paso 2 dependen de los productos seleccionados en el paso 1. La fuente de datos es la columna 9 del Excel ("Esquemas Permitidos"), separada por comas. `PortfolioService.get_allowed_schemes_for_products()` computa la **INTERSECCIÓN**: solo se muestran esquemas válidos para TODOS los productos seleccionados. Un producto sin restricción aporta todos los MVP schemes (no estrecha el conjunto). Si la intersección es vacía, `SchemeSelector` muestra un aviso y el usuario no puede avanzar. El backend valida en `POST /api/proposals/` con HTTP 422 si hay incompatibilidad. Ver `_validate_scheme_product_compatibility` en `proposals.py`.

14. **Mock de portfolio en tests:** El fixture `client` en `conftest.py` ya inyecta un portfolio mock permisivo (todos los MVP schemes) para que los tests existentes no fallen. Tests que necesiten restricciones específicas deben sobreescribir `get_portfolio_service` con su propio fixture (patrón igual que `portfolio_mock` en `test_portfolio_api.py`).

1. **`REVIEWED` NO puede rechazarse.** Solo `PENDING_REVIEW` y `PENDING_VP` pueden ir a `REJECTED`.
2. **`submit-review` maneja 4 transiciones** según el estado actual: `DRAFT→PENDING_REVIEW`, `REVIEWED→PENDING_VP`, `APPROVED→SENT_TO_CLIENT`, `REJECTED→DRAFT`. El endpoint detecta el estado automáticamente.
3. **Los endpoints de documentos son POST, no GET**, y usan prefijo `/api/proposals/`, no `/documents/`.
4. **Concesión/BPO y Suministro son Fase 2** — están definidos en el enum pero no deben usarse en el MVP.
5. **Los documentos se guardan en `/tmp/innti_docs/`** (FileResponse), no se sirven desde memoria (StreamingResponse).
6. **No hay Alembic** — el esquema de BD se recrea con `Base.metadata.create_all` al iniciar.
7. **`action` es campo requerido** en los bodies de `/approve` y `/reject`: `"action": "approved"` o `"action": "rejected"`. No tiene valor por defecto en el schema Pydantic.
8. **ProposalEditor tiene 8 pestañas + sub-tabs por esquema**: 2 globales (Contexto, Carta de Presentación) y 6 por esquema (Alcance, Plazo, Condiciones Económicas, Forma de Pago, Servicios Excluidos, Propiedad Intelectual). Cuando hay ≥ 2 esquemas, las pestañas por esquema muestran un selector adicional para alternar entre el contenido de cada esquema. El botón Guardar persiste tanto cambios globales (vía `PATCH /api/proposals/{id}`) como cambios por esquema (vía `PATCH /api/proposals/{id}/schemes/{scheme_id}`).
9. **`key={proposal.updated_at}` en ProposalEditor**: fuerza re-mount del componente TipTap cuando Innti regenera el contenido, evitando contenido obsoleto en el editor sin recargar la página.
10. **Contenido por esquema vs global**: el contenido textual de una propuesta se divide entre `Proposal` (globales: carta, contexto, confidencialidad) y `ProposalScheme` (por esquema: alcance, plazo, condiciones, pago, exclusiones, IP). El servicio `proposal_content_resolver.py` centraliza la resolución con defaults inteligentes (SaaS sin exclusiones, IP por tipo de esquema).
11. **`combine_schemes=False` requiere ≥ 2 esquemas**: el validator de `ProposalCreate` rechaza con 422 si se intenta crear con un solo esquema. No tiene sentido pedir "Documentos separados" con un único esquema.
12. **El conversor HTML→docx preserva marcas**: `_add_html_paragraphs` en `document_generator.py` ya **no** convierte el HTML de TipTap a texto plano. Usa el parser stateful `_HtmlToDocxParser` (basado en `html.parser.HTMLParser` de la stdlib) que mapea cada marca/tag a runs de python-docx: `<strong>/<b>`, `<em>/<i>`, `<u>`, `<s>/<del>`, `<sup>`, `<sub>`, `<mark>`, `<span style="color">`, `<a href>`, `<blockquote>`, `<hr>`, `<h1>`–`<h6>`, `<ul>/<ol>/<li>`, y `text-align` en `<p>`. La función legacy `_strip_html` se mantiene **solo** para `_has_content` (detectar si hay contenido real, no para serializar). Cualquier extensión nueva del editor TipTap también debe ampliar este parser para que llegue al .docx.

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
| Relación Producto → Esquemas | ✅ | ✅ | — |
| Filtros y búsqueda en lista | ✅ | — | — |

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

