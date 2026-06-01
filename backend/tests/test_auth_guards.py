"""
Tests for auth.py — JWT validation and role-based access guards.
Complements test_auth.py (which covers /login). These tests focus on:
  - get_current_user error paths (invalid JWT, missing sub, no user, inactive)
  - require_creator / require_approver_1 / require_approver_2 / require_approver_any / require_admin

The guards are exercised via real endpoints (TestClient) so that
FastAPI's Depends graph runs end to end.
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import status
from jose import jwt

from fastapi import HTTPException

from app.auth import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_password_hash,
    require_admin,
    require_approver_1,
    require_approver_2,
    require_approver_any,
    require_creator,
)
from app.models.user import User, UserRole


# ---------- get_current_user: JWT validation ----------

def test_invalid_jwt_returns_401(client):
    """Token mal formado → 401 con WWW-Authenticate."""
    response = client.post(
        "/api/proposals/",
        json={"title": "x", "client_id": 1, "products": [], "schemes": []},
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.headers.get("www-authenticate") == "Bearer"


def test_jwt_without_sub_returns_401(client):
    """Token válido firmado pero sin claim 'sub' → 401."""
    token = jwt.encode(
        {"exp": datetime.now(timezone.utc) + timedelta(minutes=5)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response = client.post(
        "/api/proposals/",
        json={"title": "x", "client_id": 1, "products": [], "schemes": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_jwt_user_not_in_db_returns_401(client):
    """sub válido pero el usuario no existe en BD → 401."""
    token = create_access_token({"sub": "ghost@nowhere.com"})
    response = client.post(
        "/api/proposals/",
        json={"title": "x", "client_id": 1, "products": [], "schemes": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_inactive_user_returns_400(db_session, client):
    """Usuario existe pero is_active=False → 400 'Usuario inactivo'."""
    user = User(
        full_name="Inactivo",
        email="inactive@test.com",
        hashed_password=get_password_hash("pass"),
        role=UserRole.creator,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": user.email})
    response = client.post(
        "/api/proposals/",
        json={"title": "x", "client_id": 1, "products": [], "schemes": []},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "inactivo" in response.json()["detail"].lower()


def test_expired_jwt_returns_401(db_session, client):
    """Token expirado → 401."""
    user = User(
        full_name="Exp",
        email="expired@test.com",
        hashed_password=get_password_hash("pass"),
        role=UserRole.creator,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()

    expired_token = jwt.encode(
        {
            "sub": user.email,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    response = client.post(
        "/api/proposals/",
        json={"title": "x", "client_id": 1, "products": [], "schemes": []},
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ---------- Role guards: rejection paths ----------

def _make_user(db_session, role: UserRole, email: str) -> dict:
    user = User(
        full_name=f"User {role.value}",
        email=email,
        hashed_password=get_password_hash("pass"),
        role=role,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token({"sub": user.email})
    return {"Authorization": f"Bearer {token}"}


def test_require_creator_rejects_approver_1(db_session, client, sample_proposal_data):
    """approver_1 no puede crear propuestas (require_creator)."""
    headers = _make_user(db_session, UserRole.approver_1, "a1@test.com")
    response = client.post("/api/proposals/", json=sample_proposal_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "creator" in response.json()["detail"].lower()


def test_require_creator_rejects_approver_2(db_session, client, sample_proposal_data):
    """approver_2 no puede crear propuestas."""
    headers = _make_user(db_session, UserRole.approver_2, "a2@test.com")
    response = client.post("/api/proposals/", json=sample_proposal_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_require_creator_rejects_admin(db_session, client, sample_proposal_data):
    """admin no es creator — POST /proposals/ debe rechazar."""
    headers = _make_user(db_session, UserRole.admin, "admin1@test.com")
    response = client.post("/api/proposals/", json=sample_proposal_data, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_require_admin_accepts_admin(db_session, client):
    """admin puede listar usuarios (require_admin)."""
    headers = _make_user(db_session, UserRole.admin, "admin@test.com")
    response = client.get("/api/users/", headers=headers)
    assert response.status_code == status.HTTP_200_OK


def test_require_admin_rejects_creator(db_session, client):
    """creator no puede acceder a endpoints de admin."""
    headers = _make_user(db_session, UserRole.creator, "c@test.com")
    response = client.get("/api/users/", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "administrador" in response.json()["detail"].lower()


def test_require_admin_rejects_approver(db_session, client):
    """approver_1 no puede acceder a endpoints de admin."""
    headers = _make_user(db_session, UserRole.approver_1, "a1b@test.com")
    response = client.get("/api/users/", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------- require_approver_any: usado en /approve y /reject ----------

def test_require_approver_any_rejects_creator(db_session, client):
    """creator no puede aprobar — el guard require_approver_any debe rechazar."""
    headers = _make_user(db_session, UserRole.creator, "creator_appr@test.com")
    response = client.post(
        "/api/proposals/1/approve",
        json={
            "role": "reviewer",
            "approver_name": "X",
            "action": "approved",
        },
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "aprobador" in response.json()["detail"].lower()


def test_require_approver_any_rejects_admin(db_session, client):
    """admin tampoco — solo approver_1 o approver_2 pasan el guard."""
    headers = _make_user(db_session, UserRole.admin, "admin_appr@test.com")
    response = client.post(
        "/api/proposals/1/reject",
        json={
            "role": "reviewer",
            "approver_name": "X",
            "action": "rejected",
            "comments": "motivo",
        },
        headers=headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ---------- Unit tests directos para los guards ----------
# require_approver_1 y require_approver_2 no se usan aún en ningún endpoint,
# así que los testeamos llamándolos como funciones puras.

def _user(role: UserRole) -> User:
    return User(
        id=1,
        full_name="X",
        email="x@test.com",
        hashed_password="hashed",
        role=role,
        is_active=True,
    )


def test_require_creator_passes_for_creator():
    user = _user(UserRole.creator)
    assert require_creator(current_user=user) is user


def test_require_creator_raises_for_non_creator():
    user = _user(UserRole.approver_1)
    with pytest.raises(HTTPException) as exc_info:
        require_creator(current_user=user)
    assert exc_info.value.status_code == 403


def test_require_approver_1_passes_for_approver_1():
    user = _user(UserRole.approver_1)
    assert require_approver_1(current_user=user) is user


def test_require_approver_1_raises_for_approver_2():
    user = _user(UserRole.approver_2)
    with pytest.raises(HTTPException) as exc_info:
        require_approver_1(current_user=user)
    assert exc_info.value.status_code == 403
    assert "Ángela" in exc_info.value.detail


def test_require_approver_2_passes_for_approver_2():
    user = _user(UserRole.approver_2)
    assert require_approver_2(current_user=user) is user


def test_require_approver_2_raises_for_approver_1():
    user = _user(UserRole.approver_1)
    with pytest.raises(HTTPException) as exc_info:
        require_approver_2(current_user=user)
    assert exc_info.value.status_code == 403
    assert "Juan Pablo" in exc_info.value.detail


def test_require_approver_any_passes_for_both_approvers():
    assert require_approver_any(current_user=_user(UserRole.approver_1)).role == UserRole.approver_1
    assert require_approver_any(current_user=_user(UserRole.approver_2)).role == UserRole.approver_2


def test_require_approver_any_raises_for_creator():
    user = _user(UserRole.creator)
    with pytest.raises(HTTPException) as exc_info:
        require_approver_any(current_user=user)
    assert exc_info.value.status_code == 403


def test_require_admin_passes_for_admin():
    user = _user(UserRole.admin)
    assert require_admin(current_user=user) is user


def test_require_admin_raises_for_non_admin():
    user = _user(UserRole.creator)
    with pytest.raises(HTTPException) as exc_info:
        require_admin(current_user=user)
    assert exc_info.value.status_code == 403
