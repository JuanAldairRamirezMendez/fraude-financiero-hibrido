# Operacion y recuperacion

## Variables obligatorias

Copiar `.env.example` a `.env` y establecer al menos `POSTGRES_PASSWORD`,
`JWT_SECRET_KEY` de 32 caracteres o mas y `AUTH_BOOTSTRAP_PASSWORD`. Los
secretos no deben escribirse en `docker-compose.yml` ni en la imagen.

## Despliegue local con Docker

```bash
docker compose up -d --build
docker compose ps
curl http://localhost:8000/api/v1/health/live
```

La API ejecuta `alembic upgrade head` antes de iniciar Uvicorn. El modelo
entrenado se monta desde `models_saved/`; el artefacto requerido debe estar
presente antes de iniciar un entorno con `FAIL_FAST=true`.

## Backup y restore

Los backups de PostgreSQL usan formato custom y deben almacenarse fuera del
host de la aplicacion.

El frontend se valida en CI con las dependencias declaradas en
`frontend/package.json`. El lockfile pnpm existente se conserva para el
entorno de desarrollo; el runner de CI debe migrar a Corepack/pnpm cuando el
toolchain quede estandarizado.

```bash
DATABASE_URL='postgresql+psycopg://user:password@host:5432/db' \
  BACKUP_DIR=/secure/backups ops/backup_database.sh

DATABASE_URL='postgresql+psycopg://user:password@host:5432/db' \
  BACKUP_FILE=/secure/backups/fraud_detection-YYYYMMDDTHHMMSSZ.dump \
  ops/restore_database.sh
```

Probar un restore periodicamente en una base aislada. El procedimiento de
restore reemplaza objetos existentes y requiere una ventana de mantenimiento.

## Rollback

1. Detener el despliegue actual y conservar la imagen anterior por su digest.
2. Desplegar la imagen anterior con la misma configuracion de secretos.
3. Solo ejecutar `alembic downgrade <revision>` tras validar compatibilidad y
   tener un backup; las migraciones nuevas deben ser backward-compatible.
4. Verificar `/api/v1/health/ready`, login y una peticion de analisis.