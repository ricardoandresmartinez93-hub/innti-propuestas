"""
Endpoints para generación de documentos Word y PDF.

El contenido de la propuesta se resuelve por esquema vía
``proposal_content_resolver`` — cada ``ProposalScheme`` tiene su propio
alcance, plazo, condiciones económicas, forma de pago, servicios excluidos y
propiedad intelectual.

Modo combinado (``combine_schemes=True``): un único Word con N bloques
"ESQUEMA: …" donde cada uno trae sus secciones.

Modo separado (``combine_schemes=False`` y >= 2 esquemas): un .docx por
esquema, empaquetados en ZIP.
"""
import logging
import uuid
import zipfile
from fastapi import APIRouter, Depends, HTTPException, status

log = logging.getLogger(__name__)
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from app.database import get_db
from app.config import get_settings, Settings
from app.models.proposal import Proposal, ProposalScheme
from app.services.document_generator import DocumentGenerator
from app.services.portfolio_service import PortfolioService
from app.services.innti_service import InntiService, InntiServiceError
from app.services.proposal_content_resolver import (
    resolve_scheme_content,
    resolve_combined_content,
)

router = APIRouter(prefix="/api/proposals", tags=["Documentos"])

DOCX_MEDIA_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)

SCHEME_LABEL = {
    "licensing": "licenciamiento",
    "services": "servicios",
    "support_maintenance": "soporte_mantenimiento",
}


def _cover_letter_fallback(
    client_name: str,
    client_position: str,
    client_entity: str,
    proposal_title: str,
) -> str:
    """Template HTML para la carta de presentación cuando Innti falla."""
    position_part = f", {client_position}" if client_position else ""
    return (
        f"<p>Estimado(a) señor(a) <strong>{client_name}</strong>{position_part},</p>"
        f"<p>Por medio de la presente, Quipux S.A.S. tiene el agrado de presentar a "
        f"<strong>{client_entity}</strong> la propuesta comercial denominada "
        f'<strong>"{proposal_title}"</strong>, elaborada con el propósito de apoyar '
        f"sus objetivos de transformación digital y contribuir a la modernización de la "
        f"gestión pública de manera eficiente y sostenible.</p>"
        f"<p>En Quipux S.A.S. nos comprometemos con los más altos estándares de innovación "
        f"y excelentes niveles de servicio. La propuesta que ponemos a su consideración ha "
        f"sido ajustada a las expectativas del proyecto y refleja nuestra experiencia y "
        f"capacidad técnica para acompañar a su institución en este proceso.</p>"
        f"<p>Quedamos atentos a sus comentarios y a disposición para cualquier ampliación "
        f"de la información contenida en este documento.</p>"
        f"<p>Cordialmente,</p>"
        f"<p><strong>Juan Pablo Ramírez Madrid</strong><br/>"
        f"Vicepresidente de Nuevos Negocios<br/>"
        f"Quipux S.A.S.</p>"
    )


def _get_output_dir() -> Path:
    output_dir = Path(tempfile.gettempdir()) / "innti_docs"
    output_dir.mkdir(exist_ok=True)
    return output_dir


# ---------------------------------------------------------------------------
# Generación de contenido con Innti
# ---------------------------------------------------------------------------

def _generate_global_content_with_innti(proposal: Proposal, db: Session) -> None:
    """Genera contenido GLOBAL (carta y contexto) con Innti y lo persiste.

    No toca contenido por esquema; eso lo hace ``_generate_scheme_content_with_innti``.
    """
    innti = InntiService()
    client = proposal.client

    with ThreadPoolExecutor(max_workers=2) as pool:
        ctx_future = pool.submit(
            innti.generate_context_section, client.entity, proposal.title
        )
        letter_future = pool.submit(
            innti.generate_cover_letter,
            client.name, client.position or "", client.entity, proposal.title,
        )

        try:
            proposal.context_content = ctx_future.result()
        except InntiServiceError as e:
            log.warning("Innti [context]: %s", e)

        try:
            letter = letter_future.result()
            if letter:
                proposal.letter_content = letter
            else:
                log.warning("Innti [letter]: returned empty — using fallback")
                proposal.letter_content = _cover_letter_fallback(
                    client.name, client.position or "", client.entity, proposal.title
                )
        except InntiServiceError as e:
            log.warning("Innti [letter]: %s — using fallback", e)
            proposal.letter_content = _cover_letter_fallback(
                client.name, client.position or "", client.entity, proposal.title
            )

    db.commit()


def _generate_scheme_content_with_innti(
    proposal: Proposal, scheme: ProposalScheme, product_names: list[str], db: Session
) -> None:
    """Genera contenido POR ESQUEMA (alcance, plazo, condiciones, pago) con Innti.

    Persiste el resultado en el propio ``ProposalScheme``. Los textos fijos
    (exclusiones, IP) se dejan en blanco para que el resolver aplique los
    defaults por tipo de esquema en tiempo de render.
    """
    innti = InntiService()
    scheme_str = scheme.scheme_type.value if hasattr(scheme.scheme_type, "value") else str(scheme.scheme_type)
    label = SCHEME_LABEL.get(scheme_str, scheme_str)

    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {
            "scope_content": pool.submit(
                innti.generate_scope_section, product_names, scheme_str
            ),
            "validity_period": pool.submit(
                innti.generate_validity_section, scheme_str
            ),
            "economic_conditions": pool.submit(
                innti.generate_economic_conditions_section,
                product_names, scheme_str, label,
            ),
            "payment_terms": pool.submit(
                innti.generate_payment_terms_section, scheme_str
            ),
        }
        for field, future in futures.items():
            try:
                setattr(scheme, field, future.result())
            except InntiServiceError as e:
                log.warning("Innti [%s/%s]: %s", scheme_str, field, e)

    db.commit()


