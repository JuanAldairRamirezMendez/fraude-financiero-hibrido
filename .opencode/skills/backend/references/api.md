# API backend

Base `/api/v1`. Usa estados HTTP coherentes y `{ code, message, requestId, details? }` para errores. Las listas usan `page`, `pageSize`, `q`, `sort` y `order`. Cambios incompatibles requieren nueva version. `POST /analyze` acepta `Idempotency-Key`.
