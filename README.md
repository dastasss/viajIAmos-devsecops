# ViajIAmos — Plataforma demo de transporte de pasajeros (DevOps / DevSecOps)

Proyecto portafolio de **DevOps/DevSecOps Junior**: microservicios Dockerizados,
orquestados en Kubernetes, con CI/CD completo (GitHub Actions + GitLab CI
preparado para GKE), observabilidad y seguridad integrada desde el pipeline.

```
                            ┌─────────────┐
   Cliente ────HTTP────────►│   Gateway   │  (único punto de entrada)
   Socket.IO───────────────►│   :8000     │
                            └──────┬──────┘
                                   │ service discovery (DNS)
         ┌─────────────┬───────────┼─────────────┬─────────────┐
         ▼             ▼           ▼             ▼             ▼
   ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐
   │  booking  │ │  payment  │ │  driver   │ │ realtime  │ │    ai     │
   │ :8001     │ │ :8002     │ │ :8003     │ │ :8004     │ │ :8005     │
   │ reservas  │ │ pagos     │ │ conduct.  │ │ Socket.IO │ │ LLM+fallbk│
   └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────┘
        └─────────────── /metrics estilo Prometheus (GMP) ─────────┘
```

## Quickstart (local, sin GCP ni tarjeta)

```bash
# 1. Levantar el stack completo
docker compose up -d --build

# 2. Smoke test end-to-end (reserva → pago → conductor → evento → IA)
python tests/smoke_test.py

# 3. (Opcional) IA real local con Ollama
docker compose --profile ai-local up -d && docker exec viajiamos-ollama-1 ollama pull llama3.2
```

## Kubernetes (kind local / minikube / GKE)

> kind es la opción recomendada: Docker Desktop dejó de incluir Kubernetes
> embebido (v4.66+). El repo incluye `k8s/kind-config.yaml` ya probado.

```bash
# 1. Crear cluster kind (una vez)
kind create cluster --name viajiamos --config k8s/kind-config.yaml

# 2. Construir imágenes y cargarlas al cluster
docker compose build
for img in gateway booking-service payment-service driver-service realtime-service ai-service; do
  docker tag viajiamos/$img:local ghcr.io/viajiamos-demo/$img:latest
  kind load docker-image ghcr.io/viajiamos-demo/$img:latest --name viajiamos
done

# 3. Desplegar todo el stack (29 recursos) y verificar rollout
kubectl apply -k k8s/
kubectl rollout status deployment -n viajiamos --timeout=240s

# 4. Acceso y smoke test contra el cluster
kubectl port-forward -n viajiamos svc/gateway 18000:8000
python tests/smoke_test.py --base http://localhost:18000   # (SMOKE_TIMEOUT=25 si el cluster está frío)
./scripts/healthcheck.sh                                   # verifica todos los servicios
```

## Estructura

```
├── services/            # 6 microservicios FastAPI (multi-stage, no-root)
├── k8s/                 # deployments, services, configmaps, secrets,
│                        # ingress, HPA, NetworkPolicies, RBAC (kustomize)
├── .github/workflows/   # CI/CD: build → test → security → integration → deploy
├── .gitlab-ci.yml       # GitLab CI espejo (Fase 2: GitLab + GKE)
├── scripts/             # deploy, rollback, diagnose-pod, collect-logs,
│                        # healthcheck, check-net (Bash)
├── monitoring/          # prometheus.yml + reglas de alertas
├── docs/                # RUNBOOK, TROUBLESHOOTING, CI_CD, SECURITY,
│                        # ALERTS, AI_SERVICE
└── tests/               # smoke test end-to-end
```

## Documentación

| Doc | Contenido |
|---|---|
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | Deploy, release candidates, rollback, restauración |
| [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | Diagnóstico de 5 pasos + guía por síntoma |
| [docs/CI_CD.md](docs/CI_CD.md) | Pipelines, variables, secretos, gates |
| [docs/SECURITY.md](docs/SECURITY.md) | Hardening, escaneos, secretos, red, RBAC |
| [docs/ALERTS.md](docs/ALERTS.md) | Alertas log-based de alto impacto |
| [docs/AI_SERVICE.md](docs/AI_SERVICE.md) | Motor de IA multi-proveedor |
| [monitoring/README.md](monitoring/README.md) | Métricas y dashboards |

## Seguridad (resumen)

- Imágenes multi-stage con usuario no-root; `securityContext` completo
  (readOnlyRootFilesystem, drop ALL capabilities, seccomp).
- Pipeline con **Gitleaks** (secretos), **Trivy** (imágenes),
  **pip-audit** (dependencias), **Bandit** (SAST).
- NetworkPolicies default-deny + RBAC de mínimo privilegio.
- Secretos vía Kubernetes Secrets / variables protegidas de CI (nunca en repo).

## Roadmap (Fase 2 — GitLab + GCP)

1. Mirror del repo a GitLab.com y activación de `.gitlab-ci.yml`.
2. Cuenta GCP (free trial $300) → cluster GKE.
3. Deploy real vía pipeline (job `deploy-gke` manual) → rolling updates/rollbacks reales.
4. GCP Managed Prometheus + Cloud Monitoring: dashboards y alertas.
5. Alertas log-based de `docs/ALERTS.md` (pagos, booking, Socket.IO, conductores).
6. AI service con `AI_PROVIDER=openai` y llave vía Secret Manager.

## Licencia

MIT — ver [LICENSE](LICENSE).