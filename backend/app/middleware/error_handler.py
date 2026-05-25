"""
Middleware de manejo de errores centralizado para FastAPI.
"""
import logging
import traceback
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError

from app.services.portfolio_service import PortfolioNotFoundError
from app.services.innti_service import InntiServiceError
from app.services.approval_service import ApprovalError
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

def create_error_response(error: str, detail: str, status_code: int) -> JSONResponse:
    """Crea una respuesta JSON estandarizada para errores."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "detail": detail,
            "status_code": status_code
        }
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación de FastAPI/Pydantic."""
    logger.error(f"Error de validación: {exc}")
    return create_error_response(
        error="Validation Error",
        detail=str(exc.errors()),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

async def portfolio_not_found_handler(request: Request, exc: PortfolioNotFoundError):
    """Maneja error de portafolio no encontrado."""
    logger.error(f"Portafolio no encontrado: {exc}")
    return create_error_response(
        error="Portfolio Not Found",
        detail=str(exc),
        status_code=status.HTTP_404_NOT_FOUND
    )

async def innti_service_error_handler(request: Request, exc: InntiServiceError):
    """Maneja errores del servicio Innti."""
    logger.error(f"Error en servicio Innti: {exc}")
    return create_error_response(
        error="Innti Service Error",
        detail=str(exc),
        status_code=status.HTTP_502_BAD_GATEWAY
    )

async def approval_error_handler(request: Request, exc: ApprovalError):
    """Maneja errores del flujo de aprobación."""
    logger.error(f"Error de aprobación: {exc}")
    return create_error_response(
        error="Approval Error",
        detail=str(exc),
        status_code=status.HTTP_400_BAD_REQUEST
    )

async def global_exception_handler(request: Request, exc: Exception):
    """Captura cualquier excepción no manejada."""
    logger.error(f"Excepción no manejada: {exc}")
    if settings.debug:
        logger.error(traceback.format_exc())
        detail = f"{str(exc)}\n{traceback.format_exc()}"
    else:
        detail = "Internal Server Error"
        
    return create_error_response(
        error="Internal Server Error",
        detail=detail,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

def register_error_handlers(app):
    """Registra todos los handlers de excepciones en la aplicación FastAPI."""
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(PortfolioNotFoundError, portfolio_not_found_handler)
    app.add_exception_handler(InntiServiceError, innti_service_error_handler)
    app.add_exception_handler(ApprovalError, approval_error_handler)
    app.add_exception_handler(Exception, global_exception_handler)
