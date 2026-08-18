"""Enrutamiento y proxy del API Gateway.

El gateway es el único punto de entrada HTTP de la plataforma. Resuelve los
servicios internos por nombre de servicio (DNS de Kubernetes / red de Docker),
lo que demuestra comprensión de service discovery y redes básicas.
"""

import logging
import os

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from . import metrics

log = logging.getLogger("uvicorn.error")

SERVICES = {
    "bookings": os.getenv("BOOKING_SERVICE_URL", "http://booking-service:8001"),
    "payments": os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:8002"),
    "drivers": os.getenv("DRIVER_SERVICE_URL", "http://driver-service:8003"),
    "events": os.getenv("REALTIME_SERVICE_URL", "http://realtime-service:8004"),
    "ai": os.getenv("AI_SERVICE_URL", "http://ai-service:8005"),
}

ROUTES: dict[str, tuple[str, str]] = {
    "/v1/bookings": ("bookings", SERVICES["bookings"]),
    "/v1/payments": ("payments", SERVICES["payments"]),
    "/v1/drivers": ("drivers", SERVICES["drivers"]),
    "/v1/events": ("events", SERVICES["events"]),
    "/v1/ai": ("ai", SERVICES["ai"]),
}

router = APIRouter(tags=["gateway"])


def _match_route(path: str):
    for prefix, (name, url) in ROUTES.items():
        if path == prefix or path.startswith(prefix + "/"):
            return name, url
    return None


@router.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
async def proxy(path: str, request: Request) -> Response:
    """Reenvía la petición al microservicio correspondiente (proxy HTTP)."""
    full_path = f"/v1/{path}" if path else "/v1"
    matched = _match_route(full_path)
    if matched is None:
        return JSONResponse({"detail": "Ruta no encontrada"}, status_code=404)

    name, upstream = matched
    target = f"{upstream}/{full_path.lstrip('/')}"
    body = await request.body()
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.request(
                request.method, target, params=request.query_params, content=body, headers=headers
            )
    except httpx.HTTPError as exc:
        metrics.UPSTREAM_ERRORS.labels(name).inc()
        log.error("Upstream %s (%s) falló: %s", name, upstream, exc)
        return JSONResponse(
            {"detail": f"Servicio {name} no disponible"},
            status_code=502,
            headers={"X-Upstream-Error": "true"},
        )

    metrics.UPSTREAM_ERRORS.labels(name)
    return Response(
        content=response.content,
        status_code=response.status_code,
        media_type=response.headers.get("content-type"),
    )