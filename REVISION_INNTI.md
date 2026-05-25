# Revisión técnica del trabajo de Innti — Proyecto Innti Propuestas

**Fecha de revisión:** 24 de mayo de 2026
**Revisor:** Claude (Cowork)
**Alcance:** Revisión profunda, commit por commit, de los 14 prompts de `prompts_innti.md`.
**Modo:** Reportar y corregir.

---

## 1. Resumen ejecutivo

Cada prompt del archivo `prompts_innti.md` se ejecutó en un commit independiente. Se
revisó el diff de cada commit contra los requisitos, restricciones técnicas y
objetivo declarado del prompt correspondiente, y la consistencia con el resto del
código base.

**Resultado global:** de los 14 prompts, **5 quedaron correctos**, **1 quedó parcial**
y **8 presentan defectos** — incluyendo 6 de severidad alta (uno de ellos rompe la
compilación del frontend y otro hace fallar un test). Innti produjo código que, en
general, *parece* correcto y sigue la estructura pedida, pero falla en la
**integración entre piezas** (rutas, endpoints, contratos) y en algunos detalles
de cómo funcionan realmente las librerías (TipTap, Docker, jest-dom).

Todos los defectos de severidad alta/media fueron **corregidos**. Los puntos
menores se reportan con recomendación; algunos se corrigieron y otros se dejaron
documentados para decisión del equipo (ver sección 5).

### Tabla de veredictos por prompt

| Prompt | Tema | Veredicto | Hallazgo principal |
|--------|------|-----------|--------------------|
| 1.1 | CRUD de Clientes | ✅ Correcto | — |
| 1.2 | Productos en propuesta | ✅ Correcto | — |
| 2.1 | PDF desde Word | ⚠️ Incompleto | El método se creó pero nunca se expuso como endpoint (ver H3) |
| 2.2 | Plantilla Word Quipux | ✅ Correcto | Detalles cosméticos menores |
| 3.1 | Formulario de Cliente | ✅ Correcto | Detalles menores |
| 3.2 | Selector de esquemas | ✅ Correcto | Detalles menores |
| 3.3 | Editor TipTap | ❌ Bug grave | H1 — el editor corrompe el contenido entre pestañas |
| 4.1 | Wizard de creación | ❌ Bug | H2 — redirige a una ruta inexistente |
| 4.2 | Página de detalle | ❌ Bug | H3 — "Generar PDF" no genera un PDF |
| 5.1 | Tests de integración API | ❌ Bug | H4 — bloque duplicado hace fallar un test |
| 5.2 | Tests de componentes React | ❌ Bug | H6 — rompe `npm run build` (tsc) |
| 6.1 | Documentación de la API | ❌ Inexacto | M1 — múltiples errores factuales |
| 7.1 | Manejo de errores central | ⚠️ Parcial | M2 — la centralización no es efectiva |
| 8.1 | Dockerfile / compose | ❌ Bug | H5 — la BD SQLite hace crashear el contenedor |

---

## 2. Hallazgos de severidad ALTA

### H1 — El editor de propuestas corrompe el contenido al cambiar de pestaña (Prompt 3.3)

**Archivo:** `frontend/src/components/ProposalEditor.tsx`

El componente tiene 4 pestañas (Contexto, Alcance, Condiciones Económicas, Forma de
Pago) que comparten **una sola instancia** del editor TipTap. El callback `onUpdate`
escribe lo que el usuario teclea en `contents[activeTab]`:

```js
onUpdate: ({ editor }) => {
  setContents((prev) => ({ ...prev, [activeTab]: html }))
}
```

El problema: en `@tiptap/react`, `onUpdate` se registra **una sola vez** al crear el
editor (verificado en el código de `@tiptap/core`: el constructor hace
`this.on('update', this.options.onUpdate)` y `setOptions` nunca vuelve a registrar
el listener). Por lo tanto el closure de `onUpdate` captura para siempre el valor
**inicial** de `activeTab` (`context_content`).