def _ensure_content_ready(
    proposal: Proposal,
    use_innti: bool,
    db: Session,
) -> None:
    """Si ``use_innti=True``, genera todo el contenido faltante y lo persiste."""
    if not use_innti:
        return

    _generate_global_content_with_innti(proposal, db)
    product_names = [p.product_name for p in proposal.products]
    for scheme in proposal.schemes:
        _generate_scheme_content_with_innti(proposal, scheme, product_names, db)


# ---------------------------------------------------------------------------
# Generación de archivos
# ---------------------------------------------------------------------------

def _load_portfolio_products(proposal: Proposal, settings: Settings):
    portfolio = PortfolioService(settings.portfolio_file_path)
    product_names = [p.product_name for p in proposal.products]
    portfolio_products = portfolio.get_by_names(product_names)
    category_map = {p.product_name.lower(): p.category or "" for p in proposal.products}
    for pp in portfolio_products:
        pp.category = category_map.get(pp.name.lower(), "")
    return portfolio_products


def _build_combined_docx(
    proposal_id: int,
    use_innti: bool,
    db: Session,
    settings: Settings,
) -> Path:
    """Genera un único Word con todos los esquemas combinados (combine_schemes=True)."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    _ensure_content_ready(proposal, use_innti, db)

    portfolio_products = _load_portfolio_products(proposal, settings)
    combined = resolve_combined_content(proposal)
    client = proposal.client

    generator = DocumentGenerator()
    doc = generator.generate_combined_proposal_docx(
        title=proposal.cover_title or proposal.title,
        client_name=client.name,
        client_position=client.position or "",
        client_entity=client.entity,
        client_city=client.city or "Bogotá",
        products=portfolio_products,
        context_text=combined["context_text"],
        letter_text=combined["letter_text"],
        schemes_payload=combined["schemes"],
    )

    uid = uuid.uuid4().hex[:8]
    output_path = _get_output_dir() / f"propuesta_{proposal_id}_{uid}.docx"
    generator.save_document(doc, str(output_path))
    return output_path


def _build_separate_docx_files(
    proposal_id: int,
    use_innti: bool,
    db: Session,
    settings: Settings,
) -> list[Path]:
    """Genera un .docx por esquema con su contenido específico (combine_schemes=False)."""
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    _ensure_content_ready(proposal, use_innti, db)

    portfolio_products = _load_portfolio_products(proposal, settings)
    client = proposal.client
    output_dir = _get_output_dir()
    generator = DocumentGenerator()
    paths: list[Path] = []

    for scheme in proposal.schemes:
        scheme_str = scheme.scheme_type.value if hasattr(scheme.scheme_type, "value") else str(scheme.scheme_type)
        label = SCHEME_LABEL.get(scheme_str, scheme_str)
        content = resolve_scheme_content(proposal, scheme)

        doc = generator.generate_proposal_docx(
            title=proposal.cover_title or proposal.title,
            client_name=client.name,
            client_position=client.position or "",
            client_entity=client.entity,
            client_city=client.city or "Bogotá",
            scheme_types=[scheme_str],
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

        uid = uuid.uuid4().hex[:8]
        output_path = output_dir / f"propuesta_{proposal_id}_{label}_{uid}.docx"
        generator.save_document(doc, str(output_path))
        paths.append(output_path)

    return paths


def _pack_zip(file_paths: list[Path], zip_path: Path) -> Path:
    """Empaqueta una lista de archivos en un ZIP."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fp in file_paths:
            zf.write(fp, arcname=fp.name)
    return zip_path


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/{proposal_id}/generate-document")
def generate_document(
    proposal_id: int,
    use_innti: bool = True,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
):
    """Genera el documento Word de la propuesta.

    Si la propuesta tiene combine_schemes=False y más de un esquema, devuelve un ZIP
    con un .docx por esquema. En caso contrario devuelve un único .docx.
    """
    proposal = db.query(Proposal).filter(Proposal.id == proposal_id).first()
    if not proposal:
        raise HTTPException(status_code=404, detail="Propuesta no encontrada")

    if not proposal.combine_schemes and len(proposal.schemes) > 1:
        paths = _build_separate_docx_files(proposal_id, use_innti, db, settings)
        zip_path = _get_output_dir() / f"propuesta_{proposal_id}_documentos_{uuid.uuid4().hex[:8]}.zip"
        _pack_zip(paths, zip_path)
        return FileResponse(
            path=str(zip_path),
            filename=zip_path.name,
            media_type="application/zip",
        )

    output_path = _build_combined_docx(proposal_id, use_innti, db, settings)
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
    """Genera la propuesta en formato PDF.

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

        zip_path = _get_output_dir() / f"propuesta_{proposal_id}_pdfs_{uuid.uuid4().hex[:8]}.zip"
        _pack_zip(pdf_paths, zip_path)
        return FileResponse(
            path=str(zip_path),
            filename=zip_path.name,
            media_type="application/zip",
        )

    docx_path = _build_combined_docx(proposal_id, use_innti, db, settings)
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
    filename = f"anexo_tecnico_{proposal_id}_{uuid.uuid4().hex[:8]}.docx"
    output_path = output_dir / filename
    generator.save_document(doc, str(output_path))

    return FileResponse(
        path=str(output_path),
        filename=filename,
        media_type=DOCX_MEDIA_TYPE,
    )
