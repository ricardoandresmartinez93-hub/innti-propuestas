"""
Endpoints CRUD para propuestas comerciales.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from typing import List, Dict, Optional

from app.database import get_db
from app.models.user import User
from app.auth import require_creator
from app.models.proposal import (
    Proposal, ProposalProduct, ProposalScheme, ProposalStatus, SchemeType, MVP_SCHEME_TYPES
)
from app.models.client import Client
from app.schemas.proposal import (
    ProposalCreate, ProposalRead, ProposalUpdate,
    ProposalProductCreate, ProposalProductRead,
    ProposalSchemeRead, ProposalSchemeUpdate,
)
from app.routers.portfolio import get_portfolio_service
from app.services.portfolio_service import (
    QLOUDSI_FORBIDDEN_SCHEMES,
    is_qloudsi_product,
)

router = APIRouter(prefix="/api/proposals", tags=["Propuestas"])


def _resolve_product_type(product: ProposalProductCreate, portfolio_service) -> str:
    """Tipo de producto: el del payload o, si viene vacío, el del portafolio."""
    if product.product_type:
        return product.product_type
    match = next(
        (
            p for p in portfolio_service.get_products()
            if p.name.lower() == product.product_name.lower()
        ),
        None,
    )
    return match.product_type if match else ""


def _validate_product_scheme(product: ProposalProductCreate, portfolio_service) -> None:
    """Raises HTTP 422 si el esquema del producto viola una regla de negocio.

    Reglas, en orden: esquema disponible en el MVP; servicios QloudSI no pueden
    tener Licenciamiento (regla dura, independiente del Excel); el esquema debe
    estar en la lista permitida del producto (columna 9 del Excel, ya filtrada
    por la regla QloudSI cuando el producto existe en el portafolio).
    """
    scheme_type = product.scheme.scheme_type

    if scheme_type not in MVP_SCHEME_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"El esquema '{scheme_type.value}' no está disponible en el MVP. "
                   f"Esquemas válidos: licensing, services, support_maintenance",
        )

    product_type = _resolve_product_type(product, portfolio_service)
    if is_qloudsi_product(product_type) and scheme_type.value in QLOUDSI_FORBIDDEN_SCHEMES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"El producto '{product.product_name}' es un servicio QloudSI y no puede "
                f"tener el esquema Licenciamiento. Elegí otro esquema para este servicio."
            ),
        )

    allowed = portfolio_service.get_allowed_schemes_for_product_name(product.product_name)
    if scheme_type.value not in allowed:
        raise HTTPException(
            status_code=422,
            detail=(
                f"El esquema '{scheme_type.value}' no está permitido para el producto "
                f"'{product.product_name}'. Esquemas permitidos: {', '.join(allowed)}"
            ),
        )


@router.post("/", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
def create_proposal(
    data: ProposalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_creator),
    portfolio_svc=Depends(get_portfolio_service),
):
    """Crea una nueva propuesta comercial.

    Cada producto del payload trae su propio esquema (un esquema por producto);
    el esquema se persiste vinculado al producto vía product_id.
    """
    # Validar reglas de negocio por producto (MVP, QloudSI, columna 9)
    for prod in data.products:
        _validate_product_scheme(prod, portfolio_svc)

    # Verificar que el cliente existe
    client = db.query(Client).filter(Client.id == data.client_id).first()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cliente con id {data.client_id} no encontrado",
        )

    proposal = Proposal(
        title=data.title,
        code=data.code,
        client_id=data.client_id,
        combine_schemes=data.combine_schemes,
    )
    db.add(proposal)
    db.flush()

    # Agregar cada producto con su esquema vinculado
    for prod in data.products:
        db_prod = ProposalProduct(
            proposal_id=proposal.id,
            product_name=prod.product_name,
            product_type=prod.product_type,
            description=prod.description,
            category=prod.category,
        )
        db.add(db_prod)
        db.flush()

        scheme = prod.scheme
        db_scheme = ProposalScheme(
            proposal_id=proposal.id,
            product_id=db_prod.id,
            scheme_type=scheme.scheme_type,
            payment_frequency=scheme.payment_frequency,
            scope_content=scheme.scope_content,
            validity_period=scheme.validity_period,
            economic_conditions=scheme.economic_conditions,
            payment_terms=scheme.payment_terms,
            excluded_services=scheme.excluded_services,
            ip_section=scheme.ip_section,
        )
        db.add(db_scheme)

    db.commit()
    db.refresh(proposal)
    return proposal


@router.get("/", response_model=List[ProposalRead])
def list_proposals(
    skip: int = 0,
    limit: int = 50,
    status: Optional[ProposalStatus] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lista propuestas con filtros opcionales por estado y búsqueda de texto."""
    query = db.query(Proposal).outerjoin(Proposal.client)

    if status is not None:
        query = query.filter(Proposal.status == status)

    if q:
        term = f"%{q}%"
        query = query.filter(
            or_(
                Proposal.title.ilike(term),
                Proposal.code.ilike(term),
                Client.entity.ilike(term),
                Client.name.ilike(term),
            )
        )

    return query.order_by(Proposal.updated_at.desc()).offset(skip).limit(limit).all()


@router.get("/stats", response_model=Dict[str, int])
def get_proposal_stats(db: Session = Depends(get_db)):
    """Returns proposal counts grouped by status."""
    rows = (
        db.query(Proposal.status, func.count(Proposal.id))
        .group_by(Proposal.status)
        .all()
    )
    result: Dict[str, int] = {s.value: 0 for s in ProposalStatus}
    for row_status, count in rows:
        key = row_status.value if hasattr(row_status, "value") else str(row_status)
        result[key] = count
    return result


