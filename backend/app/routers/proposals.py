"""
Endpoints CRUD para propuestas comerciales.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.proposal import (
    Proposal, ProposalProduct, ProposalScheme, ProposalStatus, SchemeType, MVP_SCHEME_TYPES
)
from app.models.client import Client
from app.schemas.proposal import (
    ProposalCreate, ProposalRead, ProposalUpdate, ProposalProductCreate, ProposalProductRead
)

router = APIRouter(prefix="/api/proposals", tags=["Propuestas"])


@router.post("/", response_model=ProposalRead, status_code=status.HTTP_201_CREATED)
def create_proposal(data: ProposalCreate, db: Session = Depends(get_db)):
    """Crea una nueva propuesta comercial."""
    # Validar esquemas MVP
    for scheme in data.schemes:
        if scheme.scheme_type not in MVP_SCHEME_TYPES:
            raise HTTPException(
                status_code=422,  # HTTP 422 Unprocessable Content (deprecó UNPROCESSABLE_ENTITY)
                detail=f"El esquema '{scheme.scheme_type}' no está disponible en el MVP. "
                       f"Esquemas válidos: licensing, services, support_maintenance"
            )

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

    # Agregar productos
    for prod in data.products:
        db_prod = ProposalProduct(
            proposal_id=proposal.id,
            product_name=prod.product_name,
            product_type=prod.product_type,
            description=prod.description,
            category=prod.category,
        )
        db.add(db_prod)

    # Agregar esquemas
    for scheme in data.schemes:
        db_scheme = ProposalScheme(
            proposal_id=proposal.id,
            scheme_type=scheme.scheme_type,
            payment_frequency=scheme.payment_frequency,
        )
        db.add(db_scheme)

    db.commit()
    db.refresh(proposal)
    return proposal


@router.get("/", response_model=List[ProposalRead])
def list_proposals(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_db)
):
    """Lista todas las propuestas."""
    proposals = (
        db.query(Proposal)
        .order_by(Proposal.updated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return proposals


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
def delete_proposal(proposal_id: int, db: Session = Depends(get_db)):
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
    proposal_id: int, data: ProposalProductCreate, db: Session = Depends(get_db)
):
    """Agrega un producto a la propuesta."""
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

    db_product = ProposalProduct(
        proposal_id=proposal_id,
        product_name=data.product_name,
        product_type=data.product_type,
        description=data.description,
        category=data.category,
    )
    db.add(db_product)
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

    db.delete(product)
    db.commit()


@router.put("/{proposal_id}/products", response_model=List[ProposalProductRead])
def replace_proposal_products(
    proposal_id: int, data: List[ProposalProductCreate], db: Session = Depends(get_db)
):
    """Reemplaza todos los productos de la propuesta."""
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

    # Eliminar productos existentes
    db.query(ProposalProduct).filter(ProposalProduct.proposal_id == proposal_id).delete()

    # Agregar nuevos productos
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
        new_products.append(db_product)

    db.commit()
    for prod in new_products:
        db.refresh(prod)

    return new_products

