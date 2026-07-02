# Método de trabajo: Arquitecto (Claude) + Innti (desarrollador)

Este documento define **cómo trabajamos** las soluciones del proyecto usando dos roles
separados. No describe una funcionalidad; describe el proceso.

## Roles

| Rol | Quién | Responsabilidad |
|-----|-------|-----------------|
| **Arquitecto / cerebro** | Claude | Entiende el problema, decide la solución, el *cómo* y el *porqué*. Produce un `.md` por solución con los prompts ordenados que hay que ejecutar. NO escribe el código final. |
| **Desarrollador / manos** | Innti (vía OpenCode) | Ejecuta los prompts del `.md`, uno a uno, escribiendo el código real en el repo. Mantiene contexto entre prompts. |

Regla mental: **el humano dirige, el arquitecto diseña, Innti ejecuta.** La decisión
técnica siempre nace acá; Innti implementa, no decide arquitectura.

## Flujo de una solución

1. Le pedís a Claude una solución (un feature, un fix, un refactor).
2. Claude genera un archivo `docs/innti/NNN-nombre-solucion.md` con los prompts ordenados.
3. Abrís OpenCode (conectado a Innti) en la raíz del repo.
4. Pegás **el Prompt 1**, esperás que Innti termine, verificás el resultado.
5. Pegás el Prompt 2, y así sucesivamente. Cada prompt construye sobre el anterior.
6. Si algo se desvía, volvés a Claude con lo que pasó y ajusta el `.md`.

## Por qué los prompts son así

- **Innti mantiene contexto entre prompts** → los prompts son **incrementales**
  ("ahora agregá X a lo que ya hiciste"), no repiten todo desde cero.
- **OpenCode le da a Innti acceso a los archivos del repo** → los prompts **referencian
  archivos por ruta** (`backend/app/routers/clients.py`) en vez de pegar su contenido.
- **OpenCode carga `AGENTS.md` y `README.md` como instrucciones** → Innti ya conoce las
  reglas del proyecto. Los prompts **no repiten** convenciones generales; solo lo específico
  de la solución.

## Reglas de oro para los prompts (las aplica Claude al escribir el `.md`)

1. **Un objetivo por prompt.** Si un prompt hace tres cosas, se parte en tres.
2. **Incremental.** Cada prompt asume lo hecho en los anteriores.
3. **Referencia por ruta, no por contenido.** Innti lee los archivos solo.
4. **Verificación al final de cada prompt.** Un comando o check para confirmar que quedó bien
   antes de pasar al siguiente.
5. **Tests obligatorios.** Todo código nuevo (backend o frontend) va con sus pruebas en el
   mismo prompt o en el prompt inmediatamente siguiente. Una solución no está completa sin tests.
6. **No commit sin autorización.** Ningún prompt le pide a Innti commitear o pushear salvo que
   vos lo pidas explícitamente.
7. **Idiomas:** código y comentarios técnicos en inglés; textos de UI, mensajes al cliente y
   contenido de propuestas en español (regla del proyecto).

## Relación con SDD

`AGENTS.md` exige **SDD (Spec-Driven Development)** para todo desarrollo, con artifact store
`openspec` (basado en archivos, sin Engram). Por eso cada solución se clasifica en un **track**:

- **Track SDD (completo)** — features y cambios con lógica nueva. Los prompts recorren las fases:
  `/sdd-explore` → `/sdd-propose` → `/sdd-spec` → `/sdd-design` → `/sdd-tasks` → `/sdd-apply` →
  `/sdd-verify` → `/sdd-archive`.
- **Track directo** — solo excepciones permitidas por `AGENTS.md`: typos, docs menores, config
  sin lógica, o bug crítico en producción. Va directo a los prompts de fix + verificación.

Claude indica el track al inicio de cada `.md` y justifica por qué.

## Convenciones de archivos

- Carpeta: `docs/innti/`
- Nombre: `NNN-nombre-en-kebab-case.md` (ej. `001-relacionar-esquemas.md`).
  `NNN` es un correlativo de tres dígitos que da orden cronológico.
- Plantilla base: [`_PLANTILLA.md`](_PLANTILLA.md). Claude la copia y completa por cada solución.

## Índice de soluciones

| # | Solución | Track | Estado |
|---|----------|-------|--------|
| [001](001-relacionar-esquemas.md) | Relacionar esquemas por producto (regla QloudSI + documento unificado/separado) | SDD completo | Implementada — pendiente commit |
