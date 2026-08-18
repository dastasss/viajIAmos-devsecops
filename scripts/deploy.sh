#!/usr/bin/env bash
# deploy.sh - Despliega ViajIAmos en Kubernetes (rolling update).
# Uso:
#   ./scripts/deploy.sh            # aplica k8s/ con kustomize
#   ./scripts/deploy.sh -n staging # namespace override
set -euo pipefail

NAMESPACE="viajiamos"
MANIFESTS="k8s"

usage() {
  echo "Uso: $0 [-n namespace] [-f manifiestos]"
  echo "  -n   Namespace (default: viajiamos)"
  echo "  -f   Directorio de manifiestos (default: k8s)"
  exit 1
}

while getopts "n:f:h" opt; do
  case "$opt" in
    n) NAMESPACE="$OPTARG" ;;
    f) MANIFESTS="$OPTARG" ;;
    h) usage ;;
    *) usage ;;
  esac
done

command -v kubectl >/dev/null 2>&1 || { echo "ERROR: kubectl no está instalado"; exit 1; }

echo "==> Aplicando manifiestos ($MANIFESTS) en namespace $NAMESPACE"
kubectl apply -k "$MANIFESTS"

echo "==> Esperando rollout de todos los deployments"
for dep in $(kubectl get deployments -n "$NAMESPACE" -o name); do
  kubectl rollout status "$dep" -n "$NAMESPACE" --timeout=180s
done

echo "==> Estado final"
kubectl get pods,deployments,services -n "$NAMESPACE"
echo "OK: ViajIAmos desplegado"