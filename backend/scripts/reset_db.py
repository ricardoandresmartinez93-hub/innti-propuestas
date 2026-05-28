# backend/scripts/reset_db.py
import sys
import os

# Añadir el directorio backend al path para poder importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
# Importar todos los modelos para que SQLAlchemy los reconozca antes de create_all
from app.models.proposal import Proposal
from app.models.client import Client
from app.models.user import User
from app.models.approval import Approval

def reset_database():
    # Tablas a eliminar/recrear (excluye 'users' para conservar los usuarios)
    tables_to_reset = [
        t for t in Base.metadata.sorted_tables
        if t.name != "users"
    ]

    print("Eliminando tablas (excepto users)...")
    for table in reversed(tables_to_reset):
        table.drop(bind=engine, checkfirst=True)
        print(f"  - {table.name} eliminada")

    print("Creando tablas...")
    for table in tables_to_reset:
        table.create(bind=engine, checkfirst=True)
        print(f"  - {table.name} creada")

    print("¡Base de datos limpia! Los usuarios se conservaron.")

if __name__ == "__main__":
    reset_database()