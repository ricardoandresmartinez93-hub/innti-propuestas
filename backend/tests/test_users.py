"""
Pruebas unitarias para el modelo y CRUD de Usuarios.
Usa el fixture 'client' del conftest que inyecta la BD de tests aislada.
"""
import pytest
from fastapi import status


def test_create_user_creator(client):
    """Crear usuario con rol CREATOR."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Santiago Álvarez", "email": "santiago@quipux.com", "role": "creator"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["role"] == "creator"
    assert data["full_name"] == "Santiago Álvarez"
    assert data["is_active"] is True


def test_create_user_approver_1(client):
    """Crear usuario con rol APPROVER_1."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Ángela", "email": "angela@quipux.com", "role": "approver_1"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "approver_1"


def test_create_user_approver_2(client):
    """Crear usuario con rol APPROVER_2."""
    response = client.post(
        "/api/users/",
        json={
            "full_name": "Juan Pablo Ramírez Madrid",
            "email": "juanpablo@quipux.com",
            "role": "approver_2",
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "approver_2"


def test_create_user_viewer(client):
    """Crear usuario con rol VIEWER."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Michelle", "email": "michelle@quipux.com", "role": "viewer"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "viewer"


def test_email_must_be_unique(client):
    """No debe permitir dos usuarios con el mismo email."""
    user_data = {"full_name": "User 1", "email": "unique@quipux.com", "role": "creator"}
    first = client.post("/api/users/", json=user_data)
    assert first.status_code == status.HTTP_201_CREATED

    response = client.post("/api/users/", json=user_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email ya está registrado" in response.json()["detail"]


def test_deactivate_user(client):
    """Desactivar usuario debe poner is_active=False sin eliminarlo físicamente."""
    create_resp = client.post(
        "/api/users/",
        json={"full_name": "To Deactivate", "email": "deactivate@quipux.com", "role": "creator"}
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    user_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/users/{user_id}")
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    get_resp = client.get(f"/api/users/{user_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["is_active"] is False


def test_list_users_by_role(client):
    """Filtrar usuarios por rol debe retornar solo los correctos."""
    client.post("/api/users/", json={"full_name": "C1", "email": "c1@q.com", "role": "creator"})
    client.post("/api/users/", json={"full_name": "A1", "email": "a1@q.com", "role": "approver_1"})

    response = client.get("/api/users/?role=approver_1")
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) >= 1
    assert all(u["role"] == "approver_1" for u in users)


def test_default_role_is_creator(client):
    """Si no se especifica rol, debe ser CREATOR por defecto."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Default Role", "email": "default@quipux.com"}
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "creator"
