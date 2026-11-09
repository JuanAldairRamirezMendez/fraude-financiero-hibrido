from __future__ import annotations

from fastapi import Request

from app.core.errors import ServiceUnavailableError
from app.repositories.protocols import FraudRepository
from app.services.analyze_service import AnalyzeService
from app.services.inference_service import InferenceService
from app.services.metadata_service import MetadataService
from app.services.models_service import ModelsService
from app.services.snapshot_service import SnapshotService


def get_repository(request: Request) -> FraudRepository:
    repository = getattr(request.app.state, "repository", None)
    if repository is None:
        raise ServiceUnavailableError("La base de datos no está disponible.")
    return repository


def get_inference(request: Request) -> InferenceService:
    inference = getattr(request.app.state, "inference_service", None)
    if inference is None:
        raise ServiceUnavailableError("El modelo de inferencia no está cargado.")
    return inference


def get_metadata_service(request: Request) -> MetadataService:
    service = getattr(request.app.state, "metadata_service", None)
    if service is None:
        raise ServiceUnavailableError("Los metadatos del modelo no están disponibles.")
    return service


def get_snapshot_service(request: Request) -> SnapshotService:
    service = getattr(request.app.state, "snapshot_service", None)
    if service is None:
        raise ServiceUnavailableError("El snapshot del dashboard no está disponible.")
    return service


def get_models_service(request: Request) -> ModelsService:
    service = getattr(request.app.state, "models_service", None)
    if service is None:
        raise ServiceUnavailableError("La salud de los modelos no está disponible.")
    return service


def get_analyze_service(request: Request) -> AnalyzeService:
    service = getattr(request.app.state, "analyze_service", None)
    if service is None:
        raise ServiceUnavailableError("El servicio de análisis no está disponible.")
    return service
