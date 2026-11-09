---
name: Full-stack Integration
description: Guia para conectar frontend React y backend FastAPI mediante OpenAPI como fuente de verdad, errores uniformes, validacion, sesion, cache y entornos.
---

# Full-stack Integration

Usa esta skill al modificar la frontera entre `frontend/` y `backend/`.

## Reglas obligatorias
- OpenAPI del backend es la fuente de verdad; genera tipos TS, no los dupliques a mano.
- Valida en cliente para UX y en servidor para seguridad.
- `apiRequest` conserva status, code y requestId; traduce 422 a errores de formulario.
- Usa cookies HttpOnly para sesion; nunca `localStorage`.
- Mantiene mocks y API real con el mismo contrato.
- Usa React Query para servidor y flags/entornos para activacion gradual.
- Cachea metadata/snapshot con invalidacion clara; `/analyze` usa `no-store`.

## Checklist de PR
- [ ] Contrato actualizado y tipos regenerados.
- [ ] Estados loading/error/empty cubiertos.
- [ ] Errores de red, validacion, 401, 429 y 503 tienen UX.
- [ ] Mocks siguen siendo compatibles.
- [ ] Tests unitarios, contrato y E2E afectados pasan.

## Comandos
`cd frontend && pnpm gen:api && pnpm check`
