"""
Tests para el router de clientes (app/routers/clients.py).

Cubre los endpoints CRUD: POST /, GET /, GET /{id}, PATCH /{id}, DELETE /{id}.
"""
import pytest
from fastapi import status


def test_list_clients_empty(client):
    """Lista vacía al inicio."""
    response = client.get("/api/clients/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


def test_create_client_success(client, sample_client_data):
    """Crear un cliente devuelve 201 con los datos correctos."""
    response = client.post("/api/clients/", json=sample_client_data)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == sample_client_data["name"]
    assert data["entity"] == sample_client_data["entity"]
    assert data["email"] == sample_client_data["email"]
    assert "id" in data


def test_list_clients_returns_created(client, sample_client_data):
    """Listar clientes devuelve los clientes creados."""
    client.post("/api/clients/", json=sample_client_data)
    second = {**sample_client_data, "name": "Segundo Cliente", "email": "segundo@test.com"}
    client.post("/api/clients/", json=second)

    response = client.get("/api/clients/")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


def test_list_clients_pagination(client, sample_client_data):
    """skip y limit controlan la paginación correctamente."""
    for i in range(5):
        c = {**sample_client_data, "name": f"Cliente {i}", "email": f"c{i}@test.com"}
        client.post("/api/clients/", json=c)

    response = client.get("/api/clients/?skip=2&limit=2")
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


def test_get_client_by_id(client, sample_client_data):
    """Obtener un cliente por ID devuelve los datos correctos."""
    create_res = client.post("/api/clients/", json=sample_client_data)
    client_id = create_res.json()["id"]

    response = client.get(f"/api/clients/{client_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == client_id
    assert data["name"] == sample_client_data["name"]


def test_get_client_not_found(client):
    """Obtener un cliente inexistente devuelve 404."""
    response = client.get("/api/clients/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "no encontrado" in response.json()["detail"].lower()


def test_update_client_partial(client, sample_client_data):
    """PATCH actualiza solo los campos enviados."""
    create_res = client.post("/api/clients/", json=sample_client_data)
    client_id = create_res.json()["id"]

    update_data = {"name": "Nombre Actualizado", "city": "Cali"}
    response = client.patch(f"/api/clients/{client_id}", json=update_data)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Nombre Actualizado"
    assert data["city"] == "Cali"
    # El resto de campos permanece igual
    assert data["entity"] == sample_client_data["entity"]


def test_update_client_not_found(client):
    """PATCH en cliente inexistente devuelve 404."""
    response = client.patch("/api/clients/99999", json={"name": "Nuevo"})
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_client(client, sample_client_data):
    """DELETE elimina el cliente y devuelve 204; GET posterior devuelve 404."""
    create_res = client.post("/api/clients/", json=sample_client_data)
    client_id = create_res.json()["id"]

    response = client.delete(f"/api/clients/{client_id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    get_res = client.get(f"/api/clients/{client_id}")
    assert get_res.status_code == status.HTTP_404_NOT_FOUND


def test_delete_client_not_found(client):
    """DELETE en cliente inexistente devuelve 404."""
    response = client.delete("/api/clients/99999")
    assert response.status_code == status.HTTP_404_NOT_FOUND
