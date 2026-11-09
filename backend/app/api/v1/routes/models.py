from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.dependencies import get_models_service
from app.schemas.api import ModelsResponse
from app.services.models_service import ModelsService

router = APIRouter(tags=["Models"])


@router.get(
    "/models",
    response_model=ModelsResponse,
    summary="Model health, drift and persisted alerts",
)
def models(service: ModelsService = Depends(get_models_service)) -> ModelsResponse:
    return service.get()
