"""Tests del servicio de IA: heurístico determinista + proveedores con mock."""

import httpx
import pytest
from fastapi.testclient import TestClient

from app import recommender
from app.main import app
from app.models import RecommendationRequest

client = TestClient(app)

ORIGIN = "Santiago"
DEST = "Valparaíso"
KM_SANTIAGO_VALPO = 115


def test_healthz():
    assert client.get("/healthz").status_code == 200


def test_readyz():
    assert client.get("/readyz").status_code == 200


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text


def test_recommendation_validation():
    response = client.post("/v1/ai/recommendations", json={"origin": "A", "destination": "", "passengers": 0})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_heuristic_deterministic():
    request = RecommendationRequest(origin=ORIGIN, destination=DEST, passengers=2)
    rec = recommender._heuristic(request)
    expected_fare = 4000 + KM_SANTIAGO_VALPO * 700 + 1500
    assert rec.provider == "heuristic"
    assert rec.fare_clp == expected_fare
    assert rec.route == f"Ruta directa por carretera (~{KM_SANTIAGO_VALPO} km)"


class _FakeOllamaResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"response": '{"route": "Por Ruta 68", "fare_clp": 85000, "duration_minutes": 100}'}


class _FakeOllamaClient(httpx.AsyncClient):
    async def post(self, *args, **kwargs):
        return _FakeOllamaResponse()


@pytest.mark.asyncio
async def test_ollama_provider(monkeypatch):
    monkeypatch.setattr(recommender, "PROVIDER", "ollama")
    monkeypatch.setattr(recommender, "MODEL", "llama3.2")
    monkeypatch.setattr(httpx, "AsyncClient", _FakeOllamaClient)

    request = RecommendationRequest(origin=ORIGIN, destination=DEST, passengers=1)
    rec = await recommender.recommend(request)
    assert rec.provider == "ollama"
    assert rec.model == "llama3.2"
    assert rec.fare_clp == 85000


class _FailingClient(httpx.AsyncClient):
    async def post(self, *args, **kwargs):
        raise RuntimeError("ollama caído")


@pytest.mark.asyncio
async def test_ollama_failure_falls_back_to_heuristic(monkeypatch):
    monkeypatch.setattr(recommender, "PROVIDER", "ollama")
    monkeypatch.setattr(httpx, "AsyncClient", _FailingClient)

    request = RecommendationRequest(origin=ORIGIN, destination=DEST, passengers=1)
    rec = await recommender.recommend(request)
    assert rec.provider == "heuristic"


@pytest.mark.asyncio
async def test_openai_without_key_falls_back(monkeypatch):
    monkeypatch.setattr(recommender, "PROVIDER", "openai")
    monkeypatch.setattr(recommender, "API_KEY", "")
    request = RecommendationRequest(origin=ORIGIN, destination=DEST, passengers=1)
    rec = await recommender.recommend(request)
    assert rec.provider == "heuristic"