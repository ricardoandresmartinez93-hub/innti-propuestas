# Instalación en otra PC (Windows + Docker)

Guía para instalar y ejecutar **Innti Propuestas** en una PC nueva. Todo corre
dentro de Docker, así que **no** hace falta instalar Python, Node ni las
librerías de WeasyPrint a mano.

## Requisitos en la PC destino

- **Windows 10/11**
- **Docker Desktop** instalado y funcionando
  (https://www.docker.com/products/docker-desktop/)
- Conexión a internet **la primera vez** (para descargar las imágenes base).

## Pasos

1. Copiá **toda la carpeta del proyecto** a la PC destino (por ejemplo con un
   pendrive, red compartida o `git clone`).
2. Asegurate de que **Docker Desktop** esté abierto (el ícono debe decir
   *Running*).
3. Doble clic en **`install.bat`**.

El instalador se encarga de:

- Verificar que Docker esté instalado y corriendo.
- Crear `backend/.env` desde la plantilla si no existe y abrirlo para que
  completes tus credenciales (clave de IA y correo).
- Construir y levantar backend + frontend (`docker compose up -d --build`).
- Esperar a que el backend responda y abrir la app en el navegador.

Cuando termina:

- **Aplicación:** http://localhost
- **API / Documentación:** http://localhost:8000/docs

### Usuario administrador inicial

Se crea automáticamente al primer arranque:

| Email               | Contraseña   |
| ------------------- | ------------ |
| `admin@quipux.com`  | `Admin2024!` |

> Cambiá esta contraseña después de entrar.

### (Opcional) Usuarios de demo

Para cargar los usuarios de prueba con roles (creador, revisor, VP), ejecutá
**`seed-usuarios.bat`**. La contraseña de todos es `Innti2024!`.

## Uso diario

| Acción                       | Script            |
| ---------------------------- | ----------------- |
| Iniciar la app               | `start.bat`       |
| Detener la app               | `stop.bat`        |
| Reinstalar / reconstruir     | `install.bat`     |
| Cargar usuarios de demo      | `seed-usuarios.bat` |

## Configuración (`backend/.env`)

Variables importantes:

- `INNTI_API_KEY` — clave para la generación con IA (obligatoria para esa función).
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` — correo
  para notificaciones (opcional).
- `JWT_SECRET_KEY` — **cambiala** por un valor propio en producción.

Después de editar `backend/.env`, aplicá los cambios con:

```
stop.bat
start.bat
```

## Datos y persistencia

La base de datos SQLite vive en un **volumen de Docker** (`sqlite_data`), por lo
que **los datos sobreviven** a reinicios y a `stop.bat`. Solo se borrarían si
ejecutás manualmente `docker compose down -v` (la `-v` elimina el volumen).

## Problemas frecuentes

- **"Docker no está corriendo"** → abrí Docker Desktop y esperá a *Running*.
- **El puerto 80 está ocupado** → otra app (IIS, Skype, otro Nginx) usa el
  puerto 80. Cerrala o cambiá el mapeo `"80:80"` en `docker-compose.yml`
  (por ejemplo `"8080:80"`) y entrá a http://localhost:8080.
- **La generación con IA falla** → revisá que `INNTI_API_KEY` esté bien cargada
  en `backend/.env` y reiniciá con `stop.bat` + `start.bat`.
