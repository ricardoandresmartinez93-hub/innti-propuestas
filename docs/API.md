# Documentación de la API - Innti Propuestas

Esta documentación detalla los endpoints disponibles en la API de Innti Propuestas, organizada por recursos.

## Información General
- **Base URL**: `http://localhost:8000`
- **Formato de Respuesta**: `application/json` (excepto generación de documentos)

---

## Enums del Sistema

### ProposalStatus
Define el estado de una propuesta en el flujo de aprobación.
- `draft`: Borrador (en edición).
- `pending_review`: Enviada a revisión inicial (Ángela).
- `reviewed`: Revisada y aprobada por Ángela, pendiente de VP.
- `pending_vp`: Enviada a Vicepresidencia (Juan Pablo).
- `approved`: Aprobada final por VP.
- `rejected`: Rechazada en cualquier etapa.
- `sent_to_client`: Entregada formalmente al cliente.

### SchemeType
Tipos de esquemas comerciales soportados.
- `licensing`: Licenciamiento.
- `services`: Prestación de Servicios.
- `support_maintenance`: Soporte y Mantenimiento.
- `concession_bpo`: Concesión o BPO.
- `supply`: Suministro.

### ApprovalRole
Roles que participan en el proceso de aprobación.
- `reviewer`: Ángela (Primera instancia).
- `vp`: Juan Pablo (Aprobación final).

---

## 1. Portafolio
Recursos para consultar el catálogo de productos de Quipux.

### Listar Productos
- **Método**: `GET`
- **Ruta**: `/api/portfolio/products`
- **Descripción**: Obtiene la lista de productos disponibles con filtros opcionales.
- **Parámetros Query**:
    - `search` (string, opcional): Búsqueda por nombre o descripción.
    - `product_type` (string, opcional): Filtrar por tipo (ej. "Plataforma").
- **Ejemplo Curl**:
    ```bash
    curl -X GET "http://localhost:8000/api/portfolio/products?search=Innti"
    ```
- **Respuesta Exitosa (200 OK)**:
    ```json
    [
      {
        "name": "Innti",
        "product_type": "Servicio QloudSI",
        "description": "IA Corporativa y gestión del conocimiento",
        "business_framework": "Saas",
        "monetization_model": "Suscripción",
        "pricing_model": "Por usuario",
        "country": "Global"
      }
    ]
    ```

### Listar Tipos de Producto
- **Método**: `GET`
- **Ruta**: `/api/portfolio/products/types`
- **Descripción**: Obtiene los tipos de productos configurados en el sistema.
- **Ejemplo Curl**:
    ```bash
    curl -X GET "http://localhost:8000/api/portfolio/products/types"
    ```

---

## 2. Propuestas
Gestión del ciclo de vida de las propuestas comerciales.

### Crear Propuesta
- **Método**: `POST`
- **Ruta**: `/api/proposals/`
- **Descripción**: Crea una nueva propuesta en estado `draft`.
- **Request Body**:
    ```json
    {
      "title": "Propuesta Qx-Tránsito Medellín",
      "code": "PROP-2024-001",
      "client_id": 123,
      "combine_schemes": false,
      "products": ["Qx-Tránsito"],
      "schemes": ["licensing", "support_maintenance"]
    }
    ```
- **Ejemplo Curl**:
    ```bash
    curl -X POST "http://localhost:8000/api/proposals/" \
         -H "Content-Type: application/json" \
         -d '{"title": "Propuesta DEI", "code": "P-002", "client_id": 1, "products": ["DEI"]}'
    ```

### Obtener Detalle
- **Método**: `GET`
- **Ruta**: `/api/proposals/{proposal_id}`
- **Descripción**: Obtiene toda la información de una propuesta específica.

### Actualizar Propuesta
- **Método**: `PATCH`
- **Ruta**: `/api/proposals/{proposal_id}`
- **Descripción**: Actualiza campos específicos (alcance, términos, precios).
- **Request Body**: (Campos opcionales)
    ```json
    {
      "scope_description": "Implementación completa de la plataforma DEI.",
      "commercial_conditions": "Pago 50% anticipado, 50% entrega."
    }
    ```

---

## 3. Aprobaciones
Flujo de aprobación reglamentario.

### Enviar a Revisión / Avanzar
- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/submit-review`
- **Descripción**: Cambia el estado de la propuesta al siguiente nivel de revisión.
- **Ejemplo Curl**:
    ```bash
    curl -X POST "http://localhost:8000/api/proposals/1/submit-review"
    ```

### Aprobar Propuesta
- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/approve`
- **Descripción**: Registra la aprobación de un revisor o VP.
- **Request Body**:
    ```json
    {
      "role": "reviewer",
      "approver_name": "Ángela Pérez",
      "approver_email": "angela@quipux.com",
      "comments": "Revisado y conforme con los términos comerciales."
    }
    ```

### Rechazar Propuesta
- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/reject`
- **Descripción**: Devuelve la propuesta a estado `draft` con observaciones.
- **Request Body**:
    ```json
    {
      "role": "vp",
      "approver_name": "Juan Pablo",
      "comments": "Ajustar el modelo de monetización según lo conversado."
    }
    ```

---

## 4. Documentos
Generación de archivos Word (.docx) automatizada.

### Generar Oferta Comercial
- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/generate-document`
- **Descripción**: Genera el documento principal de la propuesta.
- **Parámetros Query**:
    - `use_innti` (bool, default: true): Indica si se debe usar IA para enriquecer el texto.
- **Ejemplo Curl**:
    ```bash
    curl -X POST "http://localhost:8000/api/proposals/1/generate-document?use_innti=true" --output Propuesta.docx
    ```

### Generar Anexo Técnico
- **Método**: `POST`
- **Ruta**: `/api/proposals/{proposal_id}/generate-annex`
- **Descripción**: Genera el anexo técnico detallado.

---

## Códigos de Error Comunes
| Código | Significado | Causa Común |
|---|---|---|
| 400 | Bad Request | Datos de entrada inválidos o faltantes. |
| 403 | Forbidden | Intento de modificar una propuesta ya aprobada. |
| 404 | Not Found | El ID de la propuesta o producto no existe. |
| 422 | Unprocessable Entity | Error de validación de esquema (Pydantic). |
| 500 | Internal Server Error | Error en la lógica del servidor o base de datos. |
