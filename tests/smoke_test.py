"""Smoke test end-to-end de ViajIAmos.

Uso:
    docker compose up -d --build
    python tests/smoke_test.py            # local (docker compose, puerto 8000)
    python tests/smoke_test.py --base http://localhost:18000   # contra K8s (port-forward)

El timeout es configurable por entorno (SMOKE_TIMEOUT): en clusters locales
(kind) los primeros requests son lentos por la contención de CPU al arrancar.
"""

import argparse
import os
import sys
import time

import httpx

BASE = "http://localhost:8000"
TIMEOUT = float(os.getenv("SMOKE_TIMEOUT", "10"))


def _retry(fn, tries: int = 12, sleep: float = 1.0):
    """Reintenta una llamada hasta obtener un response 2xx.

    Necesario en K8s: los servicios usan estado en memoria (demo) y con
    varias réplicas el round-robin puede caer en un pod distinto al que
    escribió. En producción esto se resuelve con una base de datos
    compartida; aquí se reintenta hasta dar con la réplica correcta.
    """
    for _ in range(tries):
        response = fn()
        if response.status_code < 400:
            return response
        time.sleep(sleep)
    return response


def _wait_ready(base: str, retries: int = 30) -> None:
    for attempt in range(retries):
        try:
            response = httpx.get(f"{base}/healthz", timeout=2.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            pass
        time.sleep(1)
    raise SystemExit("Gateway no está listo tras 30s. ¿Ejecutaste 'docker compose up -d --build'?")


def _check(name: str, ok: bool, detail: str = "") -> None:
    status = "PASS" if ok else "FAIL"
    print(f"[{status}] {name}{' - ' + detail if detail else ''}")
    if not ok:
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke test end-to-end de ViajIAmos")
    parser.add_argument("--base", default=BASE, help="URL base del gateway (default: %(default)s)")
    args = parser.parse_args()
    base = args.base

    _wait_ready(base)

    health = httpx.get(f"{base}/healthz", timeout=TIMEOUT)
    _check("Gateway /healthz", health.status_code == 200, health.text)

    booking = httpx.post(
        f"{base}/v1/bookings",
        json={"origin": "Santiago", "destination": "Valparaíso", "passenger_name": "Ana Pérez", "passengers": 2},
        timeout=TIMEOUT,
    )
    _check("Crear reserva", booking.status_code == 201, booking.text)
    booking_id = booking.json()["id"]

    fetched = _retry(lambda: httpx.get(f"{base}/v1/bookings/{booking_id}", timeout=TIMEOUT))
    _check("Consultar reserva", fetched.status_code == 200 and fetched.json()["status"] == "created")

    payment = httpx.post(
        f"{base}/v1/payments",
        json={"booking_id": booking_id, "amount_clp": 15000, "method": "card"},
        timeout=TIMEOUT,
    )
    _check("Procesar pago", payment.status_code == 201 and payment.json()["status"] == "approved", payment.text)

    paid = _retry(lambda: httpx.patch(f"{base}/v1/bookings/{booking_id}/status", json={"status": "paid"}, timeout=TIMEOUT))
    _check("Marcar reserva pagada", paid.status_code == 200 and paid.json()["status"] == "paid")

    assignment = None
    for driver_id in ("drv-001", "drv-002", "drv-003"):
        attempt = _retry(
            lambda: httpx.post(
                f"{base}/v1/drivers/assign",
                json={"booking_id": booking_id, "driver_id": driver_id},
                timeout=TIMEOUT,
            )
        )
        if attempt.status_code == 201:
            assignment = attempt
            break
    _check(
        "Asignar conductor",
        assignment is not None,
        assignment.text if assignment else "ningún conductor de la semilla disponible (estado en memoria por réplica)",
    )

    event = httpx.post(
        f"{base}/v1/events/trips",
        json={"booking_id": booking_id, "event": "driver_assigned", "payload": {"driver": assignment.json()["driver_name"]}},
        timeout=TIMEOUT,
    )
    _check("Publicar evento Socket.IO", event.status_code == 202 and event.json()["published"] is True)

    ai = httpx.post(
        f"{base}/v1/ai/recommendations",
        json={"origin": "Santiago", "destination": "Concepción", "passengers": 3},
        timeout=TIMEOUT,
    )
    _check("Recomendación IA", ai.status_code == 200 and ai.json()["provider"] in ("heuristic", "ollama", "openai"), ai.text)

    drivers = httpx.get(f"{base}/v1/drivers", timeout=TIMEOUT)
    _check("Listar conductores", drivers.status_code == 200 and len(drivers.json()) >= 3)

    metrics = httpx.get(f"{base}/metrics", timeout=TIMEOUT)
    _check("Métricas gateway", metrics.status_code == 200 and "http_requests_total" in metrics.text)

    print("\nSmoke test completado: TODO OK")


if __name__ == "__main__":
    main()