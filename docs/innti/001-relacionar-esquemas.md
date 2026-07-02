# 001 — Relacionar esquemas por producto (regla Qloudsi + documento unificado/separado)

> Solución generada según el método descrito en [`README.md`](README.md).
> Rama de trabajo: `feature/Relacionar-esquemas` (ya existe, no hace falta crearla).

## Contexto y decisión de arquitectura

- **Problema:** hoy los esquemas se eligen a nivel de **propuesta** (checkboxes globales) y
  la compatibilidad producto→esquema se calcula por **intersección** entre todos los productos
  seleccionados. Las reglas de negocio reales son otras: **cada producto/servicio tiene UN
  esquema propio**, los servicios QloudSI **nunca** pueden tener "Licenciamiento", y la
  generación de documentos debe ser **unificada** (1 documento con todos los esquemas) o
  **separada** (1 documento por producto/servicio, no por esquema).
- **Solución elegida:** mover la relación de esquema al nivel de producto
  (`ProposalScheme.product_id`), reglar QloudSI en el backend como regla de negocio codificada
  (no solo datos del Excel), rediseñar el selector de esquemas como asignación por producto, y
  cambiar la generación "separada" para iterar productos en vez de esquemas.
- **Por qué esta y no otra:** la alternativa de fusionar los campos del esquema dentro de
  `ProposalProduct` se descartó: infla el modelo de producto, rompe el resolver de contenido y
  el generador de documentos en muchos más puntos, y pierde la separación limpia entre "qué se
  vende" (producto) y "cómo se cobra" (esquema). Agregar `product_id` a `ProposalScheme`
  mantiene `proposal.schemes` funcionando y minimiza el radio de impacto.
- **Track:** `SDD completo` — cambia modelo de datos, API, generación de documentos y UI.
  Artefactos en `openspec/changes/relacionar-esquemas/` (mismo patrón que
  `openspec/changes/proposal-list-filters/`).
- **Archivos que se van a tocar (aproximado):**
  - `backend/app/models/proposal.py`
  - `backend/app/schemas/proposal.py`
  - `backend/app/routers/proposals.py`, `backend/app/routers/portfolio.py`, `backend/app/routers/documents.py`
  - `backend/app/services/portfolio_service.py`, `backend/app/services/proposal_content_resolver.py`
  - `backend/scripts/migrate_schemes_per_product.py` (nuevo)
  - `backend/tests/*` (varios)
  - `frontend/src/types/index.ts`, `frontend/src/services/api.ts`
  - `frontend/src/components/SchemeSelector.tsx`, `frontend/src/pages/NewProposalPage.tsx`, `frontend/src/pages/ProposalDetailPage.tsx`
  - `frontend/src/__tests__/*`
  - `.opencode/skills/innti-domain/SKILL.md`, `docs/API.md`, `README.md`
- **Pre-requisitos:** backend con venv activo y dependencias instaladas; `ListaPortafolio.xlsx`
  accesible; estar parado en la rama `feature/Relacionar-esquemas`.

## Validación contra el código actual (as-is vs. to-be)

| # | Estado actual (as-is) | Regla de negocio (to-be) | Brecha |
|---|----------------------|--------------------------|--------|
| G1 | `ProposalScheme` cuelga de `Proposal`; N esquemas por propuesta, sin vínculo a producto ([proposal.py:107](../../backend/app/models/proposal.py)) | 1 esquema por producto/servicio | Falta `product_id` en `ProposalScheme` y la restricción "exactamente uno" |
| G2 | Esquemas permitidos = **intersección** entre productos (`get_allowed_schemes_for_products`, `computeAllowedSchemes`) | Cada producto resuelve sus esquemas permitidos de forma **independiente** | La intersección queda obsoleta; se reemplaza por resolución por producto |
| G3 | No existe NINGUNA regla QloudSI↛Licenciamiento en código; depende solo de la columna 9 del Excel | QloudSI **nunca** puede tener Licenciamiento (regla dura de negocio) | Falta regla codificada en backend + filtro en UI |
| G4 | "Documentos separados" genera **1 docx por esquema** ([documents.py:233](../../backend/app/routers/documents.py)) | Separado = **1 documento por producto/servicio** | Cambiar la iteración de `proposal.schemes` a `proposal.products` |
| G5 | Validador: `combine_schemes=False` exige ≥2 **esquemas** ([schemas/proposal.py:87](../../backend/app/schemas/proposal.py)) | Separado tiene sentido con ≥2 **productos** | Ajustar el validador |
| G6 | UI: checkboxes de esquema globales para toda la propuesta (`SchemeSelector.tsx`) | Selector de esquema **por producto** (radio, uno solo), ocultando Licenciamiento para QloudSI | Rediseño del componente |

