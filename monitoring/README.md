# Monitoreo de ViajIAmos

Métricas expuestas por cada microservicio en `/metrics` (formato Prometheus),
escrapeables por **GCP Managed Prometheus (GMP)** en GKE:

| Métrica | Descripción | Alerta asociada |
|---|---|---|
| `http_requests_total` | Conteo por método, ruta y código | — |
| `http_request_duration_seconds` | Histograma de latencia | `LatenciaAlta` (p95 > 2s) |
| `http_errors_total` | Errores 5xx | `TasaErrorAlta` (> 5% en 5m) |
| `up` | Disponibilidad del endpoint | `ServicioCaido` (2m sin respuesta) |
| `kube_pod_container_status_restarts_total` | Reinicios de pods (GKE) | `PodReiniciandose` |
| `container_cpu_usage_seconds_total` | Uso de CPU (GKE) | `SaturaciónCPU` (> 85% límite) |
| `ai_requests_total` / `ai_fallback_total` | Uso del motor IA / fallbacks | — |

## Uso local (opcional)

```bash
docker run -d --name prom -p 9090:9090 \
  -v $PWD/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $PWD/monitoring/alert-rules.yml:/etc/prometheus/alert-rules.yml \
  prom/prometheus
# UI: http://localhost:9090
```

## En GCP (Fase 2)

1. **Dashboards Cloud Monitoring**: crear widgets por microservicio
   (latencia p95, error rate, disponibilidad, CPU/memoria) con las métricas de GMP.
2. **Alertas**: `monitoring/alert-rules.yml` traducidas a `google_monitoring_alert_policy`.
3. **Alertas log-based**: ver `docs/ALERTS.md` (los 4 eventos de alto impacto).