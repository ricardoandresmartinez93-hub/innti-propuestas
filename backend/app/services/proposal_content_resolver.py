"""
Resolución de contenido efectivo de una propuesta por esquema.

Combina los campos globales de Proposal (carta, contexto, confidencialidad)
con los campos por esquema de ProposalScheme (alcance, plazo, condiciones
económicas, forma de pago, servicios excluidos, propiedad intelectual).

Cuando un campo por esquema viene vacío, se aplica el default correspondiente
del DocumentGenerator (texto fijo, posiblemente variable por tipo de esquema —
ver IP_TEXT_BY_SCHEME y EXCLUDED_SERVICES_BY_SCHEME).
"""
from __future__ import annotations

from typing import Optional

from app.models.proposal import Proposal, ProposalScheme
from app.services.document_generator import DocumentGenerator


def _excluded_services_html(scheme_type: str) -> str:
    """Renderiza la lista de servicios excluidos por defecto como HTML."""
    items = DocumentGenerator.get_excluded_services(scheme_type)
    if not items:
        return ""
    li = "".join(f"<li>{item}</li>" for item in items)
    return f"<ul>{li}</ul>"


def _ip_html(scheme_type: str, client_entity: str) -> str:
    """Renderiza el texto de propiedad intelectual por defecto como HTML."""
    text = DocumentGenerator.get_ip_text(scheme_type)
    return f"<p>{text.format(client_entity=client_entity)}</p>"


def resolve_scheme_content(proposal: Proposal, scheme: ProposalScheme) -> dict:
    """Devuelve el contenido efectivo para generar el documento de un esquema.

    - Los campos globales (context_text, letter_text) provienen de Proposal.
    - Los campos por esquema (scope, validity, economic, payment, excluded, ip)
      provienen de ProposalScheme; si están vacíos se usan defaults del
      DocumentGenerator (algunos varían por tipo de esquema).
    - Para SaaS (services), el default de excluded_services es vacío.
    """
    client_entity = proposal.client.entity if proposal.client else ""
    scheme_type = scheme.scheme_type.value if hasattr(scheme.scheme_type, "value") else str(scheme.scheme_type)

    excluded_default = _excluded_services_html(scheme_type)
    ip_default = _ip_html(scheme_type, client_entity)
    validity_default = f"<p>{DocumentGenerator.DEFAULT_VALIDITY_TEXT}</p>"

    return {
        # Globales (carta y contexto se aplican igual a todos los esquemas)
        "context_text": proposal.context_content or "",
        "letter_text": proposal.letter_content or "",
        # Por esquema (fallback a defaults inteligentes)
        "scope_text": scheme.scope_content or "",
        "validity_period": scheme.validity_period or validity_default,
        "economic_conditions": scheme.economic_conditions or "",
        "payment_terms": scheme.payment_terms or "",
        "excluded_services_text": scheme.excluded_services if scheme.excluded_services is not None else excluded_default,
        "ip_section_text": scheme.ip_section or ip_default,
    }


def _scheme_payload(scheme: ProposalScheme, content: dict) -> dict:
    """Arma el dict de bloque que consume el renderizador combinado."""
    return {
        "scheme_type": scheme.scheme_type.value if hasattr(scheme.scheme_type, "value") else str(scheme.scheme_type),
        "scheme_id": scheme.id,
        "payment_frequency": scheme.payment_frequency,
        "scope_text": content["scope_text"],
        "validity_period": content["validity_period"],
        "economic_conditions": content["economic_conditions"],
        "payment_terms": content["payment_terms"],
        "excluded_services_text": content["excluded_services_text"],
        "ip_section_text": content["ip_section_text"],
    }


def resolve_combined_content(proposal: Proposal) -> dict:
    """Devuelve el contenido para el modo combinado (un único documento).

    Modelo nuevo (uses_product_schemes): un bloque POR PRODUCTO, en el orden de
    los productos de la propuesta; cada bloque incluye "product_name" para que
    el renderizador titule «PRODUCTO — ESQUEMA» y liste solo ese producto.

    Propuestas legadas: un bloque por esquema (sin "product_name"), preservando
    el comportamiento anterior.
    """
    if proposal.uses_product_schemes:
        blocks = []
        for product in proposal.products:
            scheme = product.scheme
            if scheme is None:
                continue
            content = resolve_scheme_content(proposal, scheme)
            payload = _scheme_payload(scheme, content)
            payload["product_name"] = product.product_name
            blocks.append(payload)
    else:
        blocks = [
            _scheme_payload(s, resolve_scheme_content(proposal, s))
            for s in proposal.schemes
        ]

    return {
        # Globales
        "context_text": proposal.context_content or "",
        "letter_text": proposal.letter_content or "",
        # Bloques por producto (modelo nuevo) o por esquema (legado)
        "schemes": blocks,
    }
