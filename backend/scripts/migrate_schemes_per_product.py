"""
Migración one-shot: esquemas vinculados a producto.

Antes: los esquemas (ProposalScheme) colgaban solo de la propuesta — un mismo
esquema aplicaba a todos los productos.

Después: cada esquema pertenece a UN producto (product_id). Las propuestas
nuevas se crean siempre con el vínculo; este script hace backfill de las
existentes.

Backfill best-effort:
    - Propuesta con exactamente 1 producto → todos sus esquemas se vinculan
      a ese producto.
    - Propuesta con 2+ productos → no hay forma de inferir el vínculo;
      los esquemas quedan con product_id NULL (propuesta "legada", conserva
      la generación de documentos por esquema) y se reporta por consola.

Es idempotente: correrlo dos veces no rompe nada — la columna solo se agrega
si falta y el backfill solo toca esquemas con product_id NULL.

Uso:
    cd backend
    python scripts/migrate_schemes_per_product.py [--dry-run]
"""
from __future__ import annotations

import argparse
import logging
import os
import sys

# Permitir importar la app aunque se ejecute desde scripts/
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text

from app.config import get_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("migrate_schemes_per_product")


def ensure_product_id_column(engine) -> bool:
    """Agrega la columna product_id a proposal_schemes si falta. True si la agregó."""
    inspector = inspect(engine)
    existing = {c["name"] for c in inspector.get_columns("proposal_schemes")}
    if "product_id" in existing:
        return False
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE proposal_schemes ADD COLUMN product_id INTEGER "
            "REFERENCES proposal_products(id)"
        ))
    log.info("Columna añadida a proposal_schemes: product_id")
    return True


def backfill(engine, dry_run: bool = False) -> dict:
    """Vincula esquemas huérfanos a su producto cuando la propuesta tiene 1 solo producto.

    Devuelve un resumen: {"linked": n, "legacy_proposals": [(id, title, n_products)]}.
    """
    linked = 0
    legacy: list[tuple] = []

    with engine.begin() as conn:
        rows = conn.execute(text(
            "SELECT p.id, p.title, COUNT(pp.id) AS n_products "
            "FROM proposals p "
            "LEFT JOIN proposal_products pp ON pp.proposal_id = p.id "
            "WHERE EXISTS (SELECT 1 FROM proposal_schemes ps "
            "              WHERE ps.proposal_id = p.id AND ps.product_id IS NULL) "
            "GROUP BY p.id, p.title"
        )).fetchall()

        for proposal_id, title, n_products in rows:
            if n_products == 1:
                product_id = conn.execute(
                    text("SELECT id FROM proposal_products WHERE proposal_id = :pid"),
                    {"pid": proposal_id},
                ).scalar()
                if dry_run:
                    log.info("[dry-run] Propuesta %s: vincular esquemas al producto %s", proposal_id, product_id)
                else:
                    result = conn.execute(
                        text(
                            "UPDATE proposal_schemes SET product_id = :prod "
                            "WHERE proposal_id = :pid AND product_id IS NULL"
                        ),
                        {"prod": product_id, "pid": proposal_id},
                    )
                    linked += result.rowcount
            else:
                legacy.append((proposal_id, title, n_products))
                log.warning(
                    "Propuesta %s '%s': %s productos, esquemas quedan como legados",
                    proposal_id, title, n_products,
                )

    return {"linked": linked, "legacy_proposals": legacy}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Vincula los esquemas existentes a su producto (backfill best-effort)"
    )
    parser.add_argument("--dry-run", action="store_true", help="No escribe cambios, solo simula")
    args = parser.parse_args()

    settings = get_settings()
    engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})

    ensure_product_id_column(engine)
    summary = backfill(engine, args.dry_run)

    log.info("Esquemas vinculados: %d", summary["linked"])
    if summary["legacy_proposals"]:
        log.info(
            "Propuestas legadas (multi-producto, sin vínculo inferible): %d",
            len(summary["legacy_proposals"]),
        )
    log.info("Migración completada%s", " (dry-run)" if args.dry_run else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
