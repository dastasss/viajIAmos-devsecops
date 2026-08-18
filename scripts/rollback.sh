#!/usr/bin/env bash
# rollback.sh - Revierte un deployment a una revisión anterior (rollback).
# Uso:
#   ./scripts/rollback.sh booking-service          # revierte al release anterior
#   ./scripts/rollback.sh booking-service -r 3     # revierte a la revisión 3
set -euo pipefail

NAMESPACE="viajiamos"
DEPLOYMENT="${1:-}"
REVISION=""

usage() {
  echo "Uso: $0 <deployment> [-r revision] [-n namespace]"
  echo "  deployment  Nombre del deployment (obligatorio)"
  echo "  -r          Revisión específica (default: anterior)"
  echo "  -n          Namespace (default: viajiamos)"
  exit 1
}

[ -z "$DEPLOYMENT" ] && usage
shift

while getopts "r:n:h" opt; do
  case "$opt" in
    r) REVISION="$OPTARG" ;;
    n) NAMESPACE="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done

command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl no está instalado"; exit 1; }

echo "==> Historial de revisiones de $DEPLOYMENT"
kubectl rollout history "deployment/$DEPLOYMENT" -n "$NAMESPACE"

if [ -n "$REVISION" ]; then
  echo "==> Revirtiendo $DEPLOYMENT a la revisión $REVISION"
  kubectl rollout undo "deployment/$DEPLOYMENT" -n "$NAMESPACE" --to-revision="$REVISION"
else
  echo "==> Revirtiendo $DEPLOYMENT a la revisión anterior"
  kubectl rollout undo "deployment/$DEPLOYMENT" -n "$NAMESPACE"
fi

echo "==> Esperando rollout"
kubectl rollout status "deployment/$DEPLOYMENT" -n "$NAMESPACE" --timeout=180s

echo "==> Pods después del rollback"
kubectl get pods -n "$NAMESPACE" -l "app=$DEPLOYMENT"
echo "OK: rollback de $DEPLOYMENT completado"