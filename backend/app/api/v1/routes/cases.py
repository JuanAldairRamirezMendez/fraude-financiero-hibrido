from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request

from app.core.dependencies import get_case_service, get_current_user, require_roles
from app.schemas.api import CaseCreateRequest, CaseListResponse, CaseResponse, CaseUpdateRequest
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["Cases"])


def _actor(user=Depends(get_current_user)) -> str:  # type: ignore[no-untyped-def]
    return user.username if user is not None else "system"


@router.post("", response_model=CaseResponse, status_code=201, summary="Open a fraud case")
def create_case(
    payload: CaseCreateRequest,
    service: CaseService = Depends(get_case_service),
    _user=Depends(require_roles("admin", "analyst")),
    actor: str = Depends(_actor),
) -> CaseResponse:
    return service.create(payload, actor)


@router.get("", response_model=CaseListResponse, summary="List fraud cases")
def list_cases(
    status: str | None = Query(default=None),
    assigned_to: str | None = Query(default=None, alias="assignedTo"),
    service: CaseService = Depends(get_case_service),
    _user=Depends(require_roles("admin", "analyst")),
) -> CaseListResponse:
    items = service.list(status, assigned_to)
    return CaseListResponse(items=items, total=len(items))


@router.get("/{case_id}", response_model=CaseResponse, summary="Get a fraud case")
def get_case(
    case_id: str,
    service: CaseService = Depends(get_case_service),
    _user=Depends(require_roles("admin", "analyst")),
) -> CaseResponse:
    return service.get(case_id)


@router.patch("/{case_id}", response_model=CaseResponse, summary="Update a fraud case")
def update_case(
    case_id: str,
    payload: CaseUpdateRequest,
    request: Request,
    service: CaseService = Depends(get_case_service),
    _user=Depends(require_roles("admin", "analyst")),
    actor: str = Depends(_actor),
) -> CaseResponse:
    _ = request
    return service.update(case_id, payload, actor)