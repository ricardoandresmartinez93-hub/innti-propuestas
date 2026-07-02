"""
Tests del vínculo esquema→producto (cambio relacionar-esquemas).

Cubre:
  - Proposal.uses_product_schemes (switch modelo nuevo vs. legado)
  - Relación 1:1 ProposalProduct.scheme
  - Script de migración migrate_schemes_per_product (columna + backfill + idempotencia)
"""
import pytest
from sqlalchemy import create_engine, inspect, text

from app.database import Base
from app.models.client import Client
from app.models.proposal import Proposal, ProposalProduct, ProposalScheme, SchemeType
from scripts.migrate_schemes_per_product import backfill, ensure_product_id_column


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_proposal(db_session, title="Propuesta test") -> Proposal:
    client = Client(name="Cliente", entity="Entidad")
    db_session.add(client)
    db_session.flush()
    proposal = Proposal(title=title, client_id=client.id)
    db_session.add(proposal)
    db_session.flush()
    return proposal


# ── Proposal.uses_product_schemes ────────────────────────────────────────────
def test_uses_product_schemes_true_when_all_linked(db_session):
    """Todos los esquemas con product_id → modelo nuevo."""
    proposal = _make_proposal(db_session)
    product = ProposalProduct(proposal_id=proposal.id, product_name="Prod A")
    db_session.add(product)
    db_session.flush()
    db_session.add(ProposalScheme(
        proposal_id=proposal.id, product_id=product.id, scheme_type=SchemeType.LICENSING,
    ))
    db_session.commit()

    assert proposal.uses_product_schemes is True


def test_uses_product_schemes_false_when_any_unlinked(db_session):
    """Mezcla de esquemas con y sin product_id → se trata como legada."""
    proposal = _make_proposal(db_session)
    product = ProposalProduct(proposal_id=proposal.id, product_name="Prod A")
    db_session.add(product)
    db_session.flush()
    db_session.add(ProposalScheme(
        proposal_id=proposal.id, product_id=product.id, scheme_type=SchemeType.LICENSING,
    ))
    db_session.add(ProposalScheme(
        proposal_id=proposal.id, scheme_type=SchemeType.SERVICES,
    ))
    db_session.commit()

    assert proposal.uses_product_schemes is False


def test_uses_product_schemes_false_without_schemes(db_session):
    """Sin esquemas no hay modelo nuevo que aplicar."""
    proposal = _make_proposal(db_session)
    db_session.commit()

    assert proposal.uses_product_schemes is False


def test_product_scheme_relationship_is_one_to_one(db_session):
    """ProposalProduct.scheme expone el esquema vinculado (uselist=False)."""
    proposal = _make_proposal(db_session)
    product = ProposalProduct(proposal_id=proposal.id, product_name="Prod A")
    db_session.add(product)
    db_session.flush()
    scheme = ProposalScheme(
        proposal_id=proposal.id, product_id=product.id,
        scheme_type=SchemeType.SERVICES, payment_frequency="mensual",
    )
    db_session.add(scheme)
    db_session.commit()
    db_session.refresh(product)

    assert product.scheme is not None
    assert product.scheme.scheme_type == SchemeType.SERVICES
    assert scheme.product.product_name == "Prod A"


# ── Migración: columna + backfill ────────────────────────────────────────────
@pytest.fixture
def migration_engine(tmp_path):
    """Engine SQLite temporal con el schema completo de la app."""
    engine = create_engine(
        f"sqlite:///{tmp_path / 'migration_test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


def _insert_proposal(conn, pid: int, title: str, n_products: int, n_schemes: int):
    """Inserta propuesta + productos + esquemas SIN product_id (estado pre-migración)."""
    conn.execute(text(
        "INSERT INTO clients (id, name, entity) VALUES (:cid, 'C', 'E')"
    ), {"cid": pid * 100})
    conn.execute(text(
        "INSERT INTO proposals (id, title, status, client_id, combine_schemes) "
        "VALUES (:pid, :title, 'DRAFT', :cid, 1)"
    ), {"pid": pid, "title": title, "cid": pid * 100})
    for i in range(n_products):
        conn.execute(text(
            "INSERT INTO proposal_products (id, proposal_id, product_name) "
            "VALUES (:id, :pid, :name)"
        ), {"id": pid * 10 + i, "pid": pid, "name": f"Prod {i}"})
    for i in range(n_schemes):
        conn.execute(text(
            "INSERT INTO proposal_schemes (id, proposal_id, scheme_type, product_id) "
            "VALUES (:id, :pid, 'LICENSING', NULL)"
        ), {"id": pid * 10 + i, "pid": pid})


def test_ensure_product_id_column_adds_when_missing(tmp_path):
    """En una tabla sin product_id, el script la agrega; segunda corrida no hace nada."""
    engine = create_engine(f"sqlite:///{tmp_path / 'legacy.db'}")
    with engine.begin() as conn:
        conn.execute(text(
            "CREATE TABLE proposal_schemes (id INTEGER PRIMARY KEY, proposal_id INTEGER)"
        ))

    assert ensure_product_id_column(engine) is True
    cols = {c["name"] for c in inspect(engine).get_columns("proposal_schemes")}
    assert "product_id" in cols

    # Idempotencia: la segunda corrida no intenta volver a agregarla
    assert ensure_product_id_column(engine) is False
    engine.dispose()


def test_backfill_links_single_product_proposals(migration_engine):
    """Propuesta con 1 producto → sus esquemas quedan vinculados a ese producto."""
    with migration_engine.begin() as conn:
        _insert_proposal(conn, pid=1, title="Single", n_products=1, n_schemes=2)

    summary = backfill(migration_engine)

    assert summary["linked"] == 2
    assert summary["legacy_proposals"] == []
    with migration_engine.connect() as conn:
        product_ids = conn.execute(text(
            "SELECT DISTINCT product_id FROM proposal_schemes WHERE proposal_id = 1"
        )).fetchall()
    assert product_ids == [(10,)]


def test_backfill_leaves_multi_product_proposals_as_legacy(migration_engine):
    """Propuesta con 2+ productos → esquemas quedan NULL y se reporta como legada."""
    with migration_engine.begin() as conn:
        _insert_proposal(conn, pid=2, title="Multi", n_products=2, n_schemes=1)

    summary = backfill(migration_engine)

    assert summary["linked"] == 0
    assert len(summary["legacy_proposals"]) == 1
    assert summary["legacy_proposals"][0][0] == 2
    with migration_engine.connect() as conn:
        null_count = conn.execute(text(
            "SELECT COUNT(*) FROM proposal_schemes "
            "WHERE proposal_id = 2 AND product_id IS NULL"
        )).scalar()
    assert null_count == 1


def test_backfill_is_idempotent(migration_engine):
    """Correr el backfill dos veces no cambia el resultado ni falla."""
    with migration_engine.begin() as conn:
        _insert_proposal(conn, pid=3, title="Idem", n_products=1, n_schemes=1)

    first = backfill(migration_engine)
    second = backfill(migration_engine)

    assert first["linked"] == 1
    assert second["linked"] == 0  # ya no quedan esquemas sin vincular
    assert second["legacy_proposals"] == []
