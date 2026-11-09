from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.core.errors import ServiceUnavailableError
from app.schemas.api import (
    Kpi,
    OverviewResponse,
    TransactionItem,
    TransactionPage,
    TransactionStatus,
)

SORT_COLUMNS = {
    "id": "id",
    "customerId": "customerId",
    "amount": "amount",
    "score": "score",
    "transactionHour": "transactionHour",
    "transactionDayOfWeek": "transactionDayOfWeek",
    "country": "country",
}


@dataclass(frozen=True, slots=True)
class OverviewFilters:
    page: int = 1
    page_size: int = 10
    q: str | None = None
    decision: TransactionStatus | None = None
    country: str | None = None
    transaction_type: str | None = None
    min_score: int | None = None
    max_score: int | None = None
    sort: str = "score"
    order: str = "desc"


class SnapshotService:
    def __init__(self, snapshot_path: Path, transactions_path: Path) -> None:
        if not snapshot_path.exists() or not transactions_path.exists():
            raise ServiceUnavailableError(
                "El snapshot del dashboard no está disponible.",
                {"snapshot": str(snapshot_path), "transactions": str(transactions_path)},
            )
        self._snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        self._frame = pd.read_parquet(transactions_path)
        self._required = {
            "id",
            "customerId",
            "transactionHour",
            "transactionDayOfWeek",
            "amount",
            "country",
            "region",
            "merchantCategory",
            "transactionType",
            "deviceType",
            "score",
            "status",
            "riskLabel",
        }
        missing = self._required - set(self._frame.columns)
        if missing:
            raise ServiceUnavailableError(
                "El snapshot de transacciones está incompleto.",
                {"missing": sorted(missing)},
            )

    @property
    def ready(self) -> bool:
        return True

    @property
    def generated_at(self) -> str:
        return str(self._snapshot["generatedAt"])

    @property
    def window_label(self) -> str:
        return str(self._snapshot["windowLabel"])

    @property
    def kpis(self) -> list[Kpi]:
        return [
            Kpi(
                id=item["id"],
                label=item["label"],
                value=item["value"],
                trend=item["trend"],
                data_points=[float(value) for value in item["dataPoints"]],
            )
            for item in self._snapshot["kpis"]
        ]

    @property
    def drift(self) -> dict[str, float]:
        return {key: float(value) for key, value in self._snapshot["drift"].items()}

    @property
    def alerts(self) -> list[dict[str, object]]:
        return list(self._snapshot.get("alerts", []))

    def overview(self, filters: OverviewFilters) -> OverviewResponse:
        frame = self._filtered(filters)
        total = int(len(frame))
        page_size = filters.page_size
        total_pages = math.ceil(total / page_size) if total else 0
        page = min(max(filters.page, 1), total_pages) if total_pages else 1
        start = (page - 1) * page_size
        rows = frame.iloc[start : start + page_size]

        return OverviewResponse(
            kpis=self.kpis,
            transactions=TransactionPage(
                items=[self._to_item(row) for row in rows.to_dict(orient="records")],
                page=page,
                page_size=page_size,
                total=total,
                total_pages=total_pages,
            ),
            total_transactions=int(self._snapshot["totalTransactions"]),
            updated_at=self.generated_at,
            window_label=str(self._snapshot["windowLabel"]),
        )

    def _filtered(self, filters: OverviewFilters) -> pd.DataFrame:
        frame = self._frame
        if filters.q:
            needle = filters.q.strip()
            if needle:
                mask = (
                    frame["id"].str.contains(needle, case=False, regex=False)
                    | frame["customerId"].str.contains(needle, case=False, regex=False)
                )
                frame = frame[mask]
        if filters.decision:
            frame = frame[frame["status"] == filters.decision]
        if filters.country:
            frame = frame[frame["country"] == filters.country]
        if filters.transaction_type:
            frame = frame[frame["transactionType"] == filters.transaction_type]
        if filters.min_score is not None:
            frame = frame[frame["score"] >= filters.min_score]
        if filters.max_score is not None:
            frame = frame[frame["score"] <= filters.max_score]

        sort_column = SORT_COLUMNS.get(filters.sort, "score")
        ascending = filters.order == "asc"
        return frame.sort_values(sort_column, ascending=ascending, kind="stable")

    @staticmethod
    def _to_item(row: dict[str, object]) -> TransactionItem:
        return TransactionItem(
            id=str(row["id"]),
            customer_id=str(row["customerId"]),
            transaction_hour=int(row["transactionHour"]),
            transaction_day_of_week=int(row["transactionDayOfWeek"]),
            amount=float(row["amount"]),
            country=str(row["country"]),
            region=str(row["region"]),
            merchant_category=str(row["merchantCategory"]),
            transaction_type=str(row["transactionType"]),
            device_type=str(row["deviceType"]),
            score=int(row["score"]),
            status=str(row["status"]),  # type: ignore[arg-type]
            risk_label=int(row["riskLabel"]),
        )
