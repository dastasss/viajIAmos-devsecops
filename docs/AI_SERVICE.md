# AI Service (recomendaciones de rutas)

## Qué hace

`POST /v1/ai/recommendations` recibe origen, destino y pasajeros, y responde
con ruta recomendada, tarifa estimada (CLP) y duración.

```json
{
  "origin": "Santiago",
  "destination": "Valparaíso",
  "passengers": 2
}
```

```json
{
  "origin": "Santiago",
  "destination": "Valparaíso",
  "route": "Ruta directa por carretera (~115 km)",
  "fare_clp": 84500,
  "duration_minutes": 130,
  "provider": "heuristic",
  "model": null
}
```

## Proveedores (por variable de entorno)

| `AI_PROVIDER` | Proveedor | Requiere | Uso |
|---|---|---|---|
| `off` (default) | Heurístico determinista | nada | CI, demos, fallback |
| `ollama` | LLM local gratuito | contenedor `ollama/ollama` | dev/demo local |
| `openai` | API compatible OpenAI | `AI_API_KEY` | producción |

**Degradación automática**: si el proveedor externo falla (timeout, error,
sin llave), responde con el heurístico y registra la métrica
`ai_fallback_total` — el servicio nunca deja de responder.

## Docker Compose con IA local real (Ollama)

```bash
docker compose --profile ai-local up -d
docker exec viajiamos-ollama-1 ollama pull llama3.2   # descarga el modelo
docker compose up -d ai-service                        # con AI_PROVIDER=ollama
```

Para activar: exporta `AI_PROVIDER=ollama` y `AI_MODEL=llama3.2` antes del
`up`, o edita `docker-compose.yml`.

## Kubernetes (Fase 2)

- `AI_PROVIDER` y `AI_MODEL` en `k8s/configmaps/ai-config.yaml`.
- `AI_API_KEY` vía Secret (`k8s/secrets/ai-secret.yaml` → `secretKeyRef`),
  alimentada por GitLab CI variables (masked) o GCP Secret Manager.

## Métricas propias

- `ai_requests_total{provider}` — uso por proveedor.
- `ai_fallback_total{reason}` — degradaciones (visible en dashboards).

## Tests

`services/ai-service/tests/test_recommender.py`: heurístico determinista,
proveedores mockeados, fallback ante errores. Corren sin llaves en CI.