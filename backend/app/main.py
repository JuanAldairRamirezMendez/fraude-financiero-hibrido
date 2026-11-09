from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.errors import ServiceUnavailableError, install_error_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import (
    CacheControlMiddleware,
    RequestContextMiddleware,
    SecurityHeadersMiddleware,
)
from app.core.rate_limit import limiter, rate_limit_handler
from app.core.settings import Settings, get_settings
from app.db.database import Database
from app.domain.assessment import Alert
from app.repositories.sql_repository import SqlFraudRepository
from app.services.analyze_service import AnalyzeService
from app.services.artifacts import ArtifactStore
from app.services.auth_service import AuthService
from app.services.inference_service import InferenceService
from app.services.metadata_service import MetadataService
from app.services.models_service import ModelsService
from app.services.snapshot_service import SnapshotService

logger = get_logger(__name__)


def _seed_alerts(repository: SqlFraudRepository, snapshot: SnapshotService) -> None:
    alerts = [
        Alert(
            id=str(item["id"]),
            occurred_at=str(item["occurredAt"]),
            model_id=str(item["modelId"]),
            alert_type=str(item["alertType"]),
            detail=str(item["detail"]),
            status=str(item["status"]),
        )
        for item in snapshot.alerts
    ]
    created = repository.seed_alerts(alerts)
    if created:
        logger.info("snapshot alerts seeded", extra={"count": created})


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()
    configure_logging(app_settings.log_level)
    app_settings.preprocessor_path.parent.mkdir(parents=True, exist_ok=True)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        started_at = datetime.now(UTC)
        app.state.started_at = started_at
        database = Database(
            app_settings.database_url,
            pool_size=app_settings.db_pool_size,
            max_overflow=app_settings.db_max_overflow,
        )
        database.create_all()
        repository = SqlFraudRepository(database)
        app.state.database = database
        app.state.repository = repository
        app.state.auth_service = AuthService(database, app_settings)
        app.state.auth_service.bootstrap()

        store: ArtifactStore | None = None
        inference: InferenceService | None = None
        snapshot: SnapshotService | None = None
        try:
            store = ArtifactStore.load(
                model_path=app_settings.model_path,
                preprocessor_path=app_settings.preprocessor_path,
                contract_path=app_settings.feature_contract_path,
                metadata_path=app_settings.model_metadata_path,
            )
            inference = InferenceService(store)
            snapshot = SnapshotService(
                app_settings.snapshot_path, app_settings.transactions_path
            )
            app.state.artifacts = store
            app.state.inference_service = inference
            app.state.snapshot_service = snapshot
            app.state.metadata_service = MetadataService(store)
            app.state.analyze_service = AnalyzeService(
                inference,
                repository,
                calibrated_threshold=store.calibrated_threshold,
                idempotency_ttl_hours=app_settings.idempotency_ttl_hours,
            )
            app.state.models_service = ModelsService(repository, snapshot, started_at)
            app.state.model_version = store.model_version
            if app_settings.seed_snapshot_alerts:
                _seed_alerts(repository, snapshot)
        except ServiceUnavailableError:
            if app_settings.fail_fast:
                raise
            logger.exception("artifacts unavailable; starting in degraded mode")

        logger.info(
            "application startup",
            extra={
                "environment": app_settings.environment,
                "version": app_settings.app_version,
                "modelVersion": getattr(app.state, "model_version", None),
            },
        )
        try:
            yield
        finally:
            database.dispose()
            logger.info("application shutdown", extra={"graceful": True})

    app = FastAPI(
        title=app_settings.app_name,
        version=app_settings.app_version,
        description=(
            "API de detección de fraude con XGBoost calibrado, explicaciones SHAP, "
            "snapshot real del dataset y salud de modelos."
        ),
        docs_url=f"{app_settings.api_prefix}/docs" if app_settings.enable_docs else None,
        redoc_url=f"{app_settings.api_prefix}/redoc" if app_settings.enable_docs else None,
        openapi_url=f"{app_settings.api_prefix}/openapi.json",
        lifespan=lifespan,
    )
    app.state.settings = app_settings
    app.state.limiter = limiter

    install_error_handlers(app)
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)  # type: ignore[arg-type]

    if not app_settings.is_production and app_settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=list(app_settings.cors_origins),
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Idempotency-Key", "X-Request-ID"],
            expose_headers=["X-Request-ID", "X-Response-Time-ms", "Retry-After"],
        )

    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(CacheControlMiddleware)
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(RequestContextMiddleware)

    app.include_router(api_router, prefix=app_settings.api_prefix)

    if app_settings.expose_prometheus:
        Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    static_dir = app_settings.static_dir
    assets_dir = static_dir / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/", include_in_schema=False)
    def root(request: Request):  # type: ignore[no-untyped-def]
        index = static_dir / "index.html"
        if index.exists():
            return FileResponse(index)
        return JSONResponse(
            {
                "name": app_settings.app_name,
                "version": app_settings.app_version,
                "api": app_settings.api_prefix,
                "docs": f"{app_settings.api_prefix}/docs",
                "requestId": getattr(request.state, "request_id", "unknown"),
            }
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str, request: Request):  # type: ignore[no-untyped-def]
        if full_path.startswith(("api/", "metrics")):
            return JSONResponse(
                status_code=404,
                content={
                    "code": "not_found",
                    "message": "Recurso no encontrado.",
                    "requestId": getattr(request.state, "request_id", "unknown"),
                },
            )
        candidate = (static_dir / full_path).resolve()
        try:
            candidate.relative_to(static_dir.resolve())
        except ValueError:
            candidate = static_dir / "index.html"
        if candidate.is_file():
            return FileResponse(candidate)
        index = static_dir / "index.html"
        if index.exists():
            return FileResponse(index)
        return JSONResponse(
            status_code=404,
            content={
                "code": "not_found",
                "message": "El frontend no está compilado en este entorno.",
                "requestId": getattr(request.state, "request_id", "unknown"),
            },
        )

    return app


app = create_app()
