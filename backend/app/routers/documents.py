"""
Endpoints para generación de documentos Word y PDF.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile

from app.database import get_db
from app.config import get_settings, Settings
from app.models.proposal import Proposal
from app.services.document_generator import DocumentGenerator
from app.services.portfolio_service import PortfolioService
from app.services.innti_service import InntiService, InntiServiceError

router = APIRouter(prefix="/api/proposals", tags=["Documentos"])


@router.post("/{proposal_id}/generate-document")
def generate_document(
    proposal_id: int,
    use_innti: bool = True,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Genera el documento Word de la propuesta.

    Args:
        proposal_id: ID de la propuesta.
        use_innti: Si True, usa Innti para generar texto. Si False, usa plantillas.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    client = proposal.client
    generator = DocumentGenerator()

    # Obtener nombres de productos del portafolio
    portfolio = PortfolioService(settings.portfolio_file_path)
    product_names = [p.product_name for p in proposal.products]
    portfolio_products = portfolio.get_by_names(product_names)

    # Generar texto con Innti o usar valores por defecto
    context_text = proposal.context_content or ""
    scope_text = proposal.scope_content or ""
    letter_text = proposal.letter_content or ""

    if use_innti and not context_text:
        try:
            innti = InntiService()
            context_text = innti.generate_context_section(
                client.entity, proposal.title
            )
            scope_text = innti.generate_scope_section(
                product_names,
                ", ".join(s.scheme_type.value for s in proposal.schemes),
            )
            letter_text = innti.generate_cover_letter(
                client.name,
                client.position or "",
                client.entity,
                proposal.title,
            )
            # Guardar contenido generado en la propuesta
            proposal.context_content = context_text
            proposal.scope_content = scope_text
            proposal.letter_content = letter_text
            db.commit()
        except InntiServiceError:
            # Fallback: continuar sin texto generado por IA
            pass

    scheme_types = [s.scheme_type.value for s in proposal.schemes]

    doc = generator.generate_proposal_docx(
        title=proposal.cover_title or proposal.title,
        client_name=client.name,
        client_position=client.position or "",
        client_entity=client.entity,
        client_city=client.city or "Bogotá",
        scheme_types=scheme_types,
        products=portfolio_products,
        context_text=context_text,
        scope_text=scope_text,
        letter_text=letter_text,
        economic_conditions=proposal.economic_conditions,
        payment_terms=proposal.payment_terms,
    )

    # Guardar en archivo temporal
    output_dir = Path(tempfile.gettempdir()) / "innti_docs"
    output_dir.mkdir(exist_ok=True)
    filename = f"propuesta_{proposal_id}.docx"
    output_path = output_dir / filename
    generator.save_document(doc, str(output_path))

    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@router.post("/{proposal_id}/generate-annex")
def generate_technical_annex(
    proposal_id: int,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Genera el anexo técnico de la propuesta."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    portfolio = PortfolioService(settings.portfolio_file_path)
    product_names = [p.product_name for p in proposal.products]
    portfolio_products = portfolio.get_by_names(product_names)

    generator = DocumentGenerator()
    doc = generator.generate_technical_annex(portfolio_products)

    output_dir = Path(tempfile.gettempdir()) / "innti_docs"
    output_dir.mkdir(exist_ok=True)
    filename = f"anexo_tecnico_{proposal_id}.docx"
    output_path = output_dir / filename
    generator.save_document(doc, str(output_path))

    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
