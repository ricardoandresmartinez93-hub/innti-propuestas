"""
Endpoints para generación de documentos Word y PDF.
"""
import zipfile
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
from typing import Optional

from app.database import get_db
from app.config import get_settings, Settings
from app.models.proposal import Proposal
from app.services.document_generator import DocumentGenerator
from app.services.portfolio_service import PortfolioService
from app.services.innti_service import InntiService, InntiServiceError

router = APIRouter(prefix="/api/proposals", tags=["Documentos"])

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

SCHEME_LABEL = {
    "licensing": "licenciamiento",
    "services": "servicios",
    "support_maintenance": "soporte_mantenimiento",
}


def _get_output_dir() -> Path:
    output_dir = Path(tempfile.gettempdir()) / "innti_docs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


def _prepare_proposal_content(
    proposal: Proposal,
    use_innti: bool,
    db: Session,
) -> dict:
    """
    Resuelve el contenido textual de la propuesta.
    Si use_innti=True intenta generar con Innti y persiste el resultado.
    Siempre devuelve un dict con las claves de texto.
    """
    client = proposal.client
    product_names = [p.product_name for p in proposal.products]

    content = {
        "context_text": proposal.context_content or "",
        "scope_text": proposal.scope_content or "",
        "letter_text": proposal.letter_content or "",
        "excluded_services_text": proposal.excluded_services or "",
        "ip_section_text": proposal.ip_section or "",
        "validity_period": proposal.validity_period,
        "economic_conditions": proposal.economic_conditions,
        "payment_terms": proposal.payment_terms,
    }

    if use_innti:
        try:
            innti = InntiService()
            scheme_type_str = ", ".join(s.scheme_type.value for s in proposal.schemes)

            content["context_text"] = innti.generate_context_section(
                client.entity, proposal.title
            )
            content["scope_text"] = innti.generate_scope_section(
                product_names, scheme_type_str
            )
            content["letter_text"] = innti.generate_cover_letter(
                client.name,
                client.position or "",
                client.entity,
                proposal.title,
            )
            content["validity_period"] = innti.generate_validity_section(scheme_type_str)
            content["economic_conditions"] = innti.generate_economic_conditions_section(
                product_names,
                scheme_type_str,
                " / ".join(s.scheme_type.value for s in proposal.schemes),
            )
            content["payment_terms"] = innti.generate_payment_terms_section(scheme_type_str)
            excluded = innti.generate_excluded_services_section()
            ip_sec = innti.generate_ip_section(client.entity)
            content["excluded_services_text"] = excluded
            content["ip_section_text"] = ip_sec

            proposal.context_content = content["context_text"]
            proposal.scope_content = content["scope_text"]
            proposal.letter_content = content["letter_text"]
            proposal.validity_period = content["validity_period"]
            proposal.economic_conditions = content["economic_conditions"]
            proposal.payment_terms = content["payment_terms"]
            proposal.excluded_services = excluded
            proposal.ip_section = ip_sec
            db.commit()

        except InntiServiceError:
            pass  # Fallback: usar valores ya en content

    return content


def _generate_single_docx(
    proposal: Proposal,
    content: dict,
    generator: DocumentGenerator,
    portfolio_products,
    scheme_types: list[str],
    output_path: Path,
) -> Path:
    """Genera un .docx para los scheme_types dados y lo guarda en output_path."""
    client = proposal.client
    doc = generator.generate_proposal_docx(
        title=proposal.cover_title or proposal.title,
        client_name=client.name,
        client_position=client.position or "",
        client_entity=client.entity,
        client_city=client.city or "Bogotá",
        scheme_types=scheme_types,
        products=portfolio_products,
        context_text=content["context_text"],
        scope_text=content["scope_text"],
        letter_text=content["letter_text"],
        validity_period=content["validity_period"],
        economic_conditions=content["economic_conditions"],
        payment_terms=content["payment_terms"],
        excluded_services=content["excluded_services_text"],
        ip_section=content["ip_section_text"],
    )
    generator.save_document(doc, str(output_path))
    return output_path


