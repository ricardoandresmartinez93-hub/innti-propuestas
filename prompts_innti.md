# Prompts para Innti - Proyecto Innti Propuestas

Documento de prompts organizados por fase para ejecutar con Innti (IA corporativa de Quipux).
Cada prompt está diseñado para producir código funcional y listo para integrar al proyecto.

---

## FASE 1: BACKEND - Modelos y Base de Datos

### Prompt 1.1: Crear endpoint de Clientes (CRUD completo)

**Objetivo:** Implementar el router CRUD completo para gestión de clientes.

**Contexto:** El proyecto usa FastAPI con SQLAlchemy. Ya existen los modelos en `app/models/client.py` y los schemas en `app/schemas/client.py`. Necesitamos el router con endpoints REST.

**Tarea específica:**
Crea el archivo `app/routers/clients.py` con los siguientes endpoints:
- `POST /api/clients/` - Crear cliente
- `GET /api/clients/` - Listar clientes (con paginación skip/limit)
- `GET /api/clients/{client_id}` - Obtener cliente por ID
- `PATCH /api/clients/{client_id}` - Actualizar cliente
- `DELETE /api/clients/{client_id}` - Eliminar cliente

**Resultado esperado:** Archivo Python completo con todos los endpoints, manejo de errores HTTP (404 si no existe), y uso de Depends(get_db) para inyección de la sesión de BD.

**Restricciones técnicas:**
- Usar FastAPI APIRouter con prefix="/api/clients" y tags=["Clientes"]
- Schemas Pydantic: ClientCreate, ClientRead, ClientUpdate (ya definidos)
- Modelo SQLAlchemy: Client (ya definido)
- Manejar HTTPException con status codes apropiados
- No usar async (SQLite no lo requiere en MVP)

**Formato de salida:** Archivo Python completo, listo para guardar en `app/routers/clients.py`.

---

### Prompt 1.2: Agregar productos a propuesta existente

**Objetivo:** Implementar endpoint para agregar/remover productos de una propuesta.

**Contexto:** Una propuesta (`Proposal`) tiene una relación many-to-many con productos del portafolio a través de `ProposalProduct`. El usuario selecciona productos del portafolio (Excel) y se asocian a la propuesta.

**Tarea específica:**
Agregar estos endpoints al router de propuestas (`app/routers/proposals.py`):
- `POST /api/proposals/{proposal_id}/products` - Agregar un producto
- `DELETE /api/proposals/{proposal_id}/products/{product_id}` - Remover un producto
- `PUT /api/proposals/{proposal_id}/products` - Reemplazar todos los productos (recibe lista)

**Resultado esperado:** Código de los 3 endpoints con validaciones.

**Restricciones técnicas:**
- Verificar que la propuesta existe (404 si no)
- Verificar que la propuesta está en estado DRAFT (400 si no, porque no se puede modificar una propuesta en revisión)
- Usar schemas: ProposalProductCreate
- El PUT recibe una lista de ProposalProductCreate y reemplaza todos los productos existentes

**Formato de salida:** Fragmento de código Python para agregar al archivo existente.

---

## FASE 2: BACKEND - Generación de Documentos

### Prompt 2.1: Implementar generación de PDF desde Word

**Objetivo:** Crear servicio que convierte documentos Word generados a PDF.

**Contexto:** El proyecto usa python-docx para generar Word. Necesitamos convertir esos documentos a PDF para envío final al cliente. El stack incluye WeasyPrint.

**Tarea específica:**
Crea un método `convert_docx_to_pdf(docx_path: str, pdf_path: str) -> str` en `app/services/document_generator.py` que:
1. Lea el archivo .docx generado
2. Extraiga el contenido como HTML
3. Use WeasyPrint para generar el PDF
4. Retorne la ruta del PDF generado

**Resultado esperado:** Método funcional que genera PDF legible desde un .docx.

**Restricciones técnicas:**
- Usar WeasyPrint (ya en requirements.txt)
- Manejar errores si el archivo no existe
- El PDF debe mantener estructura similar al Word (headings, listas, tablas)
- Alternativa: si WeasyPrint tiene problemas con docx directo, considerar usar mammoth para docx→HTML y luego WeasyPrint HTML→PDF

**Formato de salida:** Método Python completo con imports necesarios.

---

### Prompt 2.2: Crear plantilla Word con formato Quipux

**Objetivo:** Mejorar la generación de documentos Word para replicar el formato profesional de Quipux.

