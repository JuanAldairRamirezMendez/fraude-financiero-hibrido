# Errores

El cliente conserva `status`, `code` y `requestId`. Convierte 422 en errores de campo; distingue red, 401, 403, 429 y 503. Muestra mensajes utiles y el requestId para soporte, sin stack traces.
