# NNN — <Título de la solución>

> Plantilla base. Claude la copia a `NNN-nombre.md` y la completa. Ver el método en
> [`README.md`](README.md).

## Contexto y decisión de arquitectura

- **Problema:** <qué se quiere resolver, en una o dos frases>
- **Solución elegida:** <el enfoque, en criollo>
- **Por qué esta y no otra:** <la decisión de arquitectura + el descarte de la alternativa>
- **Track:** `SDD completo` | `directo` — <justificación>
- **Archivos que se van a tocar:** <rutas previstas, aproximado>
- **Pre-requisitos:** <backend levantado, seed corrido, rama creada, etc. — o "ninguno">

## Rama

```bash
git checkout -b feature/<nombre>
```

## Prompts para Innti

> Pegá un prompt por vez en OpenCode. Esperá a que Innti termine y hacé la verificación
> antes de pasar al siguiente.

### Prompt 1 — <objetivo corto>

**Qué hace este prompt:** <explicación clara para vos: qué le pedís a Innti y qué debería lograr>

**Prompt para Innti:**

```text
<texto exacto a pegar en OpenCode>
```

**Resultado esperado:** <qué archivos/cambios deberían aparecer>

**Verificación:**

```bash
<comando o check — ej. cd backend && pytest tests/test_xxx.py>
```

---

### Prompt 2 — <objetivo corto>

**Qué hace este prompt:** <...>

**Prompt para Innti:**

```text
<...>
```

**Resultado esperado:** <...>

**Verificación:**

```bash
<...>
```

---

<!-- Repetir bloque de prompt según haga falta -->

## Cierre

- [ ] Todos los prompts ejecutados y verificados
- [ ] Tests en verde (`pytest` / `npm test`)
- [ ] Documentación actualizada si el cambio lo amerita (`AGENTS.md`, `.opencode/*`, `README.md`)
- [ ] **Commit/push:** pendiente de autorización explícita del usuario
