"""
Endpoints para consulta del portafolio de soluciones.
"""
from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from pydantic import BaseModel

from app.config import get_settings, Settings

router = APIRouter(prefix="/api/portfolio", tags=["Portafolio"])


class PortfolioProductResponse(BaseModel):
    """Respuesta con datos de un producto del portafolio."""
    name: str
    product_type: str
    description: str
    business_framework: str
    monetization_model: str
    pricing_model: str
    country: str


def get_portfolio_service(settings: Settings = Depends(get_settings)):
    """Dependency para obtener el servicio de portafolio."""
    from app.services.portfolio_service import PortfolioService
    return PortfolioService(settings.portfolio_file_path)


@router.get("/products", response_model=List[PortfolioProductResponse])
def list_products(
    search: Optional[str] = Query(None, description="Buscar por nombre"),
    product_type: Optional[str] = Query(None, description="Filtrar por tipo"),
    service=Depends(get_portfolio_service),
):
    """Lista todos los productos del portafolio con filtros opcionales."""
    if search:
        products = service.search_products(search)
    elif product_type:
        products = service.filter_by_type(product_type)
    else:
        products = service.get_products()

    return [
        PortfolioProductResponse(
            name=p.name,
            product_type=p.product_type,
            description=p.description,
            business_framework=p.business_framework,
            monetization_model=p.monetization_model,
            pricing_model=p.pricing_model,
            country=p.country,
        )
        for p in products
    ]


@router.get("/products/types", response_model=List[str])
def list_product_types(service=Depends(get_portfolio_service)):
    """Lista los tipos de producto disponibles."""
    products = service.get_products()
    types = sorted(set(p.product_type for p in products if p.product_type))
    return types
