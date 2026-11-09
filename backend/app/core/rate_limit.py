from __future__ import annotations

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",", 1)[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_client_key, headers_enabled=True)


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=429,
        headers={"Retry-After": "60"},
        content={
            "code": "rate_limited",
            "message": "Demasiadas solicitudes. Inténtalo de nuevo en un minuto.",
            "requestId": request_id,
            "details": {"limit": str(exc.detail)},
        },
    )