def _build_proposal_docx(
    proposal_id: int,
    use_innti: bool,
    db: Session,
    settings: Settings,
) -> Path:
    """
    Construye el documento Word combinado y lo guarda en un archivo temporal.

    Returns:
        Ruta del archivo .docx generado.

    Raises:
        HTTPException 404 si la propuesta no existe.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    portfolio = PortfolioService(settings.portfolio_file_path)
    product_names = [p.product_name for p in proposal.products]
    portfolio_products = portfolio.get_by_names(product_names)

    category_map = {p.product_name.lower(): p.category or "" for p in proposal.products}
    for pp in portfolio_products:
        pp.category = category_map.get(pp.name.lower(), "")

    content = _prepare_proposal_content(proposal, use_innti, db)
    scheme_types = [s.scheme_type.value for s in proposal.schemes]

    output_path = _get_output_dir() / f"propuesta_{proposal_id}.docx"
    return _generate_single_docx(
        proposal, content, DocumentGenerator(), portfolio_products, scheme_types, output_path
    )


def _build_separate_docx_files(
    proposal_id: int,
    use_innti: bool,
    db: Session,
    settings: Settings,
) -> list[Path]:
    """
    Genera un .docx por esquema.

    Cuando use_innti=True, las secciones compartidas (contexto, alcance, carta,
    servicios excluidos, propiedad intelectual) se generan una sola vez.
    Las secciones que dependen del tipo de pago (plazo, condiciones económicas,
    forma de pago) se generan individualmente por esquema para que cada documento
    refleje correctamente su propia frecuencia de pago.

    Returns:
        Lista de rutas de archivos .docx generados.

    Raises:
        HTTPException 404 si la propuesta no existe.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    portfolio = PortfolioService(settings.portfolio_file_path)
    product_names = [p.product_name for p in proposal.products]
    portfolio_products = portfolio.get_by_names(product_names)

    category_map = {p.product_name.lower(): p.category or "" for p in proposal.products}
    for pp in portfolio_products:
        pp.category = category_map.get(pp.name.lower(), "")

    # Contenido base: las secciones compartidas son correctas para todos los esquemas.
    # Si use_innti=True, las secciones específicas de esquema (plazo, condiciones
    # económicas, forma de pago) se sobreescriben por esquema en el loop a continuación.
    base_content = _prepare_proposal_content(proposal, use_innti, db)

    output_dir = _get_output_dir()
    generator = DocumentGenerator()
    paths: list[Path] = []

    for scheme in proposal.schemes:
        scheme_str = scheme.scheme_type.value
        label = SCHEME_LABEL.get(scheme_str, scheme_str)

        # Clonar el contenido base y sobreescribir las secciones dependientes del esquema
        content = dict(base_content)

        if use_innti:
            try:
                innti = InntiService()
                content["validity_period"] = innti.generate_validity_section(scheme_str)
                content["economic_conditions"] = innti.generate_economic_conditions_section(
                    product_names, scheme_str, label
                )
                content["payment_terms"] = innti.generate_payment_terms_section(scheme_str)
            except InntiServiceError:
                pass  # Fallback: mantener el contenido combinado del base_content

        filename = f"propuesta_{proposal_id}_{label}.docx"
        output_path = output_dir / filename
        _generate_single_docx(
            proposal, content, generator, portfolio_products,
            [scheme_str], output_path
        )
        paths.append(output_path)

    return paths


def _pack_zip(file_paths: list[Path], zip_path: Path) -> Path:
    """Empaqueta una lista de archivos en un ZIP."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            zf.write(fp, arcname=fp.name)
    return zip_path


@router.post("/{proposal_id}/generate-document")
def generate_document(
    proposal_id: int,
    use_innti: bool = True,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Genera el documento Word de la propuesta.
    Si la propuesta tiene combine_schemes=False y más de un esquema, devuelve un ZIP
    con un .docx por esquema. En caso contrario devuelve un único .docx.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    if not proposal.combine_schemes and len(proposal.schemes) > 1:
        paths = _build_separate_docx_files(proposal_id, use_innti, db, settings)
        zip_path = _get_output_dir() / f"propuesta_{proposal_id}_documentos.zip"
        _pack_zip(paths, zip_path)
        return FileResponse(
            path=str(zip_path),
            filename=zip_path.name,
            media_type="application/zip",
        )

    output_path = _build_proposal_docx(proposal_id, use_innti, db, settings)
    return FileResponse(
        path=str(output_path),
        filename=output_path.name,
        media_type=DOCX_MEDIA_TYPE,
    )


@router.post("/{proposal_id}/generate-pdf")
def generate_pdf(
    proposal_id: int,
    use_innti: bool = True,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """
    Genera la propuesta en formato PDF.
    Si combine_schemes=False y más de un esquema, devuelve un ZIP con un PDF por esquema.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    generator = DocumentGenerator()

    if not proposal.combine_schemes and len(proposal.schemes) > 1:
        docx_paths = _build_separate_docx_files(proposal_id, use_innti, db, settings)
        pdf_paths: list[Path] = []
        for docx_path in docx_paths:
            pdf_path = docx_path.with_suffix(".pdf")
            try:
                generator.convert_docx_to_pdf(str(docx_path), str(pdf_path))
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"No se pudo generar el PDF para {docx_path.stem}: {e}",
                )
            pdf_paths.append(pdf_path)

        zip_path = _get_output_dir() / f"propuesta_{proposal_id}_pdfs.zip"
        _pack_zip(pdf_paths, zip_path)
        return FileResponse(
            path=str(zip_path),
            filename=zip_path.name,
            media_type="application/zip",
        )

    docx_path = _build_proposal_docx(proposal_id, use_innti, db, settings)
    pdf_path = docx_path.with_suffix(".pdf")
    try:
        generator.convert_docx_to_pdf(str(docx_path), str(pdf_path))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"No se pudo generar el PDF: {e}",
        )

    return FileResponse(
        path=str(pdf_path),
        filename=f"propuesta_{proposal_id}.pdf",
        media_type="application/pdf",
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

    output_dir = _get_output_dir()
    filename = f"anexo_tecnico_{proposal_id}.docx"
    output_path = output_dir / filename
    generator.save_document(doc, str(output_path))

    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type=DOCX_MEDIA_TYPE,
    )
