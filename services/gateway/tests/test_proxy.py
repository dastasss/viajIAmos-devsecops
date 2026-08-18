"""Tests del API Gateway: proxy a servicios mockeados."""

import httpx
import pytest
from fastapi.testclient import TestClient

from app import proxy
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


def test_unknown_route_returns_404():
    response = client.get("/v1/desconocido")
    assert response.status_code == 404


class _FakeResponse:
    status_code = 201
    content = b'{"id": "bk-1"}'
    headers = {"content-type": "application/json"}


class _FakeClient(httpx.AsyncClient):
    async def request(self, *args, **kwargs):
        return _FakeResponse()


class _FailingClient(httpx.AsyncClient):
    async def request(self, *args, **kwargs):
        raise httpx.ConnectError("conexión rechazada")


class _FakeRequest:
    def __init__(self, method: str = "GET"):
        self.method = method
        self.query_params = {}
        self.headers = {}

    async def body(self) -> bytes:
        return b""


@pytest.mark.asyncio
async def test_proxy_forwards_to_upstream(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient)
    response = await proxy.proxy("bookings", _FakeRequest("POST"))
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_proxy_upstream_failure_returns_502(monkeypatch):
    monkeypatch.setattr(httpx, "AsyncClient", _FailingClient)
    response = await proxy.proxy("bookings", _FakeRequest("GET"))
    assert response.status_code == 502


def test_security_headers_present():
    response = client.get("/healthz")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Server") == "ViajIAmos"