"""Motor de recomendaciones multi-proveedor.

AI_PROVIDER=off     -> fallback heurístico determinista (funciona siempre, sin llaves)
AI_PROVIDER=ollama  -> LLM local gratuito (Ollama) para desarrollo y demo
AI_PROVIDER=openai  -> LLM en la nube (compatible con API OpenAI)

Cualquier error del proveedor externo degrada automáticamente al heurístico:
el servicio nunca deja de responder. La API key se inyecta como variable de
entorno (Secret en Kubernetes / variable protegida en CI).
"""

import json
import logging
import os

import httpx

from . import metrics
from .models import Recommendation, RecommendationRequest

log = logging.getLogger("uvicorn.error")

PROVIDER = os.getenv("AI_PROVIDER", "off").lower()
API_KEY = os.getenv("AI_API_KEY", "")
MODEL = os.getenv("AI_MODEL", "llama3.2")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434")
OPENAI_URL = os.getenv("OPENAI_URL", "https://api.openai.com/v1/chat/completions")

# Distancias aproximadas entre ciudades chilenas (km) para el heurístico
_ROUTE_KM: dict[tuple[str, str], int] = {
    ("santiago", "valparaíso"): 115,
    ("santiago", "viña del mar"): 120,
    ("santiago", "concepción"): 500,
    ("santiago", "temuco"): 680,
    ("santiago", "antofagasta"): 1350,
    ("valparaíso", "santiago"): 115,
    ("viña del mar", "santiago"): 120,
    ("concepción", "temuco"): 180,
    ("concepción", "santiago"): 500,
    ("temuco", "valdivia"): 110,
    ("antofagasta", "santiago"): 1350,
}

_BASE_FARE = 4000          # CLP
_FARE_PER_KM = 700         # CLP/km
_FARE_PER_PASSENGER = 1500 # CLP por pasajero adicional
_AVG_SPEED_KMH = 60        # para estimar duración


def _heuristic(request: RecommendationRequest) -> Recommendation:
    key = (request.origin.strip().lower(), request.destination.strip().lower())
    distance = _ROUTE_KM.get(key, 50)
    fare = _BASE_FARE + distance * _FARE_PER_KM + max(request.passengers - 1, 0) * _FARE_PER_PASSENGER
    duration = int(distance / _AVG_SPEED_KMH * 60) + 15
    return Recommendation(
        origin=request.origin,
        destination=request.destination,
        route=f"Ruta directa por carretera (~{distance} km)",
        fare_clp=fare,
        duration_minutes=duration,
        provider="heuristic",
        model=None,
    )


_SYSTEM_PROMPT = (
    "Eres el motor de recomendación de viajes de ViajIAmos. Responde SOLO con JSON válido "
    "con las claves: route (string), fare_clp (int), duration_minutes (int). "
    "Sé razonable con tarifas en pesos chilenos para transporte interurbano de pasajeros."
)


def _build_user_prompt(request: RecommendationRequest) -> str:
    return (
        f"Recomienda una ruta y tarifa para viajar de {request.origin} a {request.destination} "
        f"con {request.passengers} pasajero(s)."
    )


def _parse_llm_json(text: str) -> dict:
    """Extrae el primer objeto JSON de la respuesta del LLM (tolera texto adicional)."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Respuesta del LLM sin JSON")
    return json.loads(text[start : end + 1])


async def _ask_ollama(request: RecommendationRequest) -> Recommendation:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/generate",
            json={"model": MODEL, "prompt": f"{_SYSTEM_PROMPT}\n\n{_build_user_prompt(request)}", "stream": False},
        )
        response.raise_for_status()
        data = _parse_llm_json(response.json().get("response", ""))
    return Recommendation(
        origin=request.origin,
        destination=request.destination,
        route=data["route"],
        fare_clp=int(data["fare_clp"]),
        duration_minutes=int(data["duration_minutes"]),
        provider="ollama",
        model=MODEL,
    )


async def _ask_openai(request: RecommendationRequest) -> Recommendation:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            OPENAI_URL,
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(request)},
                ],
                "temperature": 0.3,
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = _parse_llm_json(content)
    return Recommendation(
        origin=request.origin,
        destination=request.destination,
        route=data["route"],
        fare_clp=int(data["fare_clp"]),
        duration_minutes=int(data["duration_minutes"]),
        provider="openai",
        model=MODEL,
    )


async def recommend(request: RecommendationRequest) -> Recommendation:
    """Delega al proveedor configurado; ante cualquier fallo, degrada al heurístico."""
    provider = PROVIDER
    if provider == "ollama":
        metrics.AI_REQUESTS.labels("ollama").inc()
        try:
            return await _ask_ollama(request)
        except Exception as exc:
            metrics.AI_FALLBACKS.labels("ollama_error").inc()
            log.warning("Ollama no disponible (%s), usando heurístico", exc)
    elif provider == "openai":
        if not API_KEY:
            metrics.AI_FALLBACKS.labels("missing_api_key").inc()
            log.warning("AI_API_KEY no configurada, usando heurístico")
        else:
            metrics.AI_REQUESTS.labels("openai").inc()
            try:
                return await _ask_openai(request)
            except Exception as exc:
                metrics.AI_FALLBACKS.labels("openai_error").inc()
                log.warning("OpenAI falló (%s), usando heurístico", exc)

    metrics.AI_REQUESTS.labels("heuristic").inc()
    return _heuristic(request)