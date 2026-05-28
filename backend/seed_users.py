"""
Script para crear los usuarios iniciales del sistema.
Ejecutar desde la carpeta backend con el venv activado:
    python seed_users.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database import SessionLocal, init_db
from app.models.user import User, UserRole
from app.auth import get_password_hash

USERS = [
    {
        "full_name": "Creador Propuestas",
        "email": "creator@innti.com",
        "password": "Innti2024!",
        "role": UserRole.creator,
    },
    {
        "full_name": "Ángela Revisora",
        "email": "angela@innti.com",
        "password": "Innti2024!",
        "role": UserRole.approver_1,
    },
    {
        "full_name": "Juan Pablo VP",
        "email": "juanpablo@innti.com",
        "password": "Innti2024!",
        "role": UserRole.approver_2,
    },
]


def seed():
    init_db()
    db = SessionLocal()
    created = 0
    skipped = 0
    try:
        for u in USERS:
            existing = db.query(User).filter(User.email == u["email"]).first()
            if existing:
                print(f"  [SKIP] {u['email']} ya existe")
                skipped += 1
                continue
            user = User(
                full_name=u["full_name"],
                email=u["email"],
                hashed_password=get_password_hash(u["password"]),
                role=u["role"],
                is_active=True,
            )
            db.add(user)
            created += 1
            print(f"  [OK]   {u['email']} ({u['role'].value})")
        db.commit()
        print(f"\nResultado: {created} creados, {skipped} omitidos.")
    finally:
        db.close()


if __name__ == "__main__":
    print("Creando usuarios iniciales...\n")
    seed()
    print("\nListo. Credenciales:")
    for u in USERS:
        print(f"  {u['role'].value:12}  {u['email']}  /  {u['password']}")
