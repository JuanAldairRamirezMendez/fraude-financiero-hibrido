# Despliegue y operación

## Modelo de despliegue

La aplicación se publica como un único contenedor Docker:

1. La primera etapa instala dependencias Node y compila `frontend` con Vite.
2. La segunda etapa instala dependencias Python y copia el backend, los
	 artefactos y el frontend compilado.
3. `docker-entrypoint.sh` ejecuta `alembic upgrade head`.
4. Uvicorn inicia FastAPI en `0.0.0.0:${PORT:-8000}`.

FastAPI sirve el frontend compilado desde `frontend/dist` y hace fallback de
las rutas del navegador hacia `index.html`. El mismo servicio expone la API en
`/api/v1`.

## Requisitos

- Docker y Docker Compose para el entorno local.
- Python 3.13 y Node 22 para validaciones directas.
- El modelo `models_saved/xgboost_tier2_isotonic.pkl`.
- Los artefactos de `backend/artifacts/`.
- PostgreSQL en producción.

## Variables de entorno del backend

Configuración mínima recomendada para producción:

```env
APP_ENV=production
DATABASE_URL=postgresql+psycopg://user:password@host:5432/fraud_detection
AUTH_ENABLED=true
JWT_SECRET_KEY=una-clave-aleatoria-de-al-menos-32-caracteres
AUTH_BOOTSTRAP_USERNAME=admin
AUTH_BOOTSTRAP_PASSWORD=una-contraseña-segura
AUTH_COOKIE_SECURE=true
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash
FAIL_FAST=true
```

Los secretos deben configurarse en el gestor de variables del proveedor. No
deben escribirse en el repositorio, el Dockerfile ni la imagen.

`GEMINI_API_KEY` es opcional para arrancar la API, pero el endpoint de chat
responderá `503` si no existe.

## Variables del frontend

El frontend se compila dentro de Docker, por lo que estas variables deben
estar disponibles durante la fase de build:

```env
VITE_API_BASE_URL=
VITE_USE_MOCKS=false
```

Si frontend y API comparten origen, `VITE_API_BASE_URL` puede quedar vacío.
`VITE_USE_MOCKS=false` es obligatorio para que Analyzer, Overview y Models
consuman la API real. Si se omite, el código activa mocks por compatibilidad
con desarrollo.

Las variables `VITE_*` no son secretos: quedan incorporadas en JavaScript
durante la compilación. Nunca se debe colocar `GEMINI_API_KEY` en el frontend.

## Desarrollo local con Docker Compose

Crear `.env` con, como mínimo, `POSTGRES_PASSWORD`,
`AUTH_BOOTSTRAP_PASSWORD` y `JWT_SECRET_KEY`, y ejecutar:

```bash
docker compose up --build
```

Servicios disponibles:

- PostgreSQL: `localhost:5432`
- Aplicación: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/api/v1/docs`
- Healthcheck: `http://localhost:8000/api/v1/health/ready`

El contenedor espera a que PostgreSQL esté saludable y luego ejecuta las
migraciones antes de iniciar la API.

## Ejecución sin Docker

Backend:

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
VITE_USE_MOCKS=false npm run dev
```

En este modo, el frontend se sirve normalmente en `http://localhost:8443` y
usa CORS contra el backend local.

## Railway

El flujo esperado es:

```text
push a main
	-> Railway detecta el commit
	-> construye Dockerfile
	-> inyecta variables
	-> ejecuta migraciones
	-> inicia Uvicorn
	-> comprueba /api/v1/health/ready
```

Configurar en Railway:

- `DATABASE_URL` apuntando a PostgreSQL.
- `APP_ENV=production`.
- `AUTH_ENABLED=true`.
- `JWT_SECRET_KEY` y credenciales bootstrap seguras.
- `AUTH_COOKIE_SECURE=true`.
- `GEMINI_API_KEY` si se habilita el copiloto.
- `VITE_USE_MOCKS=false` como variable de build.
- `VITE_API_BASE_URL` vacío si el frontend se sirve desde el mismo dominio.

La pantalla `Cases` consume la API real; requiere `VITE_USE_MOCKS=false` y una
sesión autenticada cuando `AUTH_ENABLED=true`.

Después de cada despliegue, verificar:

```bash
curl --fail https://<dominio>/api/v1/health/ready
curl --fail https://<dominio>/api/v1/openapi.json
```

El estado `ok` requiere modelo, preprocesador, snapshot y base de datos
disponibles. Un estado `degraded` indica que el proceso vive, pero no está
listo para operar todas las funciones.

## Operación y recuperación

Antes de actualizar el modelo:

1. Validar que el contrato de features coincide con el preprocesador.
2. Validar la metadata y el hash del artefacto.
3. Ejecutar pruebas backend, frontend y E2E.
4. Construir la imagen y probar `/api/v1/health/ready`.
5. Conservar la imagen anterior para rollback.

Para una base PostgreSQL, ejecutar backups fuera del host de la aplicación y
probar periódicamente un restore en una base aislada. Consultar
`docs/operations.md` y los scripts de `ops/` para los comandos disponibles.

## Validación de calidad

```bash
cd backend && ruff check app tests && pytest
cd ../frontend && npm run check
```

La CI ejecuta además la construcción del contenedor y pruebas E2E cuando el
artefacto del modelo está disponible.
