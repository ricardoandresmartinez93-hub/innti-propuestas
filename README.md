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
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales
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
