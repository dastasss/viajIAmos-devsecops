# Guía de troubleshooting

Flujo estándar ante cualquier incidente. Sigue los 5 pasos en orden.

## Paso 0 — Estado global

```bash
kubectl get pods,deployments,services,hpa -n viajiamos
kubectl get events -n viajiamos --sort-by=.lastTimestamp | tail -20
```

## Paso 1 — Pod caído o degradado

```bash
./scripts/diagnose-pod.sh booking-service        # describe + logs + events
kubectl describe pod <pod> -n viajiamos          # CrashLoopBackOff? ImagePullBackOff?
```

Causas frecuentes:
- **ImagePullBackOff**: imagen no existe en el registry o tag equivocado.
  Verificar `kubectl describe pod` → el evento muestra el error exacto.
- **CrashLoopBackOff**: el proceso muere al arrancar. Ver logs:
  `kubectl logs <pod> -n viajiamos --previous=true`.
- **Pending**: sin recursos (HPA/saturación de nodos): `kubectl describe pod` →
  eventos de scheduling.

## Paso 2 — Probes fallando

```bash
kubectl describe pod <pod> -n viajiamos | grep -A5 -i probe
# Liveness/readiness en /healthz y /readyz (HTTP 200)
```

Si readiness falla, el pod queda sin tráfico (Service lo excluye).
Causas típicas: puerto equivocado, app lenta al arrancar (subir
`initialDelaySeconds`), dependencia externa caída.

## Paso 3 — Latencia o errores 5xx

```bash
# Métricas del servicio
curl http://localhost:9090/api/v1/query?query=rate(http_errors_total[5m])
# o en Cloud Monitoring: TasaErrorAlta / LatenciaAlta
kubectl logs -n viajiamos -l app=gateway --tail=200
```

## Paso 4 — DNS / conectividad entre servicios

```bash
./scripts/check-net.sh              # resolución DNS + HTTP de todos los servicios
kubectl get svc,ep -n viajiamos     # endpoints del Service (pods detrás)
```

`pending` en los endpoints = selector mal escrito o pods no listos.

## Paso 5 — Rollback

Si el problema comenzó tras un deploy reciente:

```bash
./scripts/rollback.sh <deployment>
```

## Guía rápida por síntoma

| Síntoma | Primer comando | Solución típica |
|---|---|---|
| Pod `CrashLoopBackOff` | `kubectl logs <pod> --previous` | Fix de código + re-deploy, o rollback |
| `ImagePullBackOff` | `kubectl describe pod` | Tag de imagen no existe; corregir CI |
| Pod `Pending` | `kubectl describe pod` | Aumentar límites o nodos |
| 502 del gateway | logs del gateway + `check-net.sh` | Servicio upstream caído; escalar o rollback |
| HPA escalando sin control | `kubectl get hpa -o yaml` | Revisar requests de CPU de los deployments |
| Socket.IO desconectando clientes | logs de realtime-service | Reinicios del pod → rollback del realtime |

## Cierre de incidente

1. Registrar la causa raíz en el README del incidente.
2. Convertir la lección en **alerta o test automático** (prevenir recurrencia).
3. Actualizar este runbook si el flujo cambió.