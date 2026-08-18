"""Métricas estilo Prometheus (escrapeables por GCP Managed Prometheus)."""

import time

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total de peticiones HTTP",
    ["service", "method", "path", "status"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Latencia de peticiones HTTP",
    ["service", "method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)

ERRORS_TOTAL = Counter(
    "http_errors_total",
    "Errores HTTP (5xx)",
    ["service", "method", "path"],
)

SERVICE_NAME = "unknown"


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware que registra latencia, tasa de errores y conteo por endpoint."""

    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            status = 500
            raise
        else:
            status = response.status_code

        path = request.url.path
        duration = time.perf_counter() - start
        REQUESTS_TOTAL.labels(SERVICE_NAME, request.method, path, status).inc()
        REQUEST_DURATION.labels(SERVICE_NAME, request.method, path).observe(duration)
        if status >= 500:
            ERRORS_TOTAL.labels(SERVICE_NAME, request.method, path).inc()
        return response


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)