"""
Tests del servicio proposal_content_resolver.

El resolver es el punto único donde se decide qué contenido va a cada documento.
Cubre dos contratos críticos:
  - Modo separado: cada esquema produce su propio dict completo (resolve_scheme_content).
  - Modo combinado: la propuesta produce un dict con N entradas por esquema (resolve_combined_content).

Reglas de negocio validadas (origen: PDF de la reunión):
  - La propiedad intelectual varía por tipo de esquema.
  - SaaS (services) NO debe mostrar la sección de servicios excluidos.
  - Cuando los campos por esquema están vacíos, se aplican defaults del DocumentGenerator.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.services.document_generator import DocumentGenerator
from app.services.proposal_content_resolver import (
    resolve_combined_content,
    resolve_scheme_content,
)


def _proposal(client_entity: str = "Consorcio ITS Medellín", schemes=None):
    """Construye un mock mínimo de Proposal con un cliente (modo legado)."""
    proposal = MagicMock()
    proposal.client = MagicMock()
    proposal.client.entity = client_entity
    proposal.context_content = "<p>Contexto global</p>"
    proposal.letter_content = "<p>Carta global</p>"
    proposal.schemes = schemes or []
    # Por defecto se comporta como propuesta legada (bloques por esquema)
    proposal.uses_product_schemes = False
    proposal.products = []
    return proposal


def _scheme(
    scheme_type: str,
    *,
    scope: str | None = None,
    validity: str | None = None,
    economic: str | None = None,
    payment: str | None = None,
    excluded=None,
    ip: str | None = None,
    scheme_id: int = 1,
):
    s = MagicMock()
    s.id = scheme_id
    s.scheme_type.value = scheme_type
    s.payment_frequency = "unico"
    s.scope_content = scope
    s.validity_period = validity
    s.economic_conditions = economic
    s.payment_terms = payment
    s.excluded_services = excluded
    s.ip_section = ip
    return s


# ---------------------------------------------------------------------------
# resolve_scheme_content
# ---------------------------------------------------------------------------

def test_returns_global_fields_from_proposal():
    """context_text y letter_text deben provenir de Proposal (campos globales)."""
    scheme = _scheme("licensing", scope="<p>Mi alcance</p>")
    content = resolve_scheme_content(_proposal(schemes=[scheme]), scheme)

    assert content["context_text"] == "<p>Contexto global</p>"
    assert content["letter_text"] == "<p>Carta global</p>"
    assert content["scope_text"] == "<p>Mi alcance</p>"


def test_saas_default_excluded_is_empty_string():
    """SaaS (services): si excluded está vacío en BD, el resolver devuelve "" para que
    la sección de Servicios Excluidos NO se renderice en el documento.
    """
    scheme = _scheme("services", excluded=None)
    content = resolve_scheme_content(_proposal(schemes=[scheme]), scheme)

    assert content["excluded_services_text"] == ""


def test_licensing_default_excluded_renders_list():
    """Licensing: si excluded está vacío en BD, el resolver devuelve la lista por defecto."""
    scheme = _scheme("licensing", excluded=None)
    content = resolve_scheme_content(_proposal(schemes=[scheme]), scheme)

    html = content["excluded_services_text"]
    assert "<ul>" in html
    # El primer ítem por defecto habla de "Infraestructura"
    assert "Infraestructura tecnológica" in html


def test_support_maintenance_default_excluded_renders_list():
    """Support: igual que licensing, debe traer la lista completa por defecto."""
    scheme = _scheme("support_maintenance", excluded=None)
    content = resolve_scheme_content(_proposal(schemes=[scheme]), scheme)

    assert "<ul>" in content["excluded_services_text"]
    assert "Infraestructura tecnológica" in content["excluded_services_text"]


def test_user_override_excluded_takes_precedence():
    """Si el usuario edita excluded_services, ese contenido se devuelve tal cual."""
    scheme = _scheme("services", excluded="<p>Solo lo que YO digo</p>")
    content = resolve_scheme_content(_proposal(schemes=[scheme]), scheme)

    assert content["excluded_services_text"] == "<p>Solo lo que YO digo</p>"


def test_ip_default_differs_by_scheme_type():
    """El default de propiedad intelectual cambia según el tipo de esquema.

    El PDF de la reunión es explícito: "la propiedad intelectual cambia
    dependiendo del esquema".
    """
    licensing_ip = resolve_scheme_content(
        _proposal(schemes=[_scheme("licensing")]),
        _scheme("licensing"),
    )["ip_section_text"]
    services_ip = resolve_scheme_content(
        _proposal(schemes=[_scheme("services")]),
        _scheme("services"),
    )["ip_section_text"]
    support_ip = resolve_scheme_content(
        _proposal(schemes=[_scheme("support_maintenance")]),
        _scheme("support_maintenance"),
    )["ip_section_text"]

    # Los 3 son diferentes
    assert licensing_ip != services_ip
    assert services_ip != support_ip
    assert licensing_ip != support_ip
    # Cada uno menciona la entidad del cliente
    assert "Consorcio ITS Medellín" in licensing_ip
    assert "Consorcio ITS Medellín" in services_ip
    assert "Consorcio ITS Medellín" in support_ip


def test_user_override_ip_takes_precedence():
    """Si el usuario edita ip_section en el esquema, se respeta sin aplicar default."""
    scheme = _scheme("licensing", ip="<p>IP personalizada</p>")
    content = resolve_scheme_content(_proposal(schemes=[scheme]), scheme)

    assert content["ip_section_text"] == "<p>IP personalizada</p>"


def test_validity_default_when_empty():
    """Si validity_period está vacío, se aplica DEFAULT_VALIDITY_TEXT."""
    scheme = _scheme("licensing", validity=None)
    content = resolve_scheme_content(_proposal(schemes=[scheme]), scheme)

    assert DocumentGenerator.DEFAULT_VALIDITY_TEXT in content["validity_period"]


# ---------------------------------------------------------------------------
# resolve_combined_content
# ---------------------------------------------------------------------------

def test_combined_payload_has_one_entry_per_scheme():
    """resolve_combined_content devuelve una entrada por esquema, preservando orden."""
    schemes = [
        _scheme("licensing", scheme_id=1, scope="<p>Alcance L</p>"),
        _scheme("services", scheme_id=2, scope="<p>Alcance S</p>"),
        _scheme("support_maintenance", scheme_id=3, scope="<p>Alcance M</p>"),
    ]
    payload = resolve_combined_content(_proposal(schemes=schemes))

    assert len(payload["schemes"]) == 3
    assert payload["schemes"][0]["scheme_type"] == "licensing"
    assert payload["schemes"][1]["scheme_type"] == "services"
    assert payload["schemes"][2]["scheme_type"] == "support_maintenance"
    assert payload["schemes"][0]["scope_text"] == "<p>Alcance L</p>"
    assert payload["schemes"][1]["scope_text"] == "<p>Alcance S</p>"


def test_combined_payload_differentiates_ip_per_scheme():
    """En el modo combinado, cada esquema trae su IP — no se duplica."""
    schemes = [_scheme("licensing", scheme_id=1), _scheme("services", scheme_id=2)]
    payload = resolve_combined_content(_proposal(schemes=schemes))

    ip_licensing = payload["schemes"][0]["ip_section_text"]
    ip_services = payload["schemes"][1]["ip_section_text"]
    assert ip_licensing != ip_services


def test_combined_payload_differentiates_excluded_per_scheme():
    """SaaS no muestra exclusiones; licensing sí. En el combinado deben coexistir distintas."""
    schemes = [_scheme("licensing", scheme_id=1), _scheme("services", scheme_id=2)]
    payload = resolve_combined_content(_proposal(schemes=schemes))

    assert "Infraestructura" in payload["schemes"][0]["excluded_services_text"]
    assert payload["schemes"][1]["excluded_services_text"] == ""


def test_combined_payload_global_fields():
    """Los campos globales (contexto, carta) aparecen una sola vez en la raíz del payload."""
    schemes = [_scheme("licensing", scheme_id=1), _scheme("services", scheme_id=2)]
    payload = resolve_combined_content(_proposal(schemes=schemes))

    assert payload["context_text"] == "<p>Contexto global</p>"
    assert payload["letter_text"] == "<p>Carta global</p>"


# ---------------------------------------------------------------------------
# resolve_combined_content — modo por producto (uses_product_schemes)
# ---------------------------------------------------------------------------

def _product(name: str, scheme):
    p = MagicMock()
    p.product_name = name
    p.scheme = scheme
    return p


def test_combined_payload_per_product_blocks_in_product_order():
    """Modelo nuevo: un bloque por producto, en el orden de los productos."""
    lic = _scheme("licensing", scheme_id=1, scope="<p>Alcance L</p>")
    srv = _scheme("services", scheme_id=2, scope="<p>Alcance S</p>")
    proposal = _proposal(schemes=[srv, lic])
    proposal.uses_product_schemes = True
    proposal.products = [_product("Producto A", lic), _product("Producto B", srv)]

    payload = resolve_combined_content(proposal)

    assert [b["product_name"] for b in payload["schemes"]] == ["Producto A", "Producto B"]
    assert payload["schemes"][0]["scheme_type"] == "licensing"
    assert payload["schemes"][1]["scheme_type"] == "services"


def test_combined_payload_same_scheme_type_two_products_two_blocks():
    """Dos productos con el mismo tipo de esquema producen dos bloques distintos."""
    lic_a = _scheme("licensing", scheme_id=1, economic="<p>VALOR-A</p>")
    lic_b = _scheme("licensing", scheme_id=2, economic="<p>VALOR-B</p>")
    proposal = _proposal(schemes=[lic_a, lic_b])
    proposal.uses_product_schemes = True
    proposal.products = [_product("Prod A", lic_a), _product("Prod B", lic_b)]

    payload = resolve_combined_content(proposal)

    assert len(payload["schemes"]) == 2
    assert payload["schemes"][0]["economic_conditions"] == "<p>VALOR-A</p>"
    assert payload["schemes"][1]["economic_conditions"] == "<p>VALOR-B</p>"


def test_combined_payload_legacy_has_no_product_name():
    """Modo legado: los bloques no llevan product_name (bloques por esquema)."""
    schemes = [_scheme("licensing", scheme_id=1)]
    payload = resolve_combined_content(_proposal(schemes=schemes))

    assert "product_name" not in payload["schemes"][0]
