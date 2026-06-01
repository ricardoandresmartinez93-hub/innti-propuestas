"""
Migración one-shot: contenido por esquema.

Antes: los campos scope_content, validity_period, economic_conditions,
payment_terms, excluded_services e ip_section vivían en Proposal — todos los
esquemas compartían el mismo texto.

Después: viven en ProposalScheme — cada esquema tiene su propio contenido.

Este script copia los valores antiguos a CADA ProposalScheme asociado antes de
que las columnas viejas dejen de existir. Es idempotente: detecta si la
migración ya se ejecutó y la omite.

Uso:
    cd backend
    .\\venv\\Scripts\\activate
    python scripts/migrate_scheme_content.py [--dry-run]

Requisitos:
    - Hacer backup de innti.db antes de ejecutar en producción.
    - Ejecutar ANTES de aplicar el nuevo modelo (que ya no tiene las columnas
      viejas en Proposal). Si ya se aplicó el modelo nuevo, recuperar la BD
      desde backup primero.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime

# Permitir importar la app aunque se ejecute desde scripts/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("migrate_scheme_content")

LEGACY_COLUMNS = [
    "scope_content",
    "validity_period",
    "economic_conditions",
    "payment_terms",
    "excluded_services",
    "ip_section",
]


def _proposals_has_legacy_columns(engine) -> bool:
    """Devuelve True si la tabla proposals aún conserva las columnas viejas."""
    inspector = inspect(engine)
    cols = {c["name"] for c in inspector.get_columns("proposals")}
    return any(c in cols for c in LEGACY_COLUMNS)


def _ensure_new_columns_exist(engine) -> None:
    """En SQLite, añade las columnas nuevas a proposal_schemes si faltan."""
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns("proposal_schemes")}
    with engine.begin() as conn:
        for col in LEGACY_COLUMNS:
            if col not in existing:
                conn.execute(text(f"ALTER TABLE proposal_schemes ADD COLUMN {col} TEXT"))
                log.info("Columna añadida a proposal_schemes: %s", col)


def _migrate(engine, dry_run: bool) -> int:
    """Copia los campos legacy de cada propuesta a sus esquemas. Devuelve filas tocadas."""
    Session = sessionmaker(bind=engine)
    session = Session()
    touched = 0
    try:
        rows = session.execute(text(
            "SELECT id, scope_content, validity_period, economic_conditions, "
            "payment_terms, excluded_services, ip_section FROM proposals"
        )).fetchall()
        log.info("Propuestas encontradas: %d", len(rows))

        for r in rows:
            proposal_id = r[0]
            payload = {
                "scope_content": r[1],
                "validity_period": r[2],
                "economic_conditions": r[3],
                "payment_terms": r[4],
                "excluded_services": r[5],
                "ip_section": r[6],
            }
            if not any(payload.values()):
                continue  # Nada que copiar

            scheme_ids = [
                row[0]
                for row in session.execute(
                    text("SELECT id FROM proposal_schemes WHERE proposal_id = :pid"),
                    {"pid": proposal_id},
                ).fetchall()
            ]
            if not scheme_ids:
                log.warning("Propuesta %s sin esquemas — datos legacy descartados", proposal_id)
                continue

            for sid in scheme_ids:
                if dry_run:
                    log.info("[dry-run] copiar a scheme %s: %s", sid, list(payload.keys()))
                else:
                    session.execute(
                        text(
                            "UPDATE proposal_schemes SET "
                            "scope_content = COALESCE(scope_content, :scope_content), "
                            "validity_period = COALESCE(validity_period, :validity_period), "
                            "economic_conditions = COALESCE(economic_conditions, :economic_conditions), "
                            "payment_terms = COALESCE(payment_terms, :payment_terms), "
                            "excluded_services = COALESCE(excluded_services, :excluded_services), "
                            "ip_section = COALESCE(ip_section, :ip_section) "
                            "WHERE id = :sid"
                        ),
                        {**payload, "sid": sid},
                    )
                touched += 1
        if not dry_run:
            session.commit()
        return touched
    finally:
        session.close()


def _drop_legacy_columns(engine, dry_run: bool) -> None:
    """SQLite soporta DROP COLUMN desde 3.35; usamos un rebuild si falla."""
    if dry_run:
        log.info("[dry-run] se omiten DROP COLUMN")
        return
    with engine.begin() as conn:
        for col in LEGACY_COLUMNS:
            try:
                conn.execute(text(f"ALTER TABLE proposals DROP COLUMN {col}"))
                log.info("Columna eliminada de proposals: %s", col)
            except Exception as e:
                log.warning("No se pudo eliminar %s: %s — borrar manualmente o recrear la tabla", col, e)


def main() -> int:
    parser = argparse.ArgumentParser(description="Migra contenido global a contenido por esquema")
    parser.add_argument("--dry-run", action="store_true", help="No escribe cambios, solo simula")
    parser.add_argument("--keep-legacy-columns", action="store_true", help="No elimina las columnas viejas de proposals")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

    if not _proposals_has_legacy_columns(engine):
        log.info("La tabla proposals ya no tiene columnas legacy — migración no necesaria")
        return 0

    backup_hint = datetime.now().strftime("innti.db.backup-%Y%m%d-%H%M%S")
    log.warning("Recordatorio: haz un backup de innti.db antes de continuar (sugerencia: cp innti.db %s)", backup_hint)

    _ensure_new_columns_exist(engine)
    touched = _migrate(engine, args.dry_run)
    log.info("Esquemas tocados: %d", touched)

    if not args.keep_legacy_columns:
        _drop_legacy_columns(engine, args.dry_run)

    log.info("Migración completada%s", " (dry-run)" if args.dry_run else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
