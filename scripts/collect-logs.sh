#!/usr/bin/env bash
# collect-logs.sh - Recolecta los logs de todos los servicios en logs/ (tar.gz).
# Uso:
#   ./scripts/collect-logs.sh            # logs de todos los deployments
#   ./scripts/collect-logs.sh booking-service payment-service
#   ./scripts/collect-logs.sh -n staging
set -euo pipefail

NAMESPACE="viajiamos"
OUT_DIR="logs"
APPS=()

usage() {
  echo "Uso: $0 [apps...] [-n namespace]"
  echo "  apps   Deployments a recolectar (default: todos)"
  echo "  -n     Namespace (default: viajiamos)"
  exit 1
}

while [ $# -gt 0 ]; do
  case "$1" in
    -n) NAMESPACE="$2"; shift 2 ;;
    -h) usage ;;
    *) APPS+=("$1"); shift ;;
  esac
done

command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl no está instalado"; exit 1; }

if [ ${#APPS[@]} -eq 0 ]; then
  APPS=($(kubectl get deployments -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}'))
fi

mkdir -p "$OUT_DIR"
STAMP=$(date +%Y%m%d-%H%M%S)

for app in "${APPS[@]}"; do
  echo "==> Recolectando logs de $app"
  for pod in $(kubectl get pods -n "$NAMESPACE" -l "app=$app" -o name); do
    name=${pod#pod/}
    kubectl logs "$pod" -n "$NAMESPACE" --all-containers=true --prefix=true \
      > "$OUT_DIR/${name}-${STAMP}.log" 2>&1 || true
  done
done

echo "==> Comprimiendo en $OUT_DIR/viajiamos-logs-${STAMP}.tar.gz"
tar -czf "$OUT_DIR/viajiamos-logs-${STAMP}.tar.gz" "$OUT_DIR"/*-"${STAMP}".log
rm -f "$OUT_DIR"/*-"${STAMP}".log

ls -lh "$OUT_DIR"/viajiamos-logs-${STAMP}.tar.gz
echo "OK: logs recolectados"