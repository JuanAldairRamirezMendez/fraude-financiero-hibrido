from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .logging import get_logger

logger = get_logger(__name__)


class AppError(Exception):
    """Domain/application error translated to a stable API envelope."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__("not_found", message, 404, details)


class ConflictError(AppError):
    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__("conflict", message, 409, details)


class ServiceUnavailableError(AppError):
    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__("service_unavailable", message, 503, details)


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def _envelope(
    request: Request,
    code: str,
    message: str,
    status_code: int,
    details: Any = None,
) -> JSONResponse:
    payload: dict[str, Any] = {
        "code": code,
        "message": message,
        "requestId": _request_id(request),
    }
    if details is not None:
        payload["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "application error",
            extra={
                "requestId": _request_id(request),
                "code": exc.code,
                "status": exc.status_code,
            },
        )
        return _envelope(request, exc.code, exc.message, exc.status_code, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        details = []
        for error in exc.errors():
            location = [str(part) for part in error.get("loc", ()) if part not in {"body", "query"}]
            details.append(
                {
                    "field": ".".join(location) or "request",
                    "message": str(error.get("msg", "Invalid value")),
                    "type": str(error.get("type", "validation_error")),
                }
            )
        return _envelope(
            request,
            "validation_error",
            "La solicitud contiene campos inválidos.",
            422,
            details,
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        code = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            405: "method_not_allowed",
            429: "rate_limited",
        }.get(exc.status_code, "http_error")
        return _envelope(request, code, str(exc.detail), exc.status_code)

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "unhandled exception",
            extra={"requestId": _request_id(request), "status": 500},
            exc_info=exc,
        )
        return _envelope(
            request,
            "internal_error",
            "Se produjo un error interno. Comparte el requestId con soporte.",
            500,
        )
