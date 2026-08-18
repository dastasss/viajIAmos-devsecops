#!/usr/bin/env bash
# check-net.sh - Diagnóstico de red: DNS (service discovery) y HTTP interno.
# Demuestra comprensión de DNS/servicios en Kubernetes (competencia del cargo).
# Uso:
#   ./scripts/check-net.sh              # DNS + HTTP de todos los servicios
#   ./scripts/check-net.sh booking-service
set -euo pipefail

NAMESPACE="viajiamos"
TARGET="${1:-all}"

command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl no está instalado"; exit 1; }

echo "==> Desplegando pod temporal de diagnóstico (busybox)"
kubectl run net-diag --image=busybox:1.36 --restart=Never -n "$NAMESPACE" -- sleep 300 2>/dev/null || true
kubectl wait --for=condition=Ready pod/net-diag -n "$NAMESPACE" --timeout=60s >/dev/null 2>&1 || {
  echo "ERROR: no se pudo crear el pod de diagnóstico"; exit 1;
}
trap 'kubectl delete pod net-diag -n "$NAMESPACE" --ignore-not-found >/dev/null 2>&1' EXIT

SERVICES=(gateway:8000 booking-service:8001 payment-service:8002 driver-service:8003 realtime-service:8004 ai-service:8005)

check() {
  local svc="$1" port="$2"
  echo ""
  echo "--- $svc ---"
  echo -n "  DNS: "
  kubectl exec net-diag -n "$NAMESPACE" -- nslookup "$svc" 2>&1 | grep -A1 "Name:" | sed 's/^/    /' || echo "    FALLO DNS"
  echo -n "  HTTP /healthz: "
  kubectl exec net-diag -n "$NAMESPACE" -- wget -q -O - "http://$svc:$port/healthz" 2>&1 || echo "    FALLO HTTP"
}

if [ "$TARGET" = "all" ]; then
  for ep in "${SERVICES[@]}"; do
    svc=${ep%%:*}; port=${ep##*:}
    check "$svc" "$port"
  done
else
  for ep in "${SERVICES[@]}"; do
    svc=${ep%%:*}; port=${ep##*:}
    [ "$svc" = "$TARGET" ] && check "$svc" "$port"
  done
fi

echo ""
echo "OK: diagnóstico de red completado"