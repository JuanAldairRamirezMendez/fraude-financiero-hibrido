from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_snapshot_service
from app.schemas.api import OverviewResponse, TransactionStatus
from app.services.snapshot_service import OverviewFilters, SnapshotService

router = APIRouter(tags=["Overview"])


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Dashboard KPIs and server-side transaction pagination",
)
def overview(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100, alias="pageSize"),
    q: str | None = Query(default=None, max_length=80),
    decision: TransactionStatus | None = Query(default=None),
    country: str | None = Query(default=None, max_length=64),
    transaction_type: str | None = Query(default=None, alias="transactionType", max_length=64),
    min_score: int | None = Query(default=None, alias="minScore", ge=0, le=100),
    max_score: int | None = Query(default=None, alias="maxScore", ge=0, le=100),
    sort: Literal[
        "id",
        "customerId",
        "amount",
        "score",
        "transactionHour",
        "transactionDayOfWeek",
        "country",
    ] = Query(default="score"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    service: SnapshotService = Depends(get_snapshot_service),
) -> OverviewResponse:
    filters = OverviewFilters(
        page=page,
        page_size=page_size,
        q=q,
        decision=decision,
        country=country,
        transaction_type=transaction_type,
        min_score=min_score,
        max_score=max_score,
        sort=sort,
        order=order,
    )
    return service.overview(filters)