**Consecuencia:** sin importar en qué pestaña esté el usuario, todo lo que escriba
se guarda en `context_content`. Al editar "Alcance" se sobrescribe "Contexto", y los
campos "Alcance", "Condiciones Económicas" y "Forma de Pago" **nunca se guardan**.
Es una corrupción de datos silenciosa que rompe la función central del componente
(y también afecta a la página de detalle, que lo usa).

**Corrección aplicada:** se introdujo una `ref` (`activeTabRef`) sincronizada con
`activeTab`, de modo que `onUpdate` siempre lee la pestaña activa actual.

---

### H2 — El wizard redirige a una ruta inexistente (Prompt 4.1)

**Archivo:** `frontend/src/pages/NewProposalPage.tsx`

Al crear la propuesta, el wizard hacía:

```js
navigate(`/editor/${res.data.id}`)
```

Pero en `App.tsx` **no existe** ninguna ruta `/editor/:id`. La ruta de la página de
detalle/edición es `/proposals/:id`. Tras crear una propuesta el usuario aterrizaba
en una pantalla en blanco (ruta sin coincidencia).

**Corrección aplicada:** `navigate(`/proposals/${res.data.id}`)`.

---

### H3 — El botón "Generar PDF" no genera un PDF (Prompts 4.2 y 2.1)

**Archivos:** `frontend/src/pages/ProposalDetailPage.tsx`, `backend/app/routers/documents.py`,
`frontend/src/services/api.ts`

La página de detalle ofrece un botón "Generar PDF", pero el handler hacía:

```js
// para 'word' Y 'pdf' llamaba al MISMO endpoint
response = await proposalApi.generateDocument(proposal.id, true)
```

`generateDocument` llama a `/generate-document`, que devuelve un archivo **`.docx`**.
El frontend envolvía esos bytes de Word en un `Blob` con tipo `application/pdf`. El
resultado es un PDF corrupto que el navegador no puede abrir.

Causa de fondo: **no existe ningún endpoint de PDF en el backend**. El método
`convert_docx_to_pdf` creado en el Prompt 2.1 quedó como código muerto — nunca se
conectó a un endpoint ni a la capa de API. Es decir, los Prompts 2.1 y 4.2 nunca se
integraron entre sí.

**Corrección aplicada:**
1. Backend: nuevo endpoint `POST /api/proposals/{id}/generate-pdf` que construye el
   Word y lo convierte a PDF con `convert_docx_to_pdf`. Se extrajo además un helper
   `_build_proposal_docx` para no duplicar la lógica de generación.
2. API frontend: nuevo método `proposalApi.generatePdf`.
3. `ProposalDetailPage`: el botón PDF ahora llama a `generatePdf`.

---

### H4 — Bloque duplicado hace fallar `test_full_approval_flow` (Prompt 5.1)

**Archivo:** `backend/tests/test_proposals_api.py`

El test `test_full_approval_flow` tenía las **últimas 5 líneas duplicadas**: tras
aprobar como VP (la propuesta queda en `approved`), volvía a llamar al endpoint
`/approve` con rol `vp`. Esa segunda llamada intenta la transición `approved →
approved`, que no es válida → el servicio lanza `InvalidTransitionError` → el router
responde **409**. La aserción `assert ... == 200` falla.

Es un error de copiar/pegar: el test que el prompt pedía explícitamente **no pasa**.

**Corrección aplicada:** se eliminó el bloque duplicado. Verificado: los 6 tests del
archivo pasan (`6 passed`).

---

### H5 — La base de datos SQLite hace crashear el contenedor (Prompt 8.1)

**Archivo:** `docker-compose.yml`

El compose montaba la BD así:

```yaml
volumes:
  - ./backend/innti_propuestas.db:/app/innti_propuestas.db
```

Montar como *bind mount* un archivo que **no existe** en el host es un error clásico
de Docker: Docker crea una **carpeta** vacía en su lugar. Al arrancar, SQLite intenta
abrir `/app/innti_propuestas.db` (que ahora es un directorio) y falla con
`unable to open database file` → el backend crashea en el primer arranque.

Además, el compose declaraba un volumen con nombre `sqlite_data:` que **nunca se
usaba** (declaración huérfana).

**Corrección aplicada:** se reescribió la sección de la BD para usar el volumen con
nombre `sqlite_data` montado en `/app/data`, y se fija `DATABASE_URL` por variable
de entorno apuntando a `sqlite:////app/data/innti_propuestas.db`. Así la BD persiste,
el volumen declarado se usa de verdad, y se evita el problema del archivo/carpeta.
También se eliminó la clave `version` (obsoleta en Docker Compose v2).

> Nota: el servicio sigue dependiendo de `./backend/.env`. Es necesario crear ese
> archivo a partir de `.env.example` antes de `docker compose up`.

---

### H6 — El archivo de test de React rompe `npm run build` (Prompt 5.2)

**Archivo:** `frontend/src/__tests__/ProposalListPage.test.tsx`

El test registra los matchers de jest-dom en tiempo de ejecución:

```js
import * as matchers from '@testing-library/jest-dom/matchers'
expect.extend(matchers)
```

Esto funciona al **ejecutar** los tests, pero **no informa a TypeScript** de que
`expect(...)` ahora tiene `.toBeInTheDocument()` o `.toHaveClass()`. Como
`tsconfig.json` incluye toda la carpeta `src`, el comando de build
(`build: "tsc && vite build"`) ejecuta `tsc`, que falla con 11 errores
`TS2339: Property 'toBeInTheDocument' does not exist...`.

Es decir: **el commit 5.2 dejó el proyecto sin poder compilar.**

**Corrección aplicada:** se reemplazó por el import canónico para Vitest, que además
aumenta los tipos del `Assertion` de Vitest:

```js
import '@testing-library/jest-dom/vitest'
```

Verificado: `tsc --noEmit` ahora termina sin errores en todo `src`.

---

## 3. Hallazgos de severidad MEDIA

### M1 — La documentación de la API tiene errores factuales (Prompt 6.1)

**Archivo:** `docs/API.md`

El documento generado contenía varios errores que llevarían a un desarrollador a
recibir errores 422:

- **Cuerpo de "Crear Propuesta" incorrecto:** documentaba `products` y `schemes`
  como listas de cadenas (`["Qx-Tránsito"]`). El esquema real exige listas de
  **objetos** (`ProposalProductCreate` / `ProposalSchemeCreate`).
- **Campos inventados en el PATCH:** documentaba `scope_description` y
  `commercial_conditions`, que no existen. Los campos reales son `scope_content`,
  `economic_conditions`, `payment_terms`, etc.
- **Falta el campo `action`** (obligatorio) en el cuerpo de "Aprobar".
- **Endpoints faltantes:** no documentaba `GET`/`DELETE` de propuestas, los endpoints
  de productos de propuesta, el historial de aprobaciones, ni **todo el recurso de
  Clientes**.
- Documentaba un código `403` que la API nunca devuelve.

**Corrección aplicada:** se reescribió `docs/API.md` por completo con los esquemas,
endpoints, enums y códigos de error reales (incluyendo el nuevo `/generate-pdf`).

### M2 — La centralización de errores no es efectiva (Prompt 7.1)

**Archivo:** `backend/app/middleware/error_handler.py`

