# Observabilidad backend

Logs JSON con timestamp, level, requestId, correlationId, route, status, durationMs y modelVersion. `/health/live` mide proceso; `/health/ready` modelo, artefactos y DB. Metricas Prometheus; trazas OpenTelemetry opcionales. No filtres stack al cliente.
