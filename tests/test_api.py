from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


# ---------- GET ----------
def test_get_order_existente():
    response = client.get("/orders/O001")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "O001"
    assert data["status"] == "DRAFT"
    assert data["units"] == 4
    assert data["total"] == "2100.00"
    assert data["discount_percent"] == 10
    assert data["events"] == []


def test_get_order_no_existe():
    assert client.get("/orders/O999").status_code == 404


# ---------- confirm ----------
def test_confirm_order_success():
    # Probamos confirmar un pedido valido existente (O001)
    response = client.post("/orders/O001/confirm")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "O001"
    assert data["status"] == "CONFIRMED"


def test_confirm_order_not_found():
    # Probamos un ID que no existe para verificar el error 404
    response = client.post("/orders/O999/confirm")
    assert response.status_code == 404


def test_confirm_dos_veces_409():
    assert client.post("/orders/O013/confirm").status_code == 200
    assert client.post("/orders/O013/confirm").status_code == 409


def test_confirm_pedido_vacio_422():
    assert client.post("/orders/O007/confirm").status_code == 422


def test_confirm_cliente_inactivo_422():
    assert client.post("/orders/O003/confirm").status_code == 422


# ---------- ship ----------
def test_ship_success():
    client.post("/orders/O016/confirm")
    response = client.post("/orders/O016/ship", json={"tracking_number": "GUIA-123"})
    assert response.status_code == 200
    assert response.json()["status"] == "SHIPPED"


def test_ship_sin_guia_422():
    client.post("/orders/O012/confirm")
    response = client.post("/orders/O012/ship", json={"tracking_number": ""})
    assert response.status_code == 422
    assert client.get("/orders/O012").json()["status"] == "CONFIRMED"


def test_ship_desde_draft_409():
    response = client.post("/orders/O012/ship", json={"tracking_number": "GUIA-1"})
    assert response.status_code == 409


def test_ship_no_existe_404():
    response = client.post("/orders/O999/ship", json={"tracking_number": "GUIA-1"})
    assert response.status_code == 404


# ---------- cancel ----------
def test_cancel_success():
    client.post("/orders/O014/confirm")
    response = client.post("/orders/O014/cancel", json={"reason": "Cliente lo pidio"})
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_cancel_sin_motivo_422():
    client.post("/orders/O014/confirm")
    response = client.post("/orders/O014/cancel", json={"reason": " "})
    assert response.status_code == 422


def test_cancel_desde_shipped_409():
    client.post("/orders/O014/confirm")
    client.post("/orders/O014/ship", json={"tracking_number": "GUIA-9"})
    response = client.post("/orders/O014/cancel", json={"reason": "Ya enviado"})
    assert response.status_code == 409
    assert client.get("/orders/O014").json()["status"] == "SHIPPED"
