# Runbook de despliegue y operación

Este runbook documenta el ciclo de vida operativo de ViajIAmos:
despliegue, release candidates, rollback y restauración de ambientes.
Objetivo: que QA y desarrollo operen **sin depender de una persona específica**.

## 1. Despliegue (rolling update)

```bash
./scripts/deploy.sh                      # aplica k8s/ (kustomize) y espera rollout
kubectl get pods -n viajiamos -w         # observar el progreso en vivo
```

Estrategia de los deployments: `maxUnavailable: 0, maxSurge: 1` → cero downtime.

## 2. Release candidate (RC)

1. `build` + `test` + `security` verdes en CI (ver `docs/CI_CD.md`).
2. La imagen `:latest` (y el tag con SHA) queda en GHCR/GitLab Registry.
3. Aplicar en el ambiente de QA: `./scripts/deploy.sh -n viajiamos-qa`.
4. QA valida → se promueve a producción con el mismo deploy, apuntando al SHA validado.
5. Los ambientes se separan por namespace (viajiamos / viajiamos-qa / viajiamos-staging).

## 3. Rollback

Cuando un release se comporta mal (errores, latencia, crash loops):

```bash
./scripts/rollback.sh booking-service            # revierte al release anterior
./scripts/rollback.sh booking-service -r 3       # o a una revisión específica
kubectl get rs -n viajiamos                      # historial de ReplicaSets
```

Regla: si la alerta crítica entra en los primeros 10 minutos post-deploy,
**rollback inmediato** (no intentar parchear en caliente).

## 4. Restauración de ambiente corrompido

Síntomas: pods en `CrashLoopBackOff`, secrets/configmaps apuntando a valores viejos,
HPA escalando sin control.

```bash
# 1. Diagnóstico (ver TROUBLESHOOTING.md)
./scripts/diagnose-pod.sh booking-service

# 2. Restaurar configmap/secret desde el repo (declarativo)
kubectl apply -k k8s/

# 3. Si el ambiente quedó irreparable, recrear el namespace limpio:
kubectl delete namespace viajiamos
./scripts/deploy.sh
```

## 5. Ventanas de despliegue

- **QA/staging**: cada merge a `main` (automático).
- **Producción**: ventana coordinada (ej. martes/jueves 10:00-12:00) con
  `workflow_dispatch` en GitHub Actions o job `manual` en GitLab CI.

## 6. Checklist de release

- [ ] Pipeline completo verde (build, test, security, integration)
- [ ] Escaneo Trivy sin HIGH/CRITICAL
- [ ] Gitleaks sin hallazgos
- [ ] Smoke test end-to-end OK
- [ ] Rollback probado en QA antes del deploy a producción
- [ ] Dashboards y alertas monitoreando los nuevos endpoints