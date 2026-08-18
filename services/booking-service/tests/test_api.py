"""Tests del servicio de reservas."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_readyz():
    response = client.get("/readyz")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text


def test_security_headers_present():
    response = client.get("/healthz")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Server") == "ViajIAmos"


def test_create_and_get_booking():
    payload = {
        "origin": "Santiago",
        "destination": "Valparaíso",
        "passenger_name": "Ana Pérez",
        "passengers": 2,
        "vehicle_type": "van",
    }
    created = client.post("/v1/bookings", json=payload)
    assert created.status_code == 201
    booking = created.json()
    assert booking["status"] == "created"
    assert booking["origin"] == "Santiago"

    fetched = client.get(f"/v1/bookings/{booking['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == booking["id"]


def test_booking_validation():
    payload = {"origin": "Santiago", "destination": "", "passenger_name": "X", "passengers": 0}
    response = client.post("/v1/bookings", json=payload)
    assert response.status_code == 422


def test_get_missing_booking_returns_404():
    response = client.get("/v1/bookings/bk-noexiste")
    assert response.status_code == 404


def test_status_update_flow():
    payload = {
        "origin": "Concepción",
        "destination": "Temuco",
        "passenger_name": "Luis Soto",
        "passengers": 1,
    }
    booking = client.post("/v1/bookings", json=payload).json()
    paid = client.patch(
        f"/v1/bookings/{booking['id']}/status", json={"status": "paid"}
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"