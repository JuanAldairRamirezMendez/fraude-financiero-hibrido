from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Request

from app.schemas.api import HealthChecks, HealthResponse

router = APIRouter(tags=["Health"])


def _payload(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    started_at: datetime = request.app.state.started_at
    repository = getattr(request.app.state, "repository", None)
    inference = getattr(request.app.state, "inference_service", None)
    snapshot = getattr(request.app.state, "snapshot_service", None)
    checks = HealthChecks(
        model_loaded=inference is not None,
        preprocessor_loaded=getattr(request.app.state, "artifacts", None) is not None,
        database_ok=bool(repository and repository.ping()),
        snapshot_loaded=snapshot is not None,
    )
    ready = all(
        [
            checks.model_loaded,
            checks.preprocessor_loaded,
            checks.database_ok,
            checks.snapshot_loaded,
        ]
    )
    return HealthResponse(
        status="ok" if ready else "degraded",
        version=settings.app_version,
        environment=settings.environment,
        uptime_seconds=round((datetime.now(UTC) - started_at).total_seconds(), 2),
        model_version=getattr(request.app.state, "model_version", None),
        checks=checks,
        request_id=getattr(request.state, "request_id", "unknown"),
    )


@router.get("/health", response_model=HealthResponse, summary="Liveness and readiness")
def health(request: Request) -> HealthResponse:
    return _payload(request)


@router.get("/health/live", response_model=HealthResponse, summary="Liveness probe")
def liveness(request: Request) -> HealthResponse:
    return _payload(request)


@router.get("/health/ready", response_model=HealthResponse, summary="Readiness probe")
def readiness(request: Request) -> HealthResponse:
    return _payload(request)
