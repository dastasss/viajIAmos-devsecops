#!/usr/bin/env bash
# diagnose-pod.sh - Diagnóstico de un pod/servicio caído o degradado.
# Es el flujo del cargo: "describe, logs y events" ante una caída.
# Uso:
#   ./scripts/diagnose-pod.sh booking-service            # diagnóstico completo
#   ./scripts/diagnose-pod.sh booking-service -f         # + follow de logs
#   ./scripts/diagnose-pod.sh booking-service -n staging
set -euo pipefail

NAMESPACE="viajiamos"
APP="${1:-}"
FOLLOW=""

usage() {
  echo "Uso: $0 <app> [-f] [-n namespace]"
  echo "  app   Label app del deployment (obligatorio)"
  echo "  -f    Follow de logs (stream)"
  echo "  -n    Namespace (default: viajiamos)"
  exit 1
}

[ -z "$APP" ] && usage
shift

while getopts "fn:h" opt; do
  case "$opt" in
    f) FOLLOW="1" ;;
    n) NAMESPACE="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done

command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl no está instalado"; exit 1; }

echo "===== 1. Estado de los pods ====="
kubectl get pods -n "$NAMESPACE" -l "app=$APP" -o wide

PODS=$(kubectl get pods -n "$NAMESPACE" -l "app=$APP" -o name)
[ -z "$PODS" ] && { echo "ERROR: no hay pods con app=$APP"; exit 1; }

for pod in $PODS; do
  PHASE=$(kubectl get "$pod" -n "$NAMESPACE" -o jsonpath='{.status.phase}')
  echo ""
  echo "===== $pod (fase: $PHASE) ====="

  echo "----- describe (eventos, probes, reason) -----"
  kubectl describe "$pod" -n "$NAMESPACE" | tail -40

  echo "----- últimos eventos del namespace -----"
  kubectl get events -n "$NAMESPACE" --sort-by=.lastTimestamp | tail -10

  echo "----- logs (últimas 50 líneas) -----"
  kubectl logs "$pod" -n "$NAMESPACE" --tail=50 --prefix=true || echo "(sin logs)"

  if [ -n "${FOLLOW:-}" ]; then
    echo "----- logs en streaming (Ctrl+C para salir) -----"
    kubectl logs "$pod" -n "$NAMESPACE" -f || true
  fi
done

echo "OK: diagnóstico de $APP completado"