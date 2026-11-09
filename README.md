# SentinelAI: sistema híbrido de detección de fraude financiero

Sistema de detección de fraude financiero orientado a producción, con pipeline de datos, API REST, dashboard web y explicabilidad de decisiones. El proyecto combina modelos de machine learning, validación de riesgos, monitoreo de salud del modelo y control de acceso por roles.

## Integrantes

- Bedon Silva, Yefli
- Ramirez Mendez, Juan Aldair
- Principe Carrasco, Augusto
- Ferrer Melgarejo, Jairo Lee

## Docente

Dr. Cesar Hernan Patricio Peralta

## Curso

Inteligencia Artificial - Facultad de Ingeniería de Software

## Objetivo del proyecto

Construir un sistema operativo para evaluar transacciones financieras sospechosas, priorizar riesgo, explicar decisiones al analista y exponer la funcionalidad mediante una API y una interfaz web.

## Capacidades principales

- Inferencia de riesgo sobre transacciones financieras
- Modelos híbridos con enfoque en XGBoost y comparación de rendimiento
- Interpretabilidad con SHAP
- API REST con autenticación opcional y RBAC
- Dashboard para overview, análisis y modelo
- Endpoints de salud y monitoreo
- Cobertura de pruebas backend/frontend y E2E
- Contenerización con Docker y orquestación local con Docker Compose

## Metodología

El proyecto sigue la metodología CRISP-DM para la cadena completa de valor de ML:

1. Comprensión del negocio
2. Comprensión de los datos
3. Preparación de los datos
4. Modelado
5. Evaluación
6. Despliegue y operación

## Stack tecnológico

### Backend

- Python 3.10+
- FastAPI
- Pydantic v2
- SQLAlchemy
- Alembic
- PostgreSQL / SQLite para entornos locales
- JWT + Argon2 para seguridad
- SlowAPI para rate limiting
- Prometheus instrumentation

### Frontend

- React 19
- TypeScript
- Vite
- React Router
- TanStack Query
- Vitest + Testing Library
- Playwright

### ML y análisis

- Pandas, NumPy, scikit-learn
- XGBoost
- CatBoost, LightGBM
- SHAP
- Joblib y artefactos persistidos

### Infraestructura y calidad

- Docker + Docker Compose
- GitHub Actions
- Ruff
- ESLint + Prettier
- Pytest + coverage

## Estructura del repositorio

```text
fraude-financiero-hibrido/
├── backend/                     # API y servicios backend
│   ├── app/                     # Aplicación FastAPI
│   ├── migrations/              # Migraciones Alembic
│   ├── tests/                   # Tests del backend
│   ├── artifacts/               # Contratos, metadata y snapshots
│   ├── requirements.txt         # Dependencias de runtime
│   ├── requirements-dev.txt     # Dependencias de desarrollo
│   └── pyproject.toml           # Configuración de Ruff y pytest
├── frontend/                    # Aplicación web React
│   ├── src/                     # Código fuente del frontend
│   ├── e2e/                     # Pruebas E2E de Playwright
│   ├── package.json             # Scripts y dependencias de UI
│   └── vite.config.ts          # Configuración de Vite
├── config/                     # Configuraciones compartidas
├── data/                       # Datos locales y no versionados
├── docs/                       # Documentación técnica
├── logs/                       # Logs de ejecución
├── notebooks/                  # Jupyter notebooks
├── models_saved/               # Modelos entrenados exportados
├── reports/                    # Reportes y resultados
├── src/                        # Código de ML experimental / soporte
├── pipeline_completo.py         # Pipeline unificado del proyecto
├── docker-compose.yml           # Orquestación local con PostgreSQL + API
├── Makefile                    # Comandos de entorno y pipeline
├── requirements.txt             # Dependencias del pipeline ML general
├── package.json                 # Hoja de herramientas del repo base
├── README.md                   # Documentación principal
├── .gitignore                  # Exclusiones de artefactos y cachés
├── commitlint.config.js        # Reglas de commit
├── docs/                       # Documentación general del sistema
├── frontend/README.md          # Guía específica del frontend
└── .github/                    # CI/CD
```

## Requisitos previos

- Python 3.10 o superior (recomendado 3.12/3.13)
- Node.js 20+
- npm
- Docker + Docker Compose
- Git

## Configuración del entorno

### 1) Clonar el proyecto

```bash
git clone <repo-url>
cd fraude-financiero-hibrido
```

### 2) Crear entorno virtual Python

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Instalar dependencias del pipeline ML

```bash
pip install -r requirements.txt
```

### 4) Instalar dependencias de la API backend

```bash
pip install -r backend/requirements.txt
pip install -r backend/requirements-dev.txt
```

### 5) Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con variables como:

```env
APP_ENV=development
POSTGRES_USER=fraud_user
POSTGRES_PASSWORD=change_me
POSTGRES_DB=fraud_detection
POSTGRES_PORT=5432
API_PORT=8000
JWT_SECRET_KEY=super-secret-key-at-least-32-chars
AUTH_ENABLED=true
AUTH_BOOTSTRAP_USERNAME=admin
AUTH_BOOTSTRAP_PASSWORD=change_me
AUTH_COOKIE_SECURE=false
```

> El backend también puede cargar configuración desde `backend/.env` si se desea aislar el entorno del servicio.

## Arranque rápido

### Opción A: con Docker Compose

```bash
docker compose up --build
```

Esto levanta:

- PostgreSQL en `localhost:5432`
- API FastAPI en `http://localhost:8000`

La API expone documentación OpenAPI en:

- `http://localhost:8000/api/v1/docs`
- `http://localhost:8000/api/v1/openapi.json`

### Opción B: ejecutar backend localmente

```bash
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Opción C: ejecutar frontend localmente

```bash
cd frontend
npm install
npm run dev
```

La interfaz queda disponible en:

- `http://localhost:8443`

## Ejecutar el pipeline completo

Para generar artefactos del sistema de ML, ejecutar el pipeline unificado:

```bash
python pipeline_completo.py
```

También está disponible el shortcut de Makefile:

```bash
make setup
make install
make pipeline
```

## Calidad y pruebas

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm run test
npm run build
```

### E2E

```bash
cd frontend
npx playwright install --with-deps chromium
npm run e2e
```

### Lint y formato

```bash
cd frontend
npm run lint
npm run format:check
```

## Seguridad y autenticación

La API soporta autenticación JWT opcional y control de acceso por roles. En modo autenticado, se usan cookies seguras y hashes de contraseña con Argon2. Los roles típicos del sistema incluyen:

- `admin`
- `analyst`
- `viewer`

El flujo principal incluye:

- login de usuario
- tokens de acceso y refresh
- revocación por sesión
- protección contra abuso con rate limiting
- cabeceras de seguridad y CORS controlado

## Documentación del proyecto

Se recomienda consultar la documentación técnica en:

- [docs/architecture.md](docs/architecture.md)
- [docs/database_schema.md](docs/database_schema.md)
- [docs/deployment.md](docs/deployment.md)

## Reglas de contribución

- Mantener pruebas y validaciones antes de enviar cambios
- No agregar artefactos generados al control de versiones
- Revisar contratos y artefactos del modelo antes de cambios de inferencia
- Usar commits descriptivos y seguir la convención del repo

## Licencia

Este proyecto es de propósito académico y de investigación.

## Año

2026
