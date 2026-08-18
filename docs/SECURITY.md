# Seguridad (DevSecOps)

Medidas implementadas en ViajIAmos, alineadas con el rol de DevSecOps:
ejecutar las medidas definidas por el equipo sin tomar decisiones de seguridad
de forma autónoma.

## 1. Imágenes contenedor (hardening)

- **Multi-stage builds**: etapa builder + runtime mínimo (`python:3.13-slim`).
- **Usuario no-root**: `appuser` (uid 10001), sin shell.
- `securityContext` en Kubernetes:
  - `runAsNonRoot: true`, `runAsUser: 10001`
  - `allowPrivilegeEscalation: false`
  - `readOnlyRootFilesystem: true`
  - `capabilities.drop: ["ALL"]`
  - `seccompProfile: RuntimeDefault`
- Namespace con Pod Security `restricted` (`pod-security.kubernetes.io/enforce`).

## 2. Escaneo en el pipeline

| Herramienta | Qué detecta | Fase |
|---|---|---|
| Gitleaks | Secretos/llaves commiteados | `security-secrets` |
| Trivy | Vulnerabilidades en imágenes | post-build |
| pip-audit | Vulnerabilidades en dependencias Python | `security-deps` |
| Bandit | Malas prácticas de código (SAST) | `security-sast` |

## 3. Gestión de secretos

- **Nunca** en el repo: la llave de IA viaja como:
  - variable `masked/protected` en CI, e
  - inyectada como **Kubernetes Secret** → `secretKeyRef` en el deployment
    (`k8s/secrets/ai-secret.yaml` es un placeholder).
- En GCP (Fase 2): **Secret Manager** + `external-secrets` o variables de CI.
- `gitleaks` en CI falla si alguien commitea una llave (política automática).

## 4. Red (microsegmentación)

- NetworkPolicies (`k8s/network-policies.yaml`):
  1. Default-deny de ingreso al namespace.
  2. Solo el **gateway** alcanza los servicios internos.
  3. Solo el gateway es expuesto al exterior (ingress).
- Los servicios internos son `ClusterIP`: no hay puertos públicos.

## 5. RBAC de mínimo privilegio

- `ServiceAccount app-sa` con rol de solo lectura en su namespace
  (`k8s/rbac.yaml`): los pods no pueden mutar recursos del clúster.

## 6. HTTP (application layer)

- Security headers en todos los servicios:
  `X-Content-Type-Options`, `X-Frame-Options`, `Content-Security-Policy`,
  `Referrer-Policy`, `Strict-Transport-Security`.
- `Server: ViajIAmos` (no revela versión de framework).
- Validación de entrada con Pydantic (422 en payloads malformados).

## Límites del rol (importante)

Como DevSecOps junior: **ejecutar y automatizar** las medidas definidas por el
Ingeniero DevSecOps, **no tomar decisiones de seguridad** (ej. aceptar o
descartar un hallazgo de Trivy por cuenta propia) — escalar al dueño de la
decisión. Esto está documentado como práctica del equipo.