@router.get("/{proposal_id}", response_model=ProposalRead)
def get_proposal(proposal_id: int, db: Session = Depends(get_db)):
    """Obtiene una propuesta por ID."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Propuesta {proposal_id} no encontrada",
        )
    return proposal


@router.patch("/{proposal_id}", response_model=ProposalRead)
def update_proposal(
    proposal_id: int, data: ProposalUpdate, db: Session = Depends(get_db)
):
    """Actualiza el contenido editable de una propuesta."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Propuesta {proposal_id} no encontrada",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(proposal, field, value)

    db.commit()
    db.refresh(proposal)
    return proposal


@router.delete("/{proposal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proposal(proposal_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_creator)):
    """Elimina una propuesta."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Propuesta {proposal_id} no encontrada",
        )
    if proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Solo se pueden eliminar propuestas en estado DRAFT. Estado actual: {proposal.status}",
        )
    db.delete(proposal)
    db.commit()


@router.post("/{proposal_id}/products", response_model=ProposalProductRead)
def add_proposal_product(
    proposal_id: int,
    data: ProposalProductCreate,
    db: Session = Depends(get_db),
    portfolio_svc=Depends(get_portfolio_service),
):
    """Agrega un producto (con su esquema propio) a la propuesta."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Propuesta {proposal_id} no encontrada",
        )

    if proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden agregar productos a propuestas en estado DRAFT",
        )

    _validate_product_scheme(data, portfolio_svc)

    db_product = ProposalProduct(
        proposal_id=proposal_id,
        product_name=data.product_name,
        product_type=data.product_type,
        description=data.description,
        category=data.category,
    )
    db.add(db_product)
    db.flush()

    db_scheme = ProposalScheme(
        proposal_id=proposal_id,
        product_id=db_product.id,
        scheme_type=data.scheme.scheme_type,
        payment_frequency=data.scheme.payment_frequency,
        scope_content=data.scheme.scope_content,
        validity_period=data.scheme.validity_period,
        economic_conditions=data.scheme.economic_conditions,
        payment_terms=data.scheme.payment_terms,
        excluded_services=data.scheme.excluded_services,
        ip_section=data.scheme.ip_section,
    )
    db.add(db_scheme)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{proposal_id}/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_proposal_product(
    proposal_id: int, product_id: int, db: Session = Depends(get_db)
):
    """Remueve un producto de la propuesta."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Propuesta {proposal_id} no encontrada",
        )

    if proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden remover productos de propuestas en estado DRAFT",
        )

    product = db.query(ProposalProduct).filter(
        ProposalProduct.id == product_id,
        ProposalProduct.proposal_id == proposal_id
    ).first()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Producto {product_id} no encontrado en la propuesta {proposal_id}",
        )

    # El esquema vinculado al producto se elimina junto con él
    db.query(ProposalScheme).filter(ProposalScheme.product_id == product_id).delete()
    db.delete(product)
    db.commit()


@router.patch("/{proposal_id}/schemes/{scheme_id}", response_model=ProposalSchemeRead)
def update_proposal_scheme(
    proposal_id: int,
    scheme_id: int,
    data: ProposalSchemeUpdate,
    db: Session = Depends(get_db),
):
    """Actualiza el contenido editable de un esquema de una propuesta."""
    scheme = (
        db.query(ProposalScheme)
        .filter(
            ProposalScheme.id == scheme_id,
            ProposalScheme.proposal_id == proposal_id,
        )
        .first()
    )
    if not scheme:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Esquema {scheme_id} no encontrado en la propuesta {proposal_id}",
        )

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scheme, field, value)

    db.commit()
    db.refresh(scheme)
    return scheme


@router.put("/{proposal_id}/products", response_model=List[ProposalProductRead])
def replace_proposal_products(
    proposal_id: int,
    data: List[ProposalProductCreate],
    db: Session = Depends(get_db),
    portfolio_svc=Depends(get_portfolio_service),
):
    """Reemplaza todos los productos de la propuesta (cada uno con su esquema)."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Propuesta {proposal_id} no encontrada",
        )

    if proposal.status != ProposalStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Solo se pueden modificar productos de propuestas en estado DRAFT",
        )

    for item in data:
        _validate_product_scheme(item, portfolio_svc)

    # Eliminar productos existentes junto con sus esquemas vinculados
    # (los esquemas legados con product_id NULL no se tocan)
    old_product_ids = [
        pid for (pid,) in db.query(ProposalProduct.id)
        .filter(ProposalProduct.proposal_id == proposal_id)
        .all()
    ]
    if old_product_ids:
        db.query(ProposalScheme).filter(
            ProposalScheme.product_id.in_(old_product_ids)
        ).delete(synchronize_session=False)
    db.query(ProposalProduct).filter(ProposalProduct.proposal_id == proposal_id).delete()

    # Agregar nuevos productos con su esquema
    new_products = []
    for item in data:
        db_product = ProposalProduct(
            proposal_id=proposal_id,
            product_name=item.product_name,
            product_type=item.product_type,
            description=item.description,
            category=item.category,
        )
        db.add(db_product)
        db.flush()
        db.add(ProposalScheme(
            proposal_id=proposal_id,
            product_id=db_product.id,
            scheme_type=item.scheme.scheme_type,
            payment_frequency=item.scheme.payment_frequency,
            scope_content=item.scheme.scope_content,
            validity_period=item.scheme.validity_period,
            economic_conditions=item.scheme.economic_conditions,
            payment_terms=item.scheme.payment_terms,
            excluded_services=item.scheme.excluded_services,
            ip_section=item.scheme.ip_section,
        ))
        new_products.append(db_product)

    db.commit()
    for prod in new_products:
        db.refresh(prod)

    return new_products

