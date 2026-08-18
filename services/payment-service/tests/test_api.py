"""Tests del servicio de pagos."""

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


def test_create_payment():
    payload = {"booking_id": "bk-abc123", "amount_clp": 15000, "method": "card"}
    response = client.post("/v1/payments", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "approved"
    assert body["booking_id"] == "bk-abc123"


def test_payment_validation():
    assert client.post("/v1/payments", json={"booking_id": "x", "amount_clp": 0}).status_code == 422


def test_get_missing_payment_returns_404():
    assert client.get("/v1/payments/py-noexiste").status_code == 404