import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.user import User, UserRole
from app.auth import get_password_hash
from app.database import get_db

@pytest.fixture
def test_user(db_session):
    user = User(
        full_name="Test User",
        email="test@example.com",
        hashed_password=get_password_hash("pass"),
        role=UserRole.creator,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def inactive_user(db_session):
    user = User(
        full_name="Inactive User",
        email="inactive@example.com",
        hashed_password=get_password_hash("pass"),
        role=UserRole.creator,
        is_active=False
    )
    db_session.add(user)
    db_session.commit()
    return user

@pytest.fixture
def approver_user(db_session):
    user = User(
        full_name="Approver User",
        email="approver@example.com",
        hashed_password=get_password_hash("pass"),
        role=UserRole.approver_1,
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    return user

def test_login_success(test_user, client):
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "pass"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_login_wrong_password(test_user, client):
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales incorrectas"

def test_login_inactive_user(inactive_user, client):
    response = client.post(
        "/api/auth/login",
        json={"email": "inactive@example.com", "password": "pass"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Usuario inactivo"

def test_login_nonexistent_user(client):
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "pass"}
    )
    assert response.status_code == 401

def test_protected_endpoint_without_token(client):
    response = client.post("/api/proposals/", json={})
    assert response.status_code == 401

def test_protected_endpoint_wrong_role(approver_user, client):
    # Login as approver
    login_res = client.post(
        "/api/auth/login",
        json={"email": "approver@example.com", "password": "pass"}
    )
    token = login_res.json()["access_token"]
    
    response = client.post(
        "/api/proposals/",
        json={"title": "Test", "client_id": 1, "products": [], "schemes": []},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
    assert "Se requiere rol creator" in response.json()["detail"]

def test_protected_endpoint_correct_role(test_user, db_session, client):
    # Create client first
    from app.models.client import Client
    client_obj = Client(name="Test Client", entity="Test Entity", email="c@test.com")
    db_session.add(client_obj)
    db_session.commit()

    login_res = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "pass"}
    )
    token = login_res.json()["access_token"]
    
    response = client.post(
        "/api/proposals/",
        json={
            "title": "Test Proposal",
            "client_id": client_obj.id,
            "products": [
                {
                    "product_name": "Producto Auth",
                    "product_type": "Plataforma",
                    "scheme": {"scheme_type": "licensing", "payment_frequency": "Pago único"},
                }
            ],
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 201
