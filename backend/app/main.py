"""
Punto de entrada de la aplicación FastAPI.
Innti Propuestas - Software de Gestión de Propuestas Comerciales de Quipux.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import portfolio, proposals, approvals, documents, clients, users, auth
from app.middleware.error_handler import register_error_handlers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja eventos del ciclo de vida de la aplicación.
    startup: al iniciar, crear tablas de BD
    shutdown: al cerrar, limpiar recursos
    """
    # Startup
    init_db()
    yield
    # Shutdown (si fuera necesario limpiar recursos)


app = FastAPI(
    title="Innti Propuestas API",
    description="API para gestión y generación de propuestas comerciales de Quipux S.A.S.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Registrar handlers de errores
register_error_handlers(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar routers
app.include_router(portfolio.router)
app.include_router(proposals.router)
app.include_router(approvals.router)
app.include_router(documents.router)
app.include_router(clients.router)
app.include_router(users.router)
app.include_router(auth.router)


@app.get("/", tags=["Health"])
def root():
    """Health check."""
    return {
        "app": "Innti Propuestas",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health", tags=["Health"])
def health():
    """Health check detallado."""
    return {
        "status": "healthy",
        "database": "sqlite",
        "innti_endpoint": settings.innti_api_base,
    }
