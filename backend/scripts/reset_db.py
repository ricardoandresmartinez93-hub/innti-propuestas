# backend/scripts/reset_db.py
import sys
import os

# Añadir el directorio backend al path para poder importar la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
# Importar todos los modelos para que SQLAlchemy los reconozca antes de create_all
from app.models.proposal import Proposal # Ajusta según tus nombres de archivos
from app.models.client import Client     # de modelos en app/models/

def reset_database():
    print("Eliminando tablas...")
    Base.metadata.drop_all(bind=engine)
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    print("¡Base de datos limpia!")

if __name__ == "__main__":
    reset_database()