El middleware se creó y registró correctamente, y los requisitos *literales* del
prompt se cumplen. Sin embargo, el **objetivo** ("manejo centralizado para
consistencia") no se logra:

- Los routers **siguen capturando** las excepciones localmente. Por ejemplo,
  `approvals.py` hace `try/except ApprovalError` y las convierte en `HTTPException`
  antes de que lleguen al handler. Por lo tanto `approval_error_handler` (y en buena
  medida `innti_service_error_handler` y `portfolio_not_found_handler`) son **código
  muerto** en la práctica.
- No se registró un handler para `HTTPException`, así que la gran mayoría de las
  respuestas de error siguen con el formato antiguo `{"detail": ...}` en lugar del
  formato estándar `{"error", "detail", "status_code"}`.

**Estado:** reportado, **no modificado**. Unificar de verdad implicaría refactorizar
todos los routers (quitar sus `try/except`) y normalizar `HTTPException`, lo que
cambia el contrato de respuesta de toda la API y los tests existentes. Es una
decisión de diseño que conviene que tome el equipo, no una corrección puntual.

---

## 4. Revisión prompt por prompt

**Prompt 1.1 — CRUD de Clientes** ✅
Cumple todos los endpoints, el prefijo/tags, los códigos 404/204 y la inyección de
`get_db`. Router registrado en `main.py`. Sin observaciones funcionales. (Nota
menor: el commit arrastró un `frontend/package-lock.json` de 5.400 líneas y un
`backend/package-lock.json` ajenos al cambio.)

**Prompt 1.2 — Productos en propuesta** ✅
Los tres endpoints (POST/DELETE/PUT) verifican existencia (404) y estado `DRAFT`
(400), y usan los esquemas correctos. El PUT reemplaza correctamente. Sin
observaciones.

**Prompt 2.1 — PDF desde Word** ⚠️
El método `convert_docx_to_pdf` está bien implementado (mammoth → HTML → WeasyPrint,
maneja archivo inexistente) y `mammoth` se añadió a `requirements.txt`. Pero quedó
**sin exponer**: ningún endpoint lo usaba. Resuelto en H3.

**Prompt 2.2 — Plantilla Word Quipux** ✅
Cumple márgenes, estilos de Heading 1/2 con los colores pedidos, portada, placeholder
de tabla de contenido, numeración de página en el pie y párrafos justificados con
interlineado 1.15. Detalle menor: importa `WD_LINE_SPACING` e `Inches` sin usarlos.

**Prompt 3.1 — Formulario de Cliente** ✅
Campos, validación de obligatorios, estado de carga y manejo de errores correctos.
Detalles menores: usa `import { Client }` (valor) en vez de `import type` —
inconsistente con el resto del proyecto, aunque no rompe el build; y `err: any`.

**Prompt 3.2 — Selector de esquemas** ✅
Los 5 esquemas con checkbox y descripción, el toggle combinar/separar al elegir 2+ y
el selector de frecuencia por esquema funcionan. Detalles menores: el `useEffect` no
incluye `onSchemesChanged` en sus dependencias; los valores de frecuencia
(`Único/Mensual/Anual`) no coinciden con la convención del backend (`unico/mensual/
anual`) — sin impacto porque la columna es texto libre.

**Prompt 3.3 — Editor TipTap** ❌
Ver **H1** (bug grave). Adicional: clase Tailwind inválida `font-white` (corregida a
`font-medium`); y se usan clases `prose`/`prose-*` aunque el plugin
`@tailwindcss/typography` no está instalado, por lo que no tienen efecto.

**Prompt 4.1 — Wizard de creación** ❌
Ver **H2**. El resto del wizard (4 pasos, validación por paso, stepper) está correcto.

**Prompt 4.2 — Página de detalle** ❌
Ver **H3**. El resto (cabecera con estado, editor, "Enviar a Revisión" solo en
`draft`, apertura por blob URL) está correcto.

**Prompt 5.1 — Tests de integración API** ❌
Ver **H4**. Observaciones adicionales: el prompt pedía usar la fixture `db_session`
para verificar el estado de la BD; Innti lo verificó vía HTTP. Además, dentro de
este commit de *tests* se modificó código de producción (`approvals.py`) para
soportar la transición `reviewed → pending_vp`, fijando el estado directamente y
saltándose la validación `can_transition` del servicio. El mock de
`weasyprint`/`mammoth` en `conftest.py` sí fue un acierto práctico.

**Prompt 5.2 — Tests de componentes React** ❌
Ver **H6**. La lógica de los tres tests es correcta. Nota: el prompt pedía "mockear
axios"; Innti mockeó el módulo de servicio `api` (más limpio, pero es una desviación).

**Prompt 6.1 — Documentación de la API** ❌
Ver **M1**.

**Prompt 7.1 — Manejo de errores centralizado** ⚠️
Ver **M2**. Detalle: el prompt mencionaba el decorador `@app.exception_handler()`;
Innti usó `app.add_exception_handler()`, que es equivalente y correcto. Faltaba el
`__init__.py` en `app/middleware/` (funcionaba como *namespace package*, pero es
inconsistente con el resto de paquetes) — **corregido**.

**Prompt 8.1 — Dockerfile / docker-compose** ❌
Ver **H5**. El resto está bien: imágenes base correctas, build multi-etapa del
frontend, nginx con proxy `/api`, `.dockerignore` del backend adecuado.

---

## 5. Resumen de correcciones aplicadas

| # | Archivo | Corrección |
|---|---------|-----------|
| H1 | `frontend/src/components/ProposalEditor.tsx` | `ref` para que `onUpdate` use la pestaña activa actual |
| H2 | `frontend/src/pages/NewProposalPage.tsx` | Redirección a `/proposals/:id` |
| H3 | `backend/app/routers/documents.py` | Nuevo endpoint `generate-pdf` + helper `_build_proposal_docx` |
| H3 | `frontend/src/services/api.ts` | Nuevo método `proposalApi.generatePdf` |
| H3 | `frontend/src/pages/ProposalDetailPage.tsx` | El botón PDF llama a `generatePdf` |
| H4 | `backend/tests/test_proposals_api.py` | Eliminado el bloque duplicado |
| H5 | `docker-compose.yml` | Volumen con nombre para la BD + `DATABASE_URL` |
| H6 | `frontend/src/__tests__/ProposalListPage.test.tsx` | Import `@testing-library/jest-dom/vitest` |
| M1 | `docs/API.md` | Reescritura completa con esquemas y endpoints reales |
| L1 | `frontend/src/components/ProposalEditor.tsx` | `font-white` → `font-medium` |
| L3 | `backend/app/middleware/__init__.py` | Archivo creado |

**No corregido (reportado para decisión del equipo):**

- **M2** — unificar de verdad el manejo de errores (refactor de routers).
- **L2** — instalar `@tailwindcss/typography` o quitar las clases `prose` del editor.
- **L4** — homogeneizar `import type` en los componentes nuevos.
- **L5** — unificar el casing de las frecuencias de pago entre frontend y backend.
- **L7** — el proyecto define un script `npm run lint` pero **no tiene archivo de
  configuración de ESLint**, por lo que `lint` falla. Es heredado del scaffold
  inicial, no de los prompts de Innti, pero conviene resolverlo.

> Nota: el árbol de trabajo tenía cambios sin commitear en `requirements.txt` y
> `prompts_innti.md` que son **solo cambios de fin de línea** (CRLF), sin efecto
> funcional.

---

## 6. Verificación realizada

- **Backend:** suite completa de pytest — **30 tests pasan** (`30 passed`),
  incluyendo `test_proposals_api.py` (6/6) tras la corrección H4.
- **Frontend:** `tsc --noEmit` sobre todo `src` — **0 errores** tras las
  correcciones (antes fallaba por H6).
- **Sintaxis Python:** `documents.py`, `test_proposals_api.py`, `error_handler.py`
  y `middleware/__init__.py` compilan sin errores.
- **`docker-compose.yml`:** YAML válido; el volumen `sqlite_data` queda declarado y
  utilizado.
- **Limitación:** no fue posible ejecutar `vitest` en el entorno de revisión porque
  `node_modules` está instalado con binarios nativos para Windows (rollup) y la
  verificación corre en Linux. Los tests de React se revisaron de forma estática y
  ahora compilan con `tsc`.

---

## 7. Conclusión

El trabajo de Innti tiene una base sólida en lo individual: cada archivo, visto de
forma aislada, suele cumplir lo que su prompt pedía. Donde falla de manera
sistemática es en la **integración** y en los **detalles de comportamiento real** de
las librerías:

- rutas de frontend que no coinciden con `App.tsx` (H2),
- un botón cuyo endpoint de backend nunca se creó (H3),
- un método de backend que quedó como código muerto (2.1),
- un editor que asume que TipTap refresca sus callbacks, cuando no lo hace (H1),
- tests que no pasan (H4) o que rompen el build (H6),
- documentación que no concuerda con los esquemas reales (M1).

La recomendación práctica es **no asumir que el código de Innti funciona solo
porque compila o porque parece correcto**: conviene siempre probar el flujo completo
de extremo a extremo y ejecutar los tests y el build antes de integrar cada prompt.
Tras las correcciones aplicadas en esta revisión, el backend pasa sus 30 tests y el
frontend compila sin errores.
