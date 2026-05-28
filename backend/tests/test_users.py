"""
Pruebas unitarias para el modelo y CRUD de Usuarios.
Usa el fixture 'client' del conftest que inyecta la BD de tests aislada.
Los endpoints de gestión de usuarios requieren autenticación de administrador.
"""
import pytest
from fastapi import status

DEFAULT_PASSWORD = "Passw0rd!"


def test_create_user_creator(client, admin_headers):
    """Crear usuario con rol CREATOR."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Santiago Álvarez", "email": "santiago@quipux.com", "role": "creator", "password": DEFAULT_PASSWORD},
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["role"] == "creator"
    assert data["full_name"] == "Santiago Álvarez"
    assert data["is_active"] is True


def test_create_user_approver_1(client, admin_headers):
    """Crear usuario con rol APPROVER_1."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Ángela", "email": "angela@quipux.com", "role": "approver_1", "password": DEFAULT_PASSWORD},
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "approver_1"


def test_create_user_approver_2(client, admin_headers):
    """Crear usuario con rol APPROVER_2."""
    response = client.post(
        "/api/users/",
        json={
            "full_name": "Juan Pablo Ramírez Madrid",
            "email": "juanpablo@quipux.com",
            "role": "approver_2",
            "password": DEFAULT_PASSWORD,
        },
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "approver_2"


def test_create_user_viewer(client, admin_headers):
    """Crear usuario con rol VIEWER."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Michelle", "email": "michelle@quipux.com", "role": "viewer", "password": DEFAULT_PASSWORD},
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "viewer"


def test_create_user_admin(client, admin_headers):
    """Crear usuario con rol ADMIN."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Admin Secundario", "email": "admin2@quipux.com", "role": "admin", "password": DEFAULT_PASSWORD},
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "admin"


def test_create_user_requires_admin(client, creator_headers):
    """Solo administradores pueden crear usuarios."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Nuevo", "email": "nuevo@quipux.com", "role": "creator", "password": DEFAULT_PASSWORD},
        headers=creator_headers,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_user_unauthenticated(client):
    """Sin autenticación no se puede crear usuarios."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Sin Auth", "email": "sinauth@quipux.com", "role": "creator", "password": DEFAULT_PASSWORD},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_email_must_be_unique(client, admin_headers):
    """No debe permitir dos usuarios con el mismo email."""
    user_data = {"full_name": "User 1", "email": "unique@quipux.com", "role": "creator", "password": DEFAULT_PASSWORD}
    first = client.post("/api/users/", json=user_data, headers=admin_headers)
    assert first.status_code == status.HTTP_201_CREATED

    response = client.post("/api/users/", json=user_data, headers=admin_headers)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "email ya está registrado" in response.json()["detail"]


def test_deactivate_user(client, admin_headers):
    """Desactivar usuario debe poner is_active=False sin eliminarlo físicamente."""
    create_resp = client.post(
        "/api/users/",
        json={"full_name": "To Deactivate", "email": "deactivate@quipux.com", "role": "creator", "password": DEFAULT_PASSWORD},
        headers=admin_headers,
    )
    assert create_resp.status_code == status.HTTP_201_CREATED
    user_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/users/{user_id}", headers=admin_headers)
    assert delete_resp.status_code == status.HTTP_204_NO_CONTENT

    get_resp = client.get(f"/api/users/{user_id}", headers=admin_headers)
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["is_active"] is False


def test_list_users_by_role(client, admin_headers):
    """Filtrar usuarios por rol debe retornar solo los correctos."""
    client.post("/api/users/", json={"full_name": "C1", "email": "c1@q.com", "role": "creator", "password": DEFAULT_PASSWORD}, headers=admin_headers)
    client.post("/api/users/", json={"full_name": "A1", "email": "a1@q.com", "role": "approver_1", "password": DEFAULT_PASSWORD}, headers=admin_headers)

    response = client.get("/api/users/?role=approver_1", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    users = response.json()
    assert len(users) >= 1
    assert all(u["role"] == "approver_1" for u in users)


def test_default_role_is_creator(client, admin_headers):
    """Si no se especifica rol, debe ser CREATOR por defecto."""
    response = client.post(
        "/api/users/",
        json={"full_name": "Default Role", "email": "default@quipux.com", "password": DEFAULT_PASSWORD},
        headers=admin_headers,
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["role"] == "creator"


def test_update_user_password(client, admin_headers):
    """El admin puede cambiar la contraseña de un usuario."""
    create_resp = client.post(
        "/api/users/",
        json={"full_name": "Pass User", "email": "passuser@quipux.com", "role": "creator", "password": DEFAULT_PASSWORD},
        headers=admin_headers,
    )
    user_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/api/users/{user_id}",
        json={"new_password": "NuevaPass123!"},
        headers=admin_headers,
    )
    assert update_resp.status_code == status.HTTP_200_OK


def test_admin_cannot_deactivate_self(client, admin_headers):
    """El admin no puede desactivar su propia cuenta."""
    # El admin_headers corresponde al usuario admin@test.com
    list_resp = client.get("/api/users/?role=admin", headers=admin_headers)
    admin_id = list_resp.json()[0]["id"]

    resp = client.delete(f"/api/users/{admin_id}", headers=admin_headers)
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