**Síntoma visible del bug (G2):** en el paso 2 del asistente ("Configurar Esquemas
Comerciales"), al elegir productos sin esquemas en común la UI bloquea el avance con el aviso
*"Los productos seleccionados no comparten ningún esquema comercial en común"* y deshabilita
"Siguiente". Esa regla ya no aplica al negocio: cada producto asigna su esquema de forma
independiente y dos productos pueden tener el mismo esquema. El aviso y el bloqueo se eliminan
(Prompts 8 y 9).

**Datos existentes:** no hay Alembic; el proyecto ya usa scripts ligeros de migración SQLite
(`backend/scripts/migrate_scheme_content.py`). Se sigue ese patrón: script que agrega la columna
`product_id` (nullable) y hace backfill best-effort. Las propuestas legadas cuyo vínculo no se
pueda inferir quedan con `product_id = NULL` y conservan el comportamiento actual de generación.
**No se borra la base de datos.**

## Reglas de negocio (fuente de verdad)

1. **Un esquema por entidad:** cada producto/servicio incluido en una propuesta tiene asignado
   exactamente UN esquema (no múltiples).
2. **Selección múltiple de productos:** el usuario puede elegir varios productos; cada uno
   mantiene su propio esquema único e independiente.
3. **Excepción QloudSI:** los productos con `product_type` que contenga "QloudSI"
   (case-insensitive) NO pueden tener el esquema `licensing` (Licenciamiento). Las plataformas
   y demás productos del portafolio SÍ pueden.
4. **Documento unificado** (`combine_schemes=True`): se genera 1 único documento que integra el
   esquema de cada producto/servicio como bloques dentro del mismo archivo.
5. **Documentos separados** (`combine_schemes=False`): se generan N documentos, uno por cada
   producto/servicio, cada uno con su esquema. Requiere ≥2 productos.
6. La restricción por datos del Excel (columna 9 "Esquemas Permitidos") sigue vigente y se
   aplica **por producto** (ya no como intersección). La regla QloudSI se aplica ENCIMA de esa
   lista: aunque el Excel diga `licensing`, un QloudSI nunca lo ofrece.

## Flujos UI/UX

### Paso 2 — Asignación de esquemas (rediseño de `SchemeSelector`)

- Se muestra **una tarjeta por producto seleccionado** (nombre + tipo del producto).
- Dentro de cada tarjeta: **radio buttons** con los esquemas permitidos para ESE producto
  (los que devuelve el backend en `allowed_schemes`, que ya excluye Licenciamiento si es QloudSI).
- En productos QloudSI se muestra una nota: *"Licenciamiento no disponible para servicios QloudSI"*.
- Cada tarjeta incluye su selector de **frecuencia de pago** (Único / Mensual / Anual).
- No se puede avanzar hasta que TODOS los productos tengan un esquema asignado.
- Desaparece el aviso de "productos sin esquema en común" (ya no hay intersección).

### Configuración de documentos

- Con **≥2 productos** aparece el toggle:
  - **"Documento unificado"** → 1 archivo; dentro, un bloque por producto con el título
    `PRODUCTO — ESQUEMA` y sus secciones propias (alcance, plazo, condiciones económicas,
    forma de pago, exclusiones, PI). Dos productos con el mismo tipo de esquema generan dos
    bloques distintos (sus condiciones económicas difieren).
  - **"Documentos separados"** → ZIP con un `.docx`/`.pdf` **por producto**, nombrado con el
    producto (ej. `propuesta_12_quipux-move_ab34cd.docx`).
- Con 1 solo producto no hay toggle: siempre se genera 1 documento.

### Detalle/edición de propuesta

- Las secciones editables por esquema se rotulan `«Producto» — «Esquema»` para que el usuario
  sepa qué está editando cuando hay varios productos.

## Prompts para Innti

> Pegá un prompt por vez en OpenCode. Esperá a que Innti termine y hacé la verificación antes
> de pasar al siguiente. Todos construyen sobre el anterior (Innti mantiene contexto).

### Prompt 1 — SDD: proposal + spec

**Qué hace este prompt:** arranca el track SDD. Innti explora el código actual y escribe la
propuesta de cambio y la especificación con las reglas de negocio como requisitos verificables.

**Prompt para Innti:**

```text
Vamos a iniciar un cambio SDD llamado "relacionar-esquemas" siguiendo el mismo patrón de
artefactos de openspec/changes/proposal-list-filters/.

Contexto del cambio — reglas de negocio nuevas:
1. Cada producto/servicio de una propuesta tiene asignado exactamente UN esquema (hoy los
   esquemas son a nivel propuesta, sin vínculo a producto).
2. El usuario puede seleccionar varios productos; cada uno mantiene su esquema propio.
3. Los productos con product_type que contenga "QloudSI" (case-insensitive) NO pueden tener
   el esquema licensing. Es una regla dura de negocio que debe vivir en el backend, no solo
   en los datos del Excel. El resto de productos sí puede.
4. combine_schemes=True → 1 documento unificado con un bloque por producto (producto + su
   esquema y sus secciones).
5. combine_schemes=False → N documentos, uno POR PRODUCTO (hoy se genera uno por esquema).
   Requiere ≥2 productos (hoy el validador exige ≥2 esquemas).
6. La restricción de la columna 9 del Excel sigue vigente pero se aplica POR PRODUCTO (la
   intersección entre productos queda obsoleta y debe eliminarse).

Tarea: explorá el código relevante (backend/app/models/proposal.py,
backend/app/schemas/proposal.py, backend/app/routers/proposals.py,
backend/app/routers/documents.py, backend/app/services/portfolio_service.py,
frontend/src/components/SchemeSelector.tsx, frontend/src/pages/NewProposalPage.tsx) y creá:
- openspec/changes/relacionar-esquemas/proposal.md (intención, alcance, impacto)
- openspec/changes/relacionar-esquemas/spec.md (requisitos con escenarios verificables para
  las 6 reglas, incluyendo casos borde: propuesta con 1 producto, dos productos con el mismo
  tipo de esquema, QloudSI intentando licensing por API directa)
- openspec/changes/relacionar-esquemas/state.yaml (fase: spec)

No modifiques código todavía. No hagas commit.
```

**Resultado esperado:** carpeta `openspec/changes/relacionar-esquemas/` con `proposal.md`,
`spec.md` y `state.yaml`.

**Verificación:** abrir los dos `.md` y confirmar que las 6 reglas están como requisitos con
escenarios (incluido el caso QloudSI + licensing → HTTP 422).

---

### Prompt 2 — SDD: design + tasks (decisiones de arquitectura ya tomadas)

**Qué hace este prompt:** fija el diseño técnico. Las decisiones ya están tomadas (las tomé yo
como arquitecto); Innti las documenta, completa el detalle técnico y desglosa las tareas.

**Prompt para Innti:**

```text
Continuamos el cambio relacionar-esquemas. Creá openspec/changes/relacionar-esquemas/design.md
y tasks.md documentando y detallando ESTAS decisiones de arquitectura (ya están tomadas, no
las cambies; sí completá el detalle técnico):

D1. Modelo: agregar product_id (Integer, ForeignKey a proposal_products.id, nullable=True,
    index) a ProposalScheme, con relación 1:1 ProposalProduct.scheme (uselist=False).
    Se conserva proposal_id. La restricción "exactamente 1 esquema por producto" se aplica a
    nivel de API (Pydantic + router), NO como unique constraint en BD, para no romper filas
    legadas con product_id NULL.
D2. Regla QloudSI: helper is_qloudsi_product(product_type: str) -> bool en
    backend/app/services/portfolio_service.py ("qloudsi" in product_type.lower()) y constante
    QLOUDSI_FORBIDDEN_SCHEMES = {"licensing"}. Única fuente de verdad de la regla.
D3. Esquemas permitidos por producto: nuevo método
    PortfolioService.get_allowed_schemes_for_product(product) = (columna 9 del Excel, o todos
    los MVP si está vacía) menos QLOUDSI_FORBIDDEN_SCHEMES si es QloudSI. El endpoint
    GET /api/portfolio pobla allowed_schemes de cada producto con este método, así el frontend
    consume la regla sin duplicarla. El método de intersección
    get_allowed_schemes_for_products se ELIMINA junto con sus usos y tests.
D4. API de creación: ProposalProductCreate incorpora un campo scheme: ProposalSchemeCreate
    (obligatorio, exactamente uno). Se elimina el campo top-level schemes de ProposalCreate.
    Validadores: (a) cada producto trae exactamente 1 esquema; (b) combine_schemes=False
    requiere ≥2 productos; (c) producto QloudSI con scheme_type licensing → HTTP 422 en el
    router. ProposalRead: cada ProposalProductRead incluye su scheme; se mantiene la lista
    schemes de la propuesta para lectura (compatibilidad con la página de detalle).
D5. Documentos: modo unificado = 1 docx con un bloque por PRODUCTO (encabezado
    "PRODUCTO — ESQUEMA"); modo separado = un docx por PRODUCTO (nombre de archivo con slug
    del producto) empaquetados en ZIP. Propuestas legadas (algún scheme con product_id NULL)
    conservan el comportamiento actual por esquema — detectarlo con una propiedad en el modelo
    (ej. Proposal.uses_product_schemes).
D6. Migración: script backend/scripts/migrate_schemes_per_product.py siguiendo el patrón de
    backend/scripts/migrate_scheme_content.py — agrega la columna si falta; backfill: si la
    propuesta tiene exactamente 1 producto, vincula sus esquemas a ese producto; si tiene
    varios, deja NULL y lo reporta por consola como propuesta legada.

tasks.md: desglosá en tareas chicas ordenadas (modelo → servicio portafolio → schemas/router →
documentos → migración → frontend types/api → SchemeSelector → páginas → docs), cada una con
sus tests. Actualizá state.yaml a fase design/tasks. No modifiques código todavía. No hagas commit.
```

**Resultado esperado:** `design.md` con D1–D6 y `tasks.md` con el desglose ordenado.

**Verificación:** leer `design.md` y confirmar que las 6 decisiones están tal cual (sin
cambios de fondo) y que `tasks.md` respeta el orden backend → frontend → docs.

---

### Prompt 3 — Backend: modelo + regla QloudSI

**Qué hace este prompt:** primera implementación. Agrega el vínculo esquema→producto en el
modelo y codifica la regla QloudSI con sus tests.

**Prompt para Innti:**

```text
Implementá las tareas de modelo y regla QloudSI del cambio relacionar-esquemas (ver
openspec/changes/relacionar-esquemas/design.md, decisiones D1 y D2):

1. En backend/app/models/proposal.py: agregá product_id a ProposalScheme (FK a
   proposal_products.id, nullable, index) y la relación ProposalProduct.scheme (uselist=False).
   Agregá la propiedad Proposal.uses_product_schemes (True si la propuesta tiene esquemas y
   todos tienen product_id).
2. En backend/app/services/portfolio_service.py: agregá is_qloudsi_product(product_type) y
   QLOUDSI_FORBIDDEN_SCHEMES según D2.
3. Tests en backend/tests/: cobertura para is_qloudsi_product (casos: "Servicio QloudSI",
   "servicio qloudsi", "Plataforma", cadena vacía, None) y para uses_product_schemes
   (todos vinculados / mezcla / sin esquemas).

Marcá las tareas correspondientes en tasks.md. No hagas commit.
```

**Resultado esperado:** modelo con `product_id` + relación, helper QloudSI, tests nuevos.

**Verificación:**

```bash
cd backend && pytest -q
```

---

### Prompt 4 — Backend: esquemas permitidos por producto (adiós intersección)

**Qué hace este prompt:** reemplaza la lógica de intersección por resolución por producto y
hace que el endpoint del portafolio ya devuelva la lista filtrada (incluida la regla QloudSI).

**Prompt para Innti:**

```text
Implementá la decisión D3 del design de relacionar-esquemas:

1. En backend/app/services/portfolio_service.py: agregá
   get_allowed_schemes_for_product(product: PortfolioProduct) -> List[str] — (allowed_schemes
   de la columna 9, o MVP_SCHEME_STRINGS si está vacía) menos QLOUDSI_FORBIDDEN_SCHEMES cuando
   is_qloudsi_product(product.product_type). Eliminá get_allowed_schemes_for_products (la
   intersección) y todos sus usos y tests.
2. En backend/app/routers/portfolio.py: poblá allowed_schemes de la respuesta con el método
   nuevo, de modo que un producto QloudSI NUNCA incluya licensing en su lista.
3. Actualizá backend/tests/test_portfolio.py: tests del método nuevo (producto sin restricción,
   con columna 9, QloudSI con y sin columna 9 — licensing nunca aparece) y limpieza de los
   tests de intersección.

Ojo: backend/app/routers/proposals.py todavía usa la intersección en
_validate_scheme_product_compatibility — en este prompt solo dejala compilando con un reemplazo
mínimo temporal si hace falta; la validación definitiva por producto la implementamos en el
siguiente prompt. Marcá las tareas en tasks.md. No hagas commit.
```

**Resultado esperado:** `allowed_schemes` por producto ya filtrado en `GET /api/portfolio`;
intersección eliminada.

**Verificación:**

```bash
cd backend && pytest -q tests/test_portfolio.py && pytest -q
```

---

### Prompt 5 — Backend: API de creación con esquema por producto

**Qué hace este prompt:** cambia el contrato de creación de propuestas — cada producto viaja
con su esquema — y aplica las tres validaciones nuevas.

**Prompt para Innti:**

```text
Implementá la decisión D4 del design de relacionar-esquemas:

1. En backend/app/schemas/proposal.py:
   - ProposalProductCreate: agregá scheme: ProposalSchemeCreate (obligatorio).
   - ProposalCreate: eliminá el campo schemes; el validador combine_schemes=False pasa a exigir
     ≥2 productos (mensaje en español acorde).
   - ProposalProductRead: agregá scheme: Optional[ProposalSchemeRead].
   - ProposalRead conserva la lista schemes (lectura/compatibilidad).
2. En backend/app/routers/proposals.py (create_proposal):
   - Validá esquemas MVP por producto.
   - Validá regla QloudSI: si is_qloudsi_product(product_type) y scheme_type == licensing →
     HTTP 422 con mensaje claro en español. Usá el product_type del payload y, si viene vacío,
     resolvelo desde el portafolio por nombre.
   - Validá columna 9 por producto con get_allowed_schemes_for_product → HTTP 422 si no cumple.
   - Creá cada ProposalScheme con proposal_id Y product_id del producto correspondiente.
   - Eliminá _validate_scheme_product_compatibility (la versión por intersección).
3. Actualizá los tests de propuestas: creación feliz multi-producto (cada uno con su esquema),
   QloudSI + licensing → 422, QloudSI + services → 201, separado con 1 producto → 422,
   payload viejo con top-level schemes → 422.

Marcá las tareas en tasks.md. No hagas commit.
```

**Resultado esperado:** `POST /api/proposals/` acepta productos-con-esquema y rechaza las tres
violaciones; tests verdes.

**Verificación:**

```bash
cd backend && pytest -q
```

---

### Prompt 6 — Backend: generación de documentos por producto

**Qué hace este prompt:** adapta el documento unificado (bloques por producto) y el modo
separado (un archivo por producto), preservando el comportamiento para propuestas legadas.

**Prompt para Innti:**

```text
Implementá la decisión D5 del design de relacionar-esquemas en
backend/app/routers/documents.py y backend/app/services/proposal_content_resolver.py (y
document_generator.py solo si hace falta):

1. Modo unificado (combine_schemes=True) para propuestas con uses_product_schemes: el payload
   de bloques se construye iterando proposal.products — cada bloque lleva encabezado
   "PRODUCTO — ESQUEMA" (nombre del producto + label del esquema en español) y las secciones
   de SU esquema. Dos productos con el mismo tipo de esquema generan dos bloques.
2. Modo separado (combine_schemes=False, ≥2 productos) para uses_product_schemes: un docx por
   PRODUCTO con las secciones de su esquema; nombre de archivo
   propuesta_{id}_{slug-del-producto}_{uid}.docx; ZIP igual que hoy. Idem PDF.
3. La generación de contenido con Innti IA por esquema (generate_scope_section, etc.) recibe
   solo el nombre del producto vinculado al esquema, no todos los productos de la propuesta.
4. Propuestas legadas (uses_product_schemes=False): conservan el flujo actual por esquema, sin
   cambios de comportamiento.
5. Actualizá/agregá tests: test_documents_api.py y test_document_generator.py — unificado con
   2 productos mismo esquema → 2 bloques; separado con 3 productos → ZIP con 3 archivos
   nombrados por producto; propuesta legada → comportamiento anterior intacto.

Marcá las tareas en tasks.md. No hagas commit.
```

**Resultado esperado:** documentos generados por producto en ambos modos; legadas intactas.

**Verificación:**

```bash
cd backend && pytest -q tests/test_documents_api.py tests/test_document_generator.py && pytest -q
```

---

### Prompt 7 — Backend: script de migración

**Qué hace este prompt:** crea la migración ligera de SQLite (columna nueva + backfill
best-effort), siguiendo el patrón que ya existe en el repo.

**Prompt para Innti:**

```text
Implementá la decisión D6 del design de relacionar-esquemas: creá
backend/scripts/migrate_schemes_per_product.py siguiendo el patrón de
backend/scripts/migrate_scheme_content.py:

1. Agrega la columna product_id a proposal_schemes si no existe (ALTER TABLE, SQLite).
2. Backfill: para cada propuesta con exactamente 1 producto, vincula todos sus esquemas a ese
   producto. Propuestas con 2+ productos: deja product_id NULL y reporta por consola
   "Propuesta {id} '{titulo}': N productos, esquemas quedan como legados".
3. Idempotente: correrlo dos veces no rompe nada.
4. Test del backfill con una BD temporal (propuesta 1-producto → vinculado; multi-producto →
   NULL).

Después corré el script contra la BD de desarrollo y mostrame el reporte. Marcá las tareas en
tasks.md. No hagas commit.
```

**Resultado esperado:** script idempotente + reporte de qué propuestas quedaron legadas.

**Verificación:**

```bash
cd backend && pytest -q && python scripts/migrate_schemes_per_product.py
```

(la segunda corrida del script debe terminar sin errores — idempotencia)

---

### Prompt 8 — Frontend: types, API y rediseño de SchemeSelector

**Qué hace este prompt:** actualiza los contratos TypeScript y convierte el selector global de
esquemas en asignación por producto (radio por tarjeta, QloudSI sin Licenciamiento).

**Prompt para Innti:**

```text
Implementá el frontend del cambio relacionar-esquemas (ver design.md D3/D4 y la sección
"Flujos UI/UX" de docs/innti/001-relacionar-esquemas.md):

1. frontend/src/types/index.ts: el producto de propuesta incorpora su scheme (uno solo);
   ajustá los tipos del payload de creación (products con scheme embebido, sin lista schemes
   top-level).
2. frontend/src/services/api.ts: adaptá el payload de creación al contrato nuevo.
3. frontend/src/components/SchemeSelector.tsx — rediseño:
   - Recibe los productos seleccionados (con su allowed_schemes que ya viene filtrado del
     backend, incluyendo la exclusión QloudSI).
   - Renderiza una tarjeta por producto: nombre, tipo, radio buttons con SOLO sus esquemas
     permitidos, y frecuencia de pago (Único/Mensual/Anual) por producto.
   - En productos QloudSI muestra la nota "Licenciamiento no disponible para servicios QloudSI".
   - Con ≥2 productos muestra el toggle "Documento unificado" / "Documentos separados"
     (combine_schemes); con 1 producto no lo muestra.
   - Emite el estado solo cuando TODOS los productos tienen esquema asignado; eliminá la
     lógica y el aviso de intersección vacía.
4. Reescribí frontend/src/__tests__/SchemeSelector.test.tsx: tarjeta por producto, QloudSI no
   renderiza opción licensing y muestra la nota, no emite hasta que todos tengan esquema,
   toggle solo con ≥2 productos.

Marcá las tareas en tasks.md. No hagas commit.
```

**Resultado esperado:** selector por producto funcionando con tests verdes.

**Verificación:**

```bash
cd frontend && npm test
```

---

### Prompt 9 — Frontend: páginas (NewProposalPage + ProposalDetailPage)

**Qué hace este prompt:** conecta el selector nuevo al asistente de creación y rotula la
edición por producto en el detalle.

**Prompt para Innti:**

```text
Cerrá el frontend de relacionar-esquemas:

1. frontend/src/pages/NewProposalPage.tsx:
   - Eliminá computeAllowedSchemes y toda la lógica de intersección.
   - Pasale al SchemeSelector los productos seleccionados con su allowed_schemes.
   - Armá el payload nuevo (cada producto con su scheme embebido).
   - No permitir avanzar/enviar si algún producto no tiene esquema asignado.
2. frontend/src/pages/ProposalDetailPage.tsx: las secciones editables por esquema se rotulan
   "«Producto» — «Esquema»" cuando la propuesta tiene esquemas vinculados a producto; si es
   una propuesta legada (esquemas sin producto), mantené el rótulo actual.
3. Actualizá los tests de páginas afectados y agregá cobertura del flujo: seleccionar 2
   productos (uno QloudSI) → asignar esquemas → payload correcto.

Después corré la suite completa de frontend Y la de backend para confirmar que no rompimos
nada. Marcá las tareas en tasks.md. No hagas commit.
```

**Resultado esperado:** flujo de creación completo con el contrato nuevo; ambas suites verdes.

**Verificación:**

```bash
cd frontend && npm test
cd ../backend && pytest -q
```

---

### Prompt 10 — Docs + verificación SDD + cierre

**Qué hace este prompt:** actualiza la documentación viva del proyecto (incluida la skill de
dominio que Innti carga en cada sesión), verifica la implementación contra la spec y cierra el
cambio SDD. Sin commit.

**Prompt para Innti:**

```text
Cierre del cambio relacionar-esquemas:

1. Actualizá .opencode/skills/innti-domain/SKILL.md: reescribí la sección "Restricción
   Producto → Esquemas" — ya no hay intersección; la resolución es por producto
   (get_allowed_schemes_for_product), un esquema por producto, y la regla dura QloudSI ↛
   licensing (is_qloudsi_product + QLOUDSI_FORBIDDEN_SCHEMES). Documentá también la semántica
   nueva de combine_schemes (unificado = bloques por producto; separado = un documento por
   producto) y el trato de propuestas legadas.
2. Actualizá docs/API.md con el contrato nuevo de POST /api/proposals/ (products con scheme
   embebido) y los tres errores 422 posibles.
3. Actualizá README.md si menciona el flujo de selección de esquemas.
4. Verificación SDD: repasá openspec/changes/relacionar-esquemas/spec.md escenario por
   escenario contra la implementación y reportá CRITICAL/WARNING/SUGGESTION. Si todo está en
   verde, marcá tasks.md completo y actualizá state.yaml a fase verify.
5. Corré ambas suites completas (pytest y npm test) y mostrame el resultado.

NO hagas commit ni push — eso lo autorizo yo después de revisar.
```

**Resultado esperado:** docs actualizadas, reporte de verificación sin CRITICAL, suites verdes.

**Verificación:** leer el reporte de verificación de Innti; confirmar que
`.opencode/skills/innti-domain/SKILL.md` ya no menciona la intersección.

---

## Cierre

> **Nota de ejecución (2026-07-02):** esta solución fue implementada directamente
> por Claude (a pedido del usuario), no por Innti vía OpenCode. Los prompts se
> ejecutaron como plan de implementación con el mismo alcance y orden.

- [x] Todos los prompts ejecutados y verificados
- [x] Tests en verde — backend: 317 passed (`pytest`) / frontend: 132 passed (`npm test`) + `tsc --noEmit` limpio
- [x] Documentación actualizada (`innti-domain/SKILL.md`, `docs/API.md`, `README.md`)
- [x] Migración corrida sobre la BD de desarrollo — 8 esquemas vinculados;
      3 propuestas multi-producto quedaron como legadas (ids 1, 2 y 7, datos de prueba)
- [ ] **Commit/push:** pendiente de autorización explícita del usuario
