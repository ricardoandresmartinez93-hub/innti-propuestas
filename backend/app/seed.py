"""
Datos iniciales (seed) para la base de datos.
"""
from sqlalchemy.orm import Session

from app.models.user import User, UserRole
from app.auth import get_password_hash

ADMIN_EMAIL = "admin@quipux.com"
ADMIN_PASSWORD = "Admin2024!"
ADMIN_FULL_NAME = "Administrador"


def seed_admin(db: Session) -> None:
    """Crea el usuario administrador inicial si no existe ninguno."""
    existing_admin = db.query(User).filter(User.role == UserRole.admin).first()
    if existing_admin:
        return

    admin = User(
        full_name=ADMIN_FULL_NAME,
        email=ADMIN_EMAIL,
        hashed_password=get_password_hash(ADMIN_PASSWORD),
        role=UserRole.admin,
        is_active=True,
    )
    db.add(admin)
    db.commit()
