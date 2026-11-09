from __future__ import annotations

from fastapi import APIRouter, Depends, Header, Request, Response

from app.core.dependencies import get_analyze_service, require_roles
from app.core.rate_limit import limiter
from app.schemas.api import AnalyzeRequest, AnalyzeResponse, ErrorResponse
from app.services.analyze_service import AnalyzeService

router = APIRouter(tags=["Analyze"])


@router.post(
    "/analyze",
    response_model=AnalyzeResponse,
    responses={
        409: {"model": ErrorResponse, "description": "Idempotency key reused"},
        422: {"model": ErrorResponse, "description": "Invalid transaction"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "Model unavailable"},
    },
    summary="Score a transaction and explain it with SHAP",
)
@limiter.limit("60/minute")
def analyze(
    request: Request,
    response: Response,
    payload: AnalyzeRequest,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
    service: AnalyzeService = Depends(get_analyze_service),
    _user=Depends(require_roles("admin", "analyst")),
) -> AnalyzeResponse:
    _ = response
    return service.analyze(
        payload,
        request_id=getattr(request.state, "request_id", "unknown"),
        idempotency_key=idempotency_key,
    )
