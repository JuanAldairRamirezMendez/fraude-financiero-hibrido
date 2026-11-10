from __future__ import annotations

from collections.abc import Callable

from fastapi import Cookie, Depends, Request

from app.core.errors import ServiceUnavailableError
from app.core.security import UserPrincipal, decode_access_token
from app.repositories.protocols import FraudRepository
from app.services.analyze_service import AnalyzeService
from app.services.auth_service import AuthService
from app.services.case_service import CaseService
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


def get_auth_service(request: Request) -> AuthService:
    service = getattr(request.app.state, "auth_service", None)
    if service is None:
        raise ServiceUnavailableError("El servicio de autenticación no está disponible.")
    return service


def get_case_service(request: Request) -> CaseService:
    service = getattr(request.app.state, "case_service", None)
    if service is None:
        raise ServiceUnavailableError("El servicio de casos no está disponible.")
    return service


def get_current_user(
    request: Request,
    access_token: str | None = Cookie(default=None),
) -> UserPrincipal | None:
    settings = request.app.state.settings
    if not settings.auth_enabled:
        return None
    if not access_token:
        from app.core.errors import AppError

        raise AppError("unauthorized", "Autenticación requerida.", 401)
    return decode_access_token(access_token, settings)


def require_roles(*roles: str) -> Callable[..., UserPrincipal | None]:
    def dependency(user: UserPrincipal | None = Depends(get_current_user)) -> UserPrincipal | None:
        if user is not None and user.role not in roles:
            from app.core.errors import AppError

            raise AppError("forbidden", "No tienes permisos para este recurso.", 403)
        return user

    return dependency
