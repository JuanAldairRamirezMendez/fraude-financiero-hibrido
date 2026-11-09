# Contract first

`backend/openapi.json` es la fuente de verdad. Tras cambiar endpoints, actualiza el esquema, ejecuta `pnpm gen:api` y revisa el diff generado. No mantengas tipos de respuesta duplicados manualmente.
