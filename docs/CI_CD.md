# Pipeline CI/CD

Dos pipelines equivalentes por etapas: **GitHub Actions** (activo) y
**GitLab CI** (preparado para la Fase 2 con GCP).

## Etapas (iguales en ambos)

```
build → test → security → integration → deploy
```

| Etapa | GitHub Actions | GitLab CI |
|---|---|---|
| Build de imágenes (multi-stage, cache de capas) | `build` (buildx + gha cache) | `docker-build` (dind) |
| Tests unitarios | `test` (matrix 6 servicios) | `test` (parallel matrix) |
| Escaneo de secretos | `security-secrets` (Gitleaks) | `gitleaks` |
| SAST de código | `security-sast` (Bandit) | `bandit` |
| Vulnerabilidades de dependencias | `security-deps` (pip-audit) | `pip-audit` |
| Escaneo de imágenes | Trivy (post-build) | Trivy (post-build) |
| Integración end-to-end | `integration` (compose + smoke) | `integration` |
| Validación manifiestos K8s | `deploy-dry-run` (kustomize) | — |
| Deploy GKE | `deploy-gke` (manual) | `deploy-gke` (manual) |

## Gestión de variables y secretos

### GitHub Actions
- Repo → Settings → Secrets and variables → Actions:
  - **Secret** `GCP_SA_KEY` (JSON de la Service Account de GCP, solo Fase 2)
  - **Variable** `GCP_PROJECT_ID`, `GKE_CLUSTER`, `GKE_REGION`
- `GITHUB_TOKEN` se usa para el push a GHCR (permisos `packages: write`).

### GitLab CI
- Settings → CI/CD → Variables:
  - `GCP_SA_KEY` → **Protected + Masked** (solo se muestra como `[MASKED]`)

## Caché de capas Docker
- GitHub Actions: `type=gha` (cache compartido por repo, modo `max`).
- GitLab CI: `--cache-from` con la imagen del commit anterior.

## Gates de seguridad (bloquean el merge)
1. Gitleaks encuentra un secreto → pipeline rojo.
2. Trivy detecta HIGH/CRITICAL en una imagen → pipeline rojo.
3. pip-audit reporta vulnerabilidad → pipeline rojo.
4. Bandit: reporte como artefacto (revisión, no bloqueo por defecto).

## Release
1. Merge a `main` → build, test, security, integration.
2. `deploy-gke` se ejecuta **manualmente** (workflow_dispatch / job manual).
3. El tag `:latest` y el tag `:$SHA` quedan en el registry.
4. Rollback de release: ver `docs/RUNBOOK.md`.