---
name: DevOps CI/CD
description: Guia para CI GitHub Actions, Docker multi-stage no root, compose, observabilidad, backups y despliegues reproducibles del proyecto.
---

# DevOps CI/CD

Usa esta skill al modificar `.github/workflows`, Docker, compose o despliegue.

## Reglas obligatorias
- CI ejecuta lint, tipos, tests, contrato, seguridad y build.
- Docker usa multi-stage, runtime slim, usuario no root, healthcheck y sin secretos.
- El mismo artefacto se promueve entre entornos; rollback debe estar documentado y probado.
- Compose cubre desarrollo y perfiles opcionales sin ocultar fallos.
- Alertas minimas: 5xx, p95 y modelo no disponible.
- Backups automaticos requieren restauracion probada.
- Terraform queda documentado hasta existir un destino cloud concreto.

## Checklist de PR
- [ ] Jobs reproducibles y cacheados sin saltarse validaciones.
- [ ] Versiones fijadas y escaneo de dependencias configurado.
- [ ] Imagen corre como no root y pasa healthcheck.
- [ ] Variables sensibles provienen del entorno/secret manager.
- [ ] Existe estrategia de rollback.

## Comandos
`docker compose config`, `docker build`, `docker compose up --build` y los comandos de CI.
