# Documentación de la API - Innti Propuestas

Esta documentación detalla los endpoints disponibles en la API de Innti Propuestas,
organizada por recurso. Es un complemento al Swagger automático disponible en `/docs`.

## Información General

- **Base URL**: `http://localhost:8000`
- **Prefijo de API**: todos los recursos cuelgan de `/api`
- **Formato de Respuesta**: `application/json` (excepto los endpoints de generación
  de documentos, que devuelven archivos binarios).
- **Autenticación**: el MVP no implementa autenticación.

---

## Enums del Sistema

### ProposalStatus

Estado de una propuesta en el flujo de aprobación.

- `draft`: Borrador, en edición.
- `pending_review`: Enviada a revisión inicial (Ángela).
- `reviewed`: Aprobada por la revisora, pendiente de pasar a VP.
- `pending_vp`: Enviada a Vicepresidencia (Juan Pablo).
- `approved`: Aprobada final por VP.
- `rejected`: Rechazada en cualquier etapa.
- `sent_to_client`: Entregada formalmente al cliente.

### SchemeType

Tipos de esquema comercial soportados.

- `licensing`: Licenciamiento.
- `services`: Prestación de Servicios.
- `support_maintenance`: Soporte y Mantenimiento.
- `concession_bpo`: Concesión o BPO.
- `supply`: Suministro.

### ApprovalRole

Roles que participan en el proceso de aprobación.

- `reviewer`: Ángela (primera instancia).
- `vp`: Juan Pablo (aprobación final).

### ApprovalAction

Acción registrada en una aprobación.

- `approved`: Aprobado.
- `rejected`: Rechazado.

---

## 1. Portafolio

Consulta del catálogo de productos de Quipux (cargado desde `ListaPortafolio.xlsx`).

### Listar Productos

- **Método**: `GET`
- **Ruta**: `/api/portfolio/products`
- **Descripción**: Lista los productos del portafolio con filtros opcionales.
- **Parámetros Query**:
  - `search` (string, opcional): búsqueda por nombre.
  - `product_type` (string, opcional): filtra por tipo (ej. `Plataforma`).
- **Ejemplo Curl**:
  ```bash
  curl -X GET "http://localhost:8000/api/portfolio/products?search=Tránsito"
  ```
- **Respuesta Exitosa (200 OK)**:
  ```json
  [
    {
      "name": "Qx-Tránsito",
      "product_type": "Plataforma",
      "description": "Plataforma misional de tránsito",
      "business_framework": "SaaS",
      "monetization_model": "Suscripción",
      "pricing_model": "Por usuario",
      "country": "Colombia"
    }
  ]
  ```

### Listar Tipos de Producto

- **Método**: `GET`
- **Ruta**: `/api/portfolio/products/types`
- **Descripción**: Devuelve la lista de tipos de producto presentes en el portafolio.
- **Respuesta Exitosa (200 OK)**: `["Plataforma", "Servicio QloudSI"]`

---

## 2. Clientes

Gestión de los clientes destinatarios de las propuestas.

### Crear Cliente

- **Método**: `POST`
- **Ruta**: `/api/clients/`
- **Request Body**:
  ```json
  {
    "name": "Andrés Barreneche Cano",
    "position": "Gerencia Financiera y Administrativa",
    "entity": "Consorcio ITS Medellín",
    "department": "Gerencia",
    "city": "Medellín",
    "email": "andres.barreneche@consorcioits.com"
  }
  ```
  Campos obligatorios: `name`, `entity`. El resto son opcionales.
- **Ejemplo Curl**:
  ```bash
  curl -X POST "http://localhost:8000/api/clients/" \
       -H "Content-Type: application/json" \
       -d '{"name": "Andrés Barreneche", "entity": "Consorcio ITS Medellín"}'
  ```
- **Respuesta Exitosa (201 Created)**: objeto cliente con `id`, `created_at` y `updated_at`.

### Listar Clientes

- **Método**: `GET`
- **Ruta**: `/api/clients/`
- **Parámetros Query**: `skip` (int, default 0), `limit` (int, default 100).

### Obtener Cliente

- **Método**: `GET`
- **Ruta**: `/api/clients/{client_id}`
- **Errores**: `404` si el cliente no existe.

### Actualizar Cliente

- **Método**: `PATCH`
- **Ruta**: `/api/clients/{client_id}`
- **Request Body**: cualquier subconjunto de los campos del cliente.

### Eliminar Cliente

- **Método**: `DELETE`
- **Ruta**: `/api/clients/{client_id}`
- **Respuesta Exitosa**: `204 No Content`.

---

## 3. Propuestas

Gestión del ciclo de vida de las propuestas comerciales.

### Crear Propuesta

- **Método**: `POST`
- **Ruta**: `/api/proposals/`
- **Descripción**: Crea una nueva propuesta en estado `draft`.
- **Request Body**:
  ```json
  {
    "title": "Licenciamiento y Modernización de soluciones",
    "code": "3018-0226",
    "client_id": 1,
    "combine_schemes": true,
    "products": [
      {
        "product_name": "Qx-Tránsito",
        "product_type": "Plataforma",
        "description": "Plataforma misional de tránsito",
        "category": "modernización"
      }
    ],
    "schemes": [
      { "scheme_type": "licensing", "payment_frequency": "unico" }
    ]
  }
  ```
  > Nota: `products` y `schemes` son **listas de objetos**, no de cadenas.
  > Cada producto sigue el esquema `ProposalProductCreate` y cada esquema el
  > `ProposalSchemeCreate`.
- **Ejemplo Curl**:
  ```bash
  curl -X POST "http://localhost:8000/api/proposals/" \
       -H "Content-Type: application/json" \
       -d '{"title": "Propuesta DEI", "client_id": 1, "products": [], "schemes": []}'
  ```
