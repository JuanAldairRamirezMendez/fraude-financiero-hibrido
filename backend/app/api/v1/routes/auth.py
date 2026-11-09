from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, Header, Request, Response

from app.core.dependencies import get_auth_service, get_current_user
from app.core.errors import AppError
from app.core.security import UserPrincipal, create_access_token, csrf_token
from app.schemas.auth import AuthResponse, AuthStatusResponse, AuthUser, LoginRequest
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


def _set_cookies(response: Response, request: Request, access_token: str, refresh_token: str) -> None:
    settings = request.app.state.settings
    common = {
        "secure": settings.auth_cookie_secure,
        "httponly": True,
        "samesite": settings.auth_cookie_samesite,
        "domain": settings.auth_cookie_domain,
        "path": "/",
    }
    response.set_cookie("access_token", access_token, max_age=settings.access_token_minutes * 60, **common)
    response.set_cookie("refresh_token", refresh_token, max_age=settings.refresh_token_days * 86400, **common)
    response.set_cookie(
        "csrf_token",
        csrf_token(),
        max_age=settings.refresh_token_days * 86400,
        secure=settings.auth_cookie_secure,
        httponly=False,
        samesite=settings.auth_cookie_samesite,
        domain=settings.auth_cookie_domain,
        path="/",
    )


def _clear_cookies(response: Response) -> None:
    for name in ("access_token", "refresh_token", "csrf_token"):
        response.delete_cookie(name, path="/")


def _check_csrf(csrf_cookie: str | None, csrf_header: str | None) -> None:
    if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
        raise AppError("forbidden", "Validación CSRF requerida.", 403)


@router.post("/login", response_model=AuthResponse, summary="Authenticate a user")
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    user = service.login(payload.username, payload.password)
    refresh_token, _ = service.issue_refresh(user)
    settings = request.app.state.settings
    _set_cookies(response, request, create_access_token(user, settings), refresh_token)
    return AuthResponse(
        user=AuthUser(id=user.id, username=user.username, role=user.role),
        expires_in=settings.access_token_minutes * 60,
    )


@router.post("/refresh", response_model=AuthResponse, summary="Rotate the refresh session")
def refresh(
    response: Response,
    request: Request,
    refresh_token: str | None = Cookie(default=None),
    csrf_cookie: str | None = Cookie(default=None, alias="csrf_token"),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    _check_csrf(csrf_cookie, csrf_header)
    if not refresh_token:
        raise AppError("unauthorized", "Sesión inválida o expirada.", 401)
    user, replacement, _ = service.rotate_refresh(refresh_token)
    settings = request.app.state.settings
    _set_cookies(response, request, create_access_token(user, settings), replacement)
    return AuthResponse(
        user=AuthUser(id=user.id, username=user.username, role=user.role),
        expires_in=settings.access_token_minutes * 60,
    )


@router.post("/logout", status_code=204, summary="Revoke the refresh session")
def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None),
    csrf_cookie: str | None = Cookie(default=None, alias="csrf_token"),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
    service: AuthService = Depends(get_auth_service),
) -> None:
    _check_csrf(csrf_cookie, csrf_header)
    if refresh_token:
        service.revoke_refresh(refresh_token)
    _clear_cookies(response)


@router.get("/me", response_model=AuthStatusResponse, summary="Get the current user")
def me(user: UserPrincipal | None = Depends(get_current_user)) -> AuthStatusResponse:
    if user is None:
        return AuthStatusResponse(authenticated=False)
    return AuthStatusResponse(
        authenticated=True,
        user=AuthUser(id=user.id, username=user.username, role=user.role),
    )
