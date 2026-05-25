"""
Punto de entrada de la aplicación FastAPI.
Innti Propuestas - Software de Gestión de Propuestas Comerciales de Quipux.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import init_db
from app.routers import portfolio, proposals, approvals, documents, clients

settings = get_settings()

app = FastAPI(
    title="Innti Propuestas API",
    description="API para gestión y generación de propuestas comerciales de Quipux S.A.S.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

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


@app.on_event("startup")
def on_startup():
    """Inicializa la base de datos al arrancar."""
    init_db()


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
