from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, Response

from app.core.dependencies import get_metadata_service
from app.schemas.api import MetadataResponse
from app.services.metadata_service import MetadataService

router = APIRouter(tags=["Metadata"])


@router.get(
    "/metadata",
    response_model=MetadataResponse,
    summary="Form contract, categories and model information",
)
def metadata(
    response: Response,
    service: MetadataService = Depends(get_metadata_service),
) -> MetadataResponse:
    result = service.get()
    etag = hashlib.sha256(result.generated_at.encode("utf-8")).hexdigest()[:24]
    response.headers["ETag"] = f'"{etag}"'
    return result