- **Errores**: `404` si `client_id` no corresponde a un cliente existente.

### Listar Propuestas

- **Método**: `GET`
- **Ruta**: `/api/proposals/`
- **Parámetros Query**: `skip` (int, default 0), `limit` (int, default 50).
- **Descripción**: Devuelve las propuestas ordenadas por fecha de actualización descendente.

### Obtener Detalle

- **Método**: `GET`
- **Ruta**: `/api/proposals/{proposal_id}`
- **Descripción**: Devuelve la propuesta completa, incluyendo `products` y `schemes`.
- **Errores**: `404` si la propuesta no existe.

### Actualizar Propuesta

- **Método**: `PATCH`
- **Ruta**: `/api/proposals/{proposal_id}`
- **Descripción**: Actualiza el contenido editable. Todos los campos son opcionales.
- **Campos válidos**: `title`, `cover_title`, `letter_content`, `context_content`,
  `scope_content`, `economic_conditions`, `payment_terms`, `excluded_services`,
  `ip_section`, `confidentiality`, `combine_schemes`.
- **Request Body**:
  ```json
  {
    "economic_conditions": "<p>Valor total: $120.000.000 + IVA</p>",
    "payment_terms": "<p>50% anticipo, 50% contra entrega</p>"
  }
  ```

### Eliminar Propuesta

- **Método**: `DELETE`
- **Ruta**: `/api/proposals/{proposal_id}`
- **Respuesta Exitosa**: `204 No Content`.

### Gestión de Productos de la Propuesta

Estos endpoints solo operan sobre propuestas en estado `draft`.

- **Agregar producto** — `POST /api/proposals/{proposal_id}/products`
  - Body: un objeto `ProposalProductCreate`.
- **Remover producto** — `DELETE /api/proposals/{proposal_id}/products/{product_id}`
  - Respuesta: `204 No Content`.
- **Reemplazar todos los productos** — `PUT /api/proposals/{proposal_id}/products`
  - Body: una **lista** de `ProposalProductCreate`.
- **Errores**: `404` si la propuesta o el producto no existen; `400` si la propuesta
  no está en estado `draft`.

---

## 4. Aprobaciones

Flujo de aprobación: `draft → pending_review → reviewed → pending_vp → approved`.

### Enviar a Revisión / Avanzar en el Flujo

- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/submit-review`
- **Descripción**: Si la propuesta está en `draft`, pasa a `pending_review`. Si está
  en `reviewed`, pasa a `pending_vp`.
- **Errores**: `404` si no existe; `400` si el estado actual no permite avanzar.

### Aprobar Propuesta

- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/approve`
- **Request Body**:
  ```json
  {
    "role": "reviewer",
    "approver_name": "Ángela Pérez",
    "approver_email": "angela@quipux.com",
    "action": "approved",
    "comments": "Revisado y conforme con los términos comerciales."
  }
  ```
  > El campo `action` es obligatorio (esquema `ApprovalCreate`). Para este endpoint
  > debe ser `approved`.
- **Comportamiento**: con `role = reviewer` la propuesta pasa a `reviewed`; con
  `role = vp` pasa a `approved`.
- **Errores**: `409 Conflict` si la transición no es válida para el estado actual;
  `400` para otros errores del flujo.

### Rechazar Propuesta

- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/reject`
- **Request Body**: mismo esquema `ApprovalCreate`, con `action = rejected`.
- **Comportamiento**: la propuesta pasa a `rejected`.

### Historial de Aprobaciones

- **Método**: `GET`
- **Ruta**: `/api/proposals/{proposal_id}/approvals`
- **Descripción**: Devuelve el historial de aprobaciones/rechazos de la propuesta.

---

## 5. Documentos

Generación de archivos a partir de una propuesta. Estos endpoints devuelven un
archivo binario, no JSON.

### Generar Propuesta en Word

- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/generate-document`
- **Parámetros Query**: `use_innti` (bool, default `true`) — usa IA para enriquecer
  el texto cuando la propuesta no tiene contenido.
- **Respuesta**: archivo `.docx`.
- **Ejemplo Curl**:
  ```bash
  curl -X POST "http://localhost:8000/api/proposals/1/generate-document?use_innti=true" \
       --output propuesta.docx
  ```

### Generar Propuesta en PDF

- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/generate-pdf`
- **Parámetros Query**: `use_innti` (bool, default `true`).
- **Descripción**: Construye el documento Word y lo convierte a PDF.
- **Respuesta**: archivo `.pdf`.

### Generar Anexo Técnico

- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/generate-annex`
- **Respuesta**: archivo `.docx` con el detalle técnico de los productos.

---

## 6. Health Check

- `GET /` — estado básico de la aplicación.
- `GET /health` — estado detallado (base de datos y endpoint de Innti).

---

## Códigos de Error Comunes

| Código | Significado | Causa común |
|--------|-------------|-------------|
| 400 | Bad Request | Operación no permitida para el estado actual (ej. modificar productos de una propuesta que no está en `draft`). |
| 404 | Not Found | El recurso indicado (propuesta, cliente, producto) no existe. |
| 409 | Conflict | Transición de estado inválida en el flujo de aprobación. |
| 422 | Unprocessable Entity | Error de validación del cuerpo de la petición (Pydantic). |
| 500 | Internal Server Error | Error inesperado del servidor o de la base de datos. |
| 502 | Bad Gateway | Error al comunicarse con el servicio de IA (Innti). |

Los errores capturados por el manejador centralizado se devuelven con el formato:

```json
{
  "error": "Approval Error",
  "detail": "No se puede aprobar desde estado 'draft'",
  "status_code": 400
}
```
