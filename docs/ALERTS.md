# Alertas log-based (Cloud Logging)

En producción (GKE + GCP), las alertas log-based se crean en
**Cloud Logging → Log-based Alerts** (o **Log Analytics → Create alert**) sobre
los logs estructurados de los microservicios. Cada regla define una consulta
(log filter), un umbral de ocurrencias en un período y un canal de notificación.

## Reglas de alto impacto operativo (mapeadas al cargo)

### 1. Fallo en el flujo de pago
Los pagos fallidos deben alertar de inmediato: dinero en juego.

```
severity>=ERROR AND
resource.labels.namespace_name="viajamos" AND
logName:"payment-service" AND
(payload.message:"pago" OR payload.message:"payment") AND
payload.message:"fall" OR payload.message:"error")
```
**Umbral**: ≥ 3 ocurrencias en 5 minutos → `severity: critical`

Implementación en el servicio: `app/api.py` de `payment-service` emite
`log.error("Pago rechazado ...")` en fallos.

### 2. Errores de booking sin respuesta
Reservas que quedan en el limbo (timeout de confirmación).

```
logName:"booking-service" AND
(payload.message:"timeout" OR payload.message:"sin respuesta" OR payload.message:"no response")
```
**Umbral**: ≥ 3 en 5 minutos → `severity: warning`

### 3. Reinicios anómalos del Socket.IO del monolito/realtime
El servicio de tiempo real es sensible a crash loops: los clientes conectados
se caen todos a la vez.

```
logName:"realtime-service" AND
(payload.message:"reinicio" OR payload.message:"restart" OR payload.message:"startup")
```
**Umbral**: ≥ 2 en 10 minutos → `severity: critical`

### 4. Timeouts de aceptación de conductor
El conductor no acepta el viaje a tiempo (SLI del flujo de asignación).

```
logName:"driver-service" AND
(payload.message:"timeout de aceptación" OR payload.message:"accept timeout")
```
**Umbral**: ≥ 5 en 15 minutos → `severity: warning`

## Configuración en GCP (Fase 2)

```bash
# gcloud CLI (se ejecuta en el pipeline / runbook):
gcloud logging alerts create "fallo-pago" \
  --description="Alertas de fallos en el flujo de pago" \
  --log-filter='logName:"payment-service" AND severity>=ERROR' \
  --condition-count=3 --condition-period=300s \
  --notification-channels="projects/PROJECT/notificationChannels/CHANNEL_ID"
```

Alternativa: exportar estas reglas como Terraform (`google_monitoring_alert_policy`)
para que sean revisables en el repo — se incluye como mejora de la Fase 2.

## Canales de notificación recomendados
- Email (P1/P2)
- Slack/Google Chat (P1/P2)
- PagerDuty (solo críticas)

## Runbook de respuesta
Ante cualquier alerta crítica: ver `docs/TROUBLESHOOTING.md` — flujo de diagnóstico
de 5 pasos (describe → logs → events → metrics → rollback).