**Contexto:** Las propuestas de Quipux tienen un formato estándar con: portada centrada, carta de presentación formal, secciones con Heading 1, párrafos en Calibri 11pt, listas con bullets, tablas con bordes grises. Ya existe un generador básico en `app/services/document_generator.py`.

**Tarea específica:**
Mejora el método `generate_proposal_docx` para:
1. Configurar márgenes: 2.5cm superior/inferior, 3cm izquierdo, 2.5cm derecho
2. Personalizar estilos: Heading 1 en azul oscuro (#1a365d), Heading 2 en gris (#2d3748)
3. Portada con título centrado en grande, subtítulo, logo placeholder
4. Tabla de contenido (placeholder con texto "TABLA DE CONTENIDO")
5. Numeración de páginas en el footer
6. Párrafos justificados con interlineado 1.15

**Resultado esperado:** Método mejorado que genera documentos con aspecto profesional.

**Restricciones técnicas:**
- Usar python-docx
- Fuente principal: Calibri
- No depender de archivos de plantilla externos (generar todo programáticamente)
- Mantener la API del método sin cambios (mismos parámetros)

**Formato de salida:** Método Python completo reemplazando el existente.

---

## FASE 3: FRONTEND - Componentes React

### Prompt 3.1: Implementar formulario de datos del cliente

**Objetivo:** Crear componente React para capturar datos del cliente destinatario de la propuesta.

**Contexto:** Proyecto React 18 + TypeScript + Tailwind CSS. Los tipos están definidos en `src/types/index.ts` (interfaz ClientCreate). La API está en `src/services/api.ts`.

**Tarea específica:**
Crea el componente `src/components/ClientForm.tsx` con:
1. Campos: nombre (requerido), cargo, entidad (requerido), departamento, ciudad, email
2. Validación de campos requeridos antes de submit
3. Botón de guardar que llama a la API
4. Estado de loading mientras se envía
5. Manejo de errores con mensaje visible

**Resultado esperado:** Componente React funcional completo.

**Restricciones técnicas:**
- React functional component con hooks (useState)
- Tailwind CSS para estilos (clases utilitarias, no CSS custom)
- TypeScript con tipos estrictos
- Props: onClientCreated(client: Client) callback
- No usar librerías de formularios (react-hook-form, formik) - mantener simple con useState

**Formato de salida:** Archivo TSX completo.

---

### Prompt 3.2: Implementar selector de esquemas de propuesta

**Objetivo:** Crear componente para seleccionar esquemas de propuesta y configurar si se combinan o separan.

**Contexto:** Los esquemas disponibles son: Licenciamiento, Prestación de Servicios, Soporte y Mantenimiento, Concesión o BPO, Suministro. El usuario puede seleccionar uno o varios. Si selecciona más de uno, debe decidir si combinarlos en un solo documento o separarlos.

**Tarea específica:**
Crea `src/components/SchemeSelector.tsx` con:
1. Lista de 5 esquemas con checkboxes
2. Descripción breve de cada esquema
3. Si se seleccionan 2+ esquemas, mostrar toggle: "Combinar en un solo documento" vs "Documentos separados"
4. Para cada esquema seleccionado, selector de frecuencia de pago: "Único", "Mensual", "Anual"

**Resultado esperado:** Componente React funcional interactivo.

**Restricciones técnicas:**
- TypeScript estricto
- Tailwind CSS
- Props: onSchemesChanged(schemes: ProposalScheme[], combineSchemes: boolean) callback
- Usar los tipos SchemeType y SCHEME_LABELS de `src/types/index.ts`

**Formato de salida:** Archivo TSX completo.

---

### Prompt 3.3: Implementar editor TipTap para propuestas

**Objetivo:** Integrar editor rich text TipTap para edición de secciones manuales de la propuesta.

**Contexto:** El usuario necesita editar secciones como condiciones económicas, forma de pago e integraciones directamente en la aplicación. El contenido se guarda como HTML y se envía al backend.

**Tarea específica:**
Crea `src/components/ProposalEditor.tsx` con:
1. Editor TipTap con toolbar básica: bold, italic, headings (H1-H3), listas, tablas
2. Secciones divididas por tabs o acordeón: Contexto, Alcance, Condiciones Económicas, Forma de Pago
3. Botón "Guardar" que envía el contenido HTML al backend via PATCH
4. Indicador de "cambios sin guardar"

**Resultado esperado:** Componente React con editor funcional.

**Restricciones técnicas:**
- Dependencias: @tiptap/react, @tiptap/starter-kit, @tiptap/extension-table (ya en package.json)
- TypeScript
- Tailwind CSS
- Props: proposalId: number, initialContent: Record<string, string>
- Guardar via proposalApi.update()

**Formato de salida:** Archivo TSX completo con imports.

---

## FASE 4: FRONTEND - Flujo Completo

### Prompt 4.1: Implementar página completa de creación de propuesta

**Objetivo:** Crear la página completa que integra todos los pasos del flujo de creación de propuesta.

**Contexto:** Ya existen los componentes: selección de portafolio (en NewProposalPage.tsx), ClientForm, SchemeSelector. Falta integrarlos en un wizard paso a paso.

**Tarea específica:**
Refactoriza `src/pages/NewProposalPage.tsx` como un wizard de 4 pasos:
1. **Paso 1:** Selección de productos del portafolio (ya implementado)
2. **Paso 2:** Selección de esquema(s) (usar SchemeSelector)
3. **Paso 3:** Datos del cliente (usar ClientForm)
4. **Paso 4:** Resumen y confirmación
Al confirmar, llamar a `proposalApi.create()` con todos los datos y redirigir al editor.

**Resultado esperado:** Wizard funcional con navegación Anterior/Siguiente.

**Restricciones técnicas:**
- useState para el paso actual (1-4)
- Validar que cada paso tenga datos antes de avanzar
- Botones: "Anterior", "Siguiente", "Crear Propuesta" (solo en paso 4)
- Usar react-router-dom useNavigate para redirigir después de crear
- Tailwind CSS para el stepper visual

**Formato de salida:** Archivo TSX completo reemplazando NewProposalPage.tsx.

---

### Prompt 4.2: Implementar página de detalle/edición de propuesta

**Objetivo:** Crear página que muestra una propuesta existente con su editor y acciones.

**Contexto:** Después de crear una propuesta, el usuario necesita editarla (agregar condiciones económicas), generar documentos y enviar a aprobación.

**Tarea específica:**
Crea `src/pages/ProposalDetailPage.tsx` con:
1. Header con título, código, estado (badge de color)
2. Editor TipTap con las secciones de la propuesta
3. Sidebar con acciones: "Generar Word", "Generar PDF", "Generar Anexo Técnico"
4. Botón "Enviar a Revisión" (solo si estado es DRAFT)
5. Los documentos descargados se abren automáticamente via blob URL

**Resultado esperado:** Página funcional con editor y descarga de documentos.

**Restricciones técnicas:**
- useParams() para obtener el ID de la URL
- useEffect para cargar la propuesta al montar
- Los botones de generar documentos deben descargar el archivo (responseType: 'blob')
- Usar ProposalEditor component
- Mostrar loading states

**Formato de salida:** Archivo TSX completo.

---

## FASE 5: TESTING

### Prompt 5.1: Tests de integración del API de propuestas

**Objetivo:** Crear tests de integración para el flujo completo de propuestas.

**Contexto:** Ya existen tests unitarios para servicios individuales. Necesitamos tests que validen el flujo completo via HTTP: crear cliente → crear propuesta → agregar productos → enviar a revisión.

**Tarea específica:**
Crea `backend/tests/test_proposals_api.py` con tests:
1. `test_create_proposal_success` - Crear propuesta con cliente y productos
2. `test_create_proposal_invalid_client` - Error 404 si el cliente no existe
3. `test_list_proposals_empty` - Lista vacía al inicio
4. `test_update_proposal_content` - PATCH para editar condiciones económicas
5. `test_delete_proposal` - Eliminar propuesta
6. `test_full_approval_flow` - Crear → submit_review → approve(reviewer) → approve(VP)

**Resultado esperado:** Archivo de tests completo que pasa con pytest.

**Restricciones técnicas:**
- Usar TestClient de FastAPI (fixture `client` de conftest.py)
- Usar fixture `db_session` para verificar estado de BD
- Primero crear un cliente, luego la propuesta (dependencia de datos)
- Assertions claros: status codes, campos en response body
- Cada test debe ser independiente (BD limpia por fixture)

**Formato de salida:** Archivo Python completo.

---

### Prompt 5.2: Tests de componentes React

**Objetivo:** Crear tests para los componentes principales del frontend.

**Contexto:** Proyecto React + TypeScript con Vitest y Testing Library.

**Tarea específica:**
Crea `frontend/src/__tests__/ProposalListPage.test.tsx` con:
1. Test que renderiza "No hay propuestas" cuando la lista está vacía
2. Test que renderiza una tabla con propuestas mockeadas
3. Test que muestra el estado correcto con el badge de color

**Resultado esperado:** Archivo de test funcional con Vitest.

**Restricciones técnicas:**
- Mockear axios con vi.mock
- Usar @testing-library/react: render, screen, waitFor
- Datos de mock: 2-3 propuestas con diferentes estados

**Formato de salida:** Archivo TSX de test completo.

---

## FASE 6: DOCUMENTACIÓN

### Prompt 6.1: Generar documentación de la API

**Objetivo:** Crear documentación detallada de todos los endpoints de la API.

**Contexto:** FastAPI genera documentación automática en /docs (Swagger). Pero necesitamos un documento complementario para el equipo.

**Tarea específica:**
Genera un archivo `docs/API.md` con:
1. Lista de todos los endpoints agrupados por recurso (Portafolio, Propuestas, Aprobaciones, Documentos)
2. Para cada endpoint: método HTTP, ruta, descripción, parámetros, body de request, response esperada
3. Ejemplos de uso con curl
4. Códigos de error comunes

**Resultado esperado:** Documento markdown completo y profesional.

**Restricciones técnicas:**
- Formato Markdown
- Incluir ejemplos reales con datos de Quipux (nombres de productos del portafolio)
- Documentar los enums: ProposalStatus, SchemeType, ApprovalRole

**Formato de salida:** Archivo Markdown completo.

---

## FASE 7: REFACTORIZACIÓN

### Prompt 7.1: Agregar manejo de errores centralizado

**Objetivo:** Implementar middleware de manejo de errores en FastAPI.

**Contexto:** Actualmente cada router maneja sus propios errores con HTTPException. Necesitamos un manejo centralizado para consistencia.

**Tarea específica:**
Crea `app/middleware/error_handler.py` con:
1. Exception handler global que captura excepciones no manejadas
2. Formato estándar de error response: `{"error": str, "detail": str, "status_code": int}`
3. Handlers específicos para: ValidationError, PortfolioNotFoundError, InntiServiceError, ApprovalError
4. Logging de errores con traceback

**Resultado esperado:** Middleware funcional registrado en main.py.

**Restricciones técnicas:**
- Usar @app.exception_handler() de FastAPI
- Logging con el módulo logging de Python
- No exponer tracebacks en producción (solo cuando DEBUG=true)
- Retornar JSONResponse con el formato estándar

**Formato de salida:** Archivo Python completo + instrucciones para registrar en main.py.

---

## FASE 8: DEPLOYMENT

### Prompt 8.1: Crear Dockerfile y docker-compose

**Objetivo:** Containerizar la aplicación para deployment.

**Contexto:** El proyecto tiene backend (Python/FastAPI) y frontend (React/Vite). En producción, el frontend se sirve como archivos estáticos.

**Tarea específica:**
Crea:
1. `backend/Dockerfile` - Imagen Python con dependencias y uvicorn
2. `frontend/Dockerfile` - Build de React y servidor nginx
3. `docker-compose.yml` - Orquestación de ambos servicios

**Resultado esperado:** Archivos Docker funcionales.

**Restricciones técnicas:**
- Backend: python:3.11-slim como base, exponer puerto 8000
- Frontend: node:18 para build, nginx:alpine para servir, exponer puerto 80
- Variables de entorno via .env
- Volume para la base de datos SQLite (persistencia)
- El frontend debe proxy /api al backend

**Formato de salida:** Los 3 archivos completos.

---

## NOTAS DE USO

### Cómo usar estos prompts con Innti:

1. **Copiar** el prompt completo (incluyendo Objetivo, Contexto, Tarea, etc.)
2. **Pegar** en la interfaz de Innti
3. **Revisar** el código generado antes de integrarlo
4. **Probar** ejecutando los tests correspondientes
5. **Ajustar** si es necesario y continuar con el siguiente prompt

### Orden de ejecución recomendado:

1. Prompts 1.x (Backend - completar CRUD)
2. Prompts 2.x (Backend - documentos)
3. Prompts 3.x (Frontend - componentes)
4. Prompts 4.x (Frontend - integración)
5. Prompts 5.x (Testing)
6. Prompts 6.x (Documentación)
7. Prompts 7.x (Refactorización)
8. Prompts 8.x (Deployment)
