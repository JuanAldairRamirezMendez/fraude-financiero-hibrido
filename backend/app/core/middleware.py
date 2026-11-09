from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from .logging import get_logger

logger = get_logger(__name__)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Cross-Origin-Opener-Policy": "same-origin",
}


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - started) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = str(duration_ms)
        logger.info(
            "request completed",
            extra={
                "requestId": request_id,
                "route": request.url.path,
                "method": request.method,
                "status": response.status_code,
                "durationMs": duration_ms,
                "modelVersion": getattr(request.app.state, "model_version", None),
            },
        )
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response: Response = await call_next(request)
        for name, value in SECURITY_HEADERS.items():
            response.headers.setdefault(name, value)
        if request.app.state.settings.is_production:
            response.headers.setdefault(
                "Content-Security-Policy",
                "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                "script-src 'self'; connect-src 'self'; frame-ancestors 'none'",
            )
        return response


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Set conservative cache defaults for API responses."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        response: Response = await call_next(request)
        path = request.url.path
        if request.method == "GET" and path.endswith(("/metadata", "/models")):
            response.headers.setdefault("Cache-Control", "public, max-age=60, stale-while-revalidate=120")
        elif path.endswith("/overview"):
            response.headers.setdefault("Cache-Control", "public, max-age=30")
        else:
            response.headers.setdefault("Cache-Control", "no-store")
        return response
