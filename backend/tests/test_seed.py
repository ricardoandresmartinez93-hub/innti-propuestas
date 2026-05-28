"""
Tests para app/seed.py — creación del administrador inicial.
"""
import pytest
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.auth import verify_password
from app.seed import seed_admin, ADMIN_EMAIL, ADMIN_FULL_NAME


class TestSeedAdmin:
    def test_creates_admin_when_none_exists(self, db_session: Session) -> None:
        """seed_admin debe crear un usuario admin si no existe ninguno."""
        # Verificar que no hay admin antes de ejecutar seed
        assert db_session.query(User).filter(User.role == UserRole.admin).first() is None

        seed_admin(db_session)

        admin = db_session.query(User).filter(User.role == UserRole.admin).first()
        assert admin is not None
        assert admin.email == ADMIN_EMAIL
        assert admin.full_name == ADMIN_FULL_NAME
        assert admin.role == UserRole.admin
        assert admin.is_active is True

    def test_admin_password_is_hashed_and_verifiable(self, db_session: Session) -> None:
        """La contraseña del admin creado por seed debe ser verificable con verify_password."""
        from app.seed import ADMIN_PASSWORD

        seed_admin(db_session)

        admin = db_session.query(User).filter(User.role == UserRole.admin).first()
        assert admin is not None
        assert verify_password(ADMIN_PASSWORD, admin.hashed_password)

    def test_does_not_create_duplicate_admin(self, db_session: Session) -> None:
        """seed_admin no debe crear un segundo admin si ya existe uno."""
        seed_admin(db_session)
        seed_admin(db_session)  # Segunda llamada — no debería agregar otro

        admin_count = db_session.query(User).filter(User.role == UserRole.admin).count()
        assert admin_count == 1

    def test_does_not_create_admin_if_one_already_exists(self, db_session: Session) -> None:
        """Si ya existe un admin (cualquiera), seed_admin no crea nada."""
        from app.auth import get_password_hash

        existing_admin = User(
            full_name="Admin Previo",
            email="otro_admin@quipux.com",
            hashed_password=get_password_hash("OtraPass1!"),
            role=UserRole.admin,
            is_active=True,
        )
        db_session.add(existing_admin)
        db_session.commit()

        seed_admin(db_session)

        admins = db_session.query(User).filter(User.role == UserRole.admin).all()
        assert len(admins) == 1
        assert admins[0].email == "otro_admin@quipux.com"

    def test_other_users_are_not_affected(self, db_session: Session) -> None:
        """seed_admin no elimina ni modifica usuarios existentes de otros roles."""
        from app.auth import get_password_hash

        creator = User(
            full_name="Creador Existente",
            email="creator@quipux.com",
            hashed_password=get_password_hash("pass123"),
            role=UserRole.creator,
            is_active=True,
        )
        db_session.add(creator)
        db_session.commit()

        seed_admin(db_session)

        total_users = db_session.query(User).count()
        assert total_users == 2  # El admin nuevo + el creator previo

        creator_check = db_session.query(User).filter(User.email == "creator@quipux.com").first()
        assert creator_check is not None
        assert creator_check.full_name == "Creador Existente"
