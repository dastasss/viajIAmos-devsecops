"""Tests del servicio de tiempo real."""

import socketio
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


def test_publish_event_returns_202():
    payload = {"booking_id": "bk-abc123", "event": "driver_assigned", "payload": {"driver": "Carlos"}}
    response = client.post("/v1/events/trips", json=payload)
    assert response.status_code == 202
    body = response.json()
    assert body["published"] is True
    assert body["booking_id"] == "bk-abc123"


def test_publish_event_validation():
    payload = {"booking_id": "bk-abc123", "event": "evento_invalido"}
    response = client.post("/v1/events/trips", json=payload)
    assert response.status_code == 422


def test_socketio_endpoint_exposed():
    response = client.get("/socket.io/", params={"EIO": "4", "transport": "polling"})
    assert response.status_code == 200