"""
Fixtures compartidos para pruebas del backend.
"""
import pytest
from unittest.mock import MagicMock, patch
import sys

# Mock dependencies that require system libraries
sys.modules["weasyprint"] = MagicMock()
sys.modules["mammoth"] = MagicMock()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.auth import get_password_hash, create_access_token
from app.routers.portfolio import get_portfolio_service


# Base de datos en memoria para tests
TEST_DATABASE_URL = "sqlite:///./test_innti.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Crea una sesión de BD limpia para cada test."""
    Base.metadata.drop_all(bind=engine)
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

    # Default: permissive portfolio service — all MVP schemes allowed for any product.
    # Tests that need specific scheme restrictions should override get_portfolio_service
    # using their own fixture (see test_portfolio_api.py's `portfolio_mock`).
    _permissive_portfolio = MagicMock()
    _permissive_portfolio.get_products.return_value = []
    _permissive_portfolio.get_allowed_schemes_for_product_name.return_value = [
        "licensing", "services", "support_maintenance"
    ]

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_portfolio_service] = lambda: _permissive_portfolio
    with patch("app.main.SessionLocal", TestSessionLocal):
        with TestClient(app) as test_client:
            yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def creator_headers(db_session: Session):
    """Crea un usuario creator y retorna las cabeceras de autorización JWT."""
    user = User(
        full_name="Test Creator",
        email="creator@test.com",
        hashed_password=get_password_hash("testpass"),
        role=UserRole.creator,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def approver_1_headers(db_session: Session):
    """Crea un usuario approver_1 (Ángela) y retorna las cabeceras JWT."""
    user = User(
        full_name="Ángela Test",
        email="angela@test.com",
        hashed_password=get_password_hash("testpass"),
        role=UserRole.approver_1,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def approver_2_headers(db_session: Session):
    """Crea un usuario approver_2 (Juan Pablo VP) y retorna las cabeceras JWT."""
    user = User(
        full_name="Juan Pablo Test",
        email="juanpablo@test.com",
        hashed_password=get_password_hash("testpass"),
        role=UserRole.approver_2,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_headers(db_session: Session):
    """Crea un usuario admin y retorna las cabeceras de autorización JWT."""
    user = User(
        full_name="Administrador Test",
        email="admin@test.com",
        hashed_password=get_password_hash("adminpass"),
        role=UserRole.admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token({"sub": user.email, "user_id": user.id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}


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
    """Datos de ejemplo para una propuesta (cada producto con su esquema)."""
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
                "scheme": {"scheme_type": "licensing", "payment_frequency": "unico"},
            },
            {
                "product_name": "Qx-Tránsito",
                "product_type": "Plataforma",
                "description": "Plataforma misional de tránsito",
                "category": "modernización",
                "scheme": {"scheme_type": "services", "payment_frequency": "mensual"},
            },
        ],
    }
