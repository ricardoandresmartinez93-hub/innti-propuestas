"""
Fixtures compartidos para pruebas del backend.
"""
import pytest
from unittest.mock import MagicMock
import sys

# Mock dependencies that require system libraries
sys.modules["weasyprint"] = MagicMock()
sys.modules["mammoth"] = MagicMock()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


# Base de datos en memoria para tests
TEST_DATABASE_URL = "sqlite:///./test_innti.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión de BD limpia para cada test."""
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session: Session):
    """Cliente HTTP de pruebas con BD inyectada."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_client_data():
    """Datos de ejemplo para un cliente."""
    return {
        "name": "Andrés Barreneche Cano",
        "position": "Gerencia Financiera y Administrativa",
        "entity": "Consorcio ITS Medellín",
        "department": "Gerencia",
        "city": "Medellín",
        "email": "andres.barreneche@consorcioits.com",
    }


@pytest.fixture
def sample_proposal_data():
    """Datos de ejemplo para una propuesta."""
    return {
        "title": "Licenciamiento y Modernización de soluciones",
        "code": "3018-0226",
        "combine_schemes": True,
        "products": [
            {
                "product_name": "Servicios digitales para el ciudadano",
                "product_type": "Plataforma",
                "description": "Plataforma de servicios digitales",
                "category": "nuevo",
            },
            {
                "product_name": "Qx-Tránsito",
                "product_type": "Plataforma",
                "description": "Plataforma misional de tránsito",
                "category": "modernización",
            },
        ],
        "schemes": [
            {"scheme_type": "licensing", "payment_frequency": "unico"},
        ],
    }
