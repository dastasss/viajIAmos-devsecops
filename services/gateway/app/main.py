"""Punto de entrada del API Gateway."""

import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from . import metrics
from .proxy import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

SERVICE_NAME = os.getenv("SERVICE_NAME", "gateway")
metrics.SERVICE_NAME = SERVICE_NAME

app = FastAPI(
    title="ViajIAmos - API Gateway",
    description="Punto de entrada único a los microservicios de ViajIAmos",
    version="1.0.0",
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = "default-src 'none'"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Server"] = "ViajIAmos"
        response.headers["X-Request-ID"] = "viajiamos-gw"
        return response


app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(metrics.MetricsMiddleware)

app.include_router(router)


@app.get("/healthz")
def healthz() -> JSONResponse:
    return JSONResponse({"status": "ok", "service": SERVICE_NAME})


@app.get("/readyz")
def readyz() -> JSONResponse:
    return JSONResponse({"status": "ready", "service": SERVICE_NAME})


@app.get("/metrics")
def metrics_endpoint():
    return metrics.metrics_response()