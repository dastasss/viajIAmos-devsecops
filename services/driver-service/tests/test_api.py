"""Tests del servicio de conductores."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    assert client.get("/healthz").status_code == 200


def test_readyz():
    assert client.get("/readyz").status_code == 200


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_list_drivers():
    response = client.get("/v1/drivers")
    assert response.status_code == 200
    assert len(response.json()) == 3


def test_assign_driver():
    payload = {"booking_id": "bk-abc123", "driver_id": "drv-001"}
    response = client.post("/v1/drivers/assign", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["driver_name"] == "Carlos Muñoz"
    assert body["eta_minutes"] == 10


def test_assign_unavailable_driver_returns_409():
    client.post("/v1/drivers/assign", json={"booking_id": "bk-1", "driver_id": "drv-001"})
    response = client.post("/v1/drivers/assign", json={"booking_id": "bk-2", "driver_id": "drv-001"})
    assert response.status_code == 409


def test_assign_unknown_driver_returns_409():
    response = client.post("/v1/drivers/assign", json={"booking_id": "bk-3", "driver_id": "drv-999"})
    assert response.status_code == 409