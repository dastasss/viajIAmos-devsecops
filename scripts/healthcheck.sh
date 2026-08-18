#!/usr/bin/env bash
# healthcheck.sh - Healthchecks HTTP de todos los servicios (healthz/readyz).
# Uso:
#   ./scripts/healthcheck.sh           # vía port-forward (K8s)
#   ./scripts/healthcheck.sh --compose # vía docker compose (localhost)
set -euo pipefail

NAMESPACE="viajiamos"
MODE="k8s"

usage() {
  echo "Uso: $0 [--compose]"
  echo "  --compose   Healthcheck contra docker compose (localhost:8000-8005)"
  echo "  (default)   Healthcheck contra K8s vía port-forward"
  exit 1
}

[ "${1:-}" = "--compose" ] && MODE="compose"
[ "${1:-}" = "-h" ] && usage

check() {
  local name="$1" url="$2"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$url" 2>/dev/null || echo "000")
  if [ "$code" = "200" ]; then
    printf "  %-18s %s\n" "$name" "OK (200)"
  else
    printf "  %-18s %s\n" "$name" "FALLO ($code)"
  fi
}

ENDPOINTS=(gateway:8000 booking-service:8001 payment-service:8002 driver-service:8003 realtime-service:8004 ai-service:8005)

if [ "$MODE" = "compose" ]; then
  echo "==> Healthcheck docker compose (localhost)"
  for ep in "${ENDPOINTS[@]}"; do
    name=${ep%%:*}; port=${ep##*:}
    check "$name" "http://localhost:$port/healthz"
  done
else
  command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl no está instalado"; exit 1; }
  echo "==> Healthcheck K8s vía port-forward (puerto 18000 en localhost)"
  kubectl port-forward -n "$NAMESPACE" svc/gateway 18000:8000 &
  PF_PID=$!
  trap 'kill $PF_PID 2>/dev/null || true' EXIT
  sleep 3
  for ep in "${ENDPOINTS[@]}"; do
    name=${ep%%:*}
    check "$name" "http://localhost:18000/$name/healthz"
  done
fi

echo "==> Healthcheck completado"