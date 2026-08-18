# Syntax=docker/dockerfile:1
# Stage 1: builder - capa de dependencias cacheable
FROM python:3.13-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY requirements.txt .
RUN pip wheel --wheel-dir /wheels -r requirements.txt

# Stage 2: runtime - imagen mínima, usuario no-root
FROM python:3.13-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    APP_USER=appuser \
    APP_HOME=/app

RUN groupadd --gid 10001 appuser \
    && useradd --uid 10001 --gid appuser --shell /usr/sbin/nologin --home-dir "$APP_HOME" appuser \
    && mkdir -p "$APP_HOME" \
    && chown -R appuser:appuser "$APP_HOME"

WORKDIR $APP_HOME
COPY --from=builder /wheels /wheels
COPY --from=builder /build/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --no-index --find-links=/wheels -r requirements.txt \
    && rm -rf /wheels requirements.txt

COPY --chown=appuser:appuser app ./app

USER appuser

EXPOSE 8002

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8002/healthz')"

LABEL org.opencontainers.image.source="https://github.com/viajiamos-demo/viajiamos-demo" \
      org.opencontainers.image.title="payment-service" \
      org.opencontainers.image.description="Servicio de pagos - ViajIAmos"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]