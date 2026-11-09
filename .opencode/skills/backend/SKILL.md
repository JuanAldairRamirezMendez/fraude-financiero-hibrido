---
name: Backend Engineering
description: Guia para implementar y revisar el backend FastAPI por capas, con dominio puro, DI explicita, persistencia SQLite/Alembic, seguridad, observabilidad y pruebas.
---

# Backend Engineering

Usa esta skill al trabajar en `backend/`.

## Reglas obligatorias
- Controladores validan y traducen HTTP; no contienen logica de negocio.
- Servicios orquestan casos de uso; repositorios encapsulan acceso a datos.
- El dominio no importa FastAPI, SQLAlchemy ni Pydantic.
- Valida con Pydantic v2 y `extra="forbid"`; configura por entorno.
- Usa DI explicita, transacciones, idempotencia, timeouts y errores uniformes.
- Carga artefactos en `lifespan` y falla rapido si modelo/preprocesador faltan.
- Logs JSON con `requestId`; nunca filtres stack traces ni datos sensibles.

## Checklist de PR
- [ ] Endpoint, servicio, repositorio y esquema tienen responsabilidades separadas.
- [ ] Hay unitarias e integracion para casos felices, limites y errores.
- [ ] Migraciones Alembic y rollback son reproducibles.
- [ ] `/health` distingue liveness y readiness.
- [ ] Se ejecutan `ruff`, `mypy` y `pytest`.

## Antipatrones
Logica en routers, SQL concatenado, excepciones ocultas, estado compartido en memoria y llamadas externas sin timeout.

## Comandos
`cd backend && ruff check . && mypy app && pytest`
