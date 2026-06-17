# Innti Propuestas

Software de Gestión de Propuestas Comerciales para Quipux S.A.S.

## Descripción

Aplicación web que automatiza la generación de propuestas comerciales, permitiendo seleccionar productos del portafolio, elegir esquemas de propuesta, generar documentos Word/PDF con estructura estándar y gestionar aprobaciones internas.

## Stack Tecnológico

- **Backend:** Python 3.11+ / FastAPI
- **Frontend:** React 18 + TypeScript + Vite + Tailwind CSS
- **Base de Datos:** SQLite (SQLAlchemy ORM)
- **IA:** Innti via LiteLLM (API OpenAI-Compatible)
- **Documentos:** python-docx (Word) + WeasyPrint (PDF)
- **Editor:** TipTap (rich text)

## Requisitos Previos

- Python 3.11+
- Node.js 18+
- PyCharm Professional (recomendado)

## Instalación

### Backend

```bash
#Paso 1
cd backend
#Paso 2
# Editar .env con tus credenciales
cp .env.example .env
#Paso 3
python -m venv .venv
#Paso 4
# Windows:
.venv\Scripts\activate
.venv\Scripts\pip.exe install uvicorn
# Linux/Mac:
source .venv/bin/activate
#Paso 5
#Ajustar en la ruta donde se tenga clonado el proyecto
.venv\Scripts\pip.exe install -r D:\estudio\innti-propuestas\backend\requirements.txt

```

### Frontend

```bash
cd frontend
npm install
```

## Ejecución

### Backend (terminal 1)

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API disponible en: http://localhost:8000/docs

### Frontend (terminal 2)

```bash
cd frontend
npm run dev
```

Aplicación disponible en: http://localhost:5173

## Testing

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm test
```

## Estructura del Proyecto

```
innti-propuestas/
├── backend/
│   ├── app/
│   │   ├── main.py              # Entry point FastAPI
│   │   ├── config.py            # Variables de entorno
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/              # Modelos BD
│   │   ├── schemas/             # Schemas Pydantic
│   │   ├── routers/             # Endpoints API
│   │   ├── services/            # Lógica de negocio
│   │   └── templates/           # Plantillas Word
│   ├── tests/                   # Pruebas unitarias
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/          # Componentes React
│   │   ├── pages/               # Páginas
│   │   ├── services/            # Cliente API
│   │   └── types/               # TypeScript types
│   └── package.json
└── README.md
```

## Variables de Entorno

Ver `backend/.env.example` para la lista completa de variables requeridas.

## Flujo de la Aplicación

1. Seleccionar productos del portafolio (ListaPortafolio.xlsx)
2. Elegir esquema(s) de propuesta
3. Ingresar datos del cliente
4. Generar documento con Innti (IA)
5. Editar secciones manuales (condiciones económicas)
6. Enviar a aprobación (Ángela → Juan Pablo)
7. Exportar PDF final

## Esquemas de Propuesta

| Esquema | Pago típico |
|---------|-------------|
| Licenciamiento | Pago único |
| Prestación de Servicios | Mensual |
| Soporte y Mantenimiento | Anual |
| Concesión o BPO | Variable |
| Suministro | Variable |

## Usuarios Iniciales

### Usuario Administrador

Al arrancar el backend por primera vez, se crea automáticamente un usuario administrador definido en [`backend/app/seed.py`](backend/app/seed.py):

| Campo | Valor |
|-------|-------|
| **Email** | `admin@quipux.com` |
| **Contraseña** | `Admin2024!` |

### Usuarios de Prueba (creator, approver)

Para crear los usuarios operativos del flujo de aprobación, ejecuta el siguiente script **una sola vez** después de levantar el backend:

```bash
cd backend
python .\.venv\Scripts\python.exe seed_users.py
```

Esto creará los siguientes usuarios (definidos en [`backend/seed_users.py`](backend/seed_users.py)):

| Rol | Email | Contraseña |
|-----|-------|------------|
| Creator | `creator@innti.com` | `Innti2024!` |
| Approver 1 | `angela@innti.com` | `Innti2024!` |
| Approver 2 | `juanpablo@innti.com` | `Innti2024!` |

> **Nota:** Si el usuario ya existe, el script lo omite sin generar errores.

## 🤖 Configuración de Innti (IA)

Para que el sistema pueda generar propuestas automáticamente, es necesario configurar la conexión con **Innti**. 

Sigue estos pasos:

1. Localiza el archivo `.env` en la carpeta `backend/`.
2. Asegúrate de tener las siguientes variables configuradas con las credenciales proporcionadas por la empresa:

```dotenv
# --- Innti (IA Corporativa) ---
INNTI_API_BASE=https://litellm.quipux.com/v1
INNTI_API_KEY=tu_clave_aqui
INNTI_MODEL=innti-dev
```