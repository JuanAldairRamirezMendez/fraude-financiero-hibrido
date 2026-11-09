from __future__ import annotations

from app.core.settings import Settings
from app.services.snapshot_service import OverviewFilters, SnapshotService


def _snapshot() -> SnapshotService:
    settings = Settings(environment="test")
    return SnapshotService(settings.snapshot_path, settings.transactions_path)


def test_real_snapshot_contains_full_dataset_and_kpis() -> None:
    snapshot = _snapshot()
    result = snapshot.overview(OverviewFilters(page=1, page_size=25))

    assert result.total_transactions == 100_000
    assert result.transactions.total == 100_000
    assert result.transactions.total_pages == 4_000
    assert len(result.transactions.items) == 25
    assert {item.status for item in result.transactions.items} <= {"Approved", "Review", "Flagged"}
    assert len(result.kpis) == 4


def test_real_snapshot_filters_and_orders_server_side() -> None:
    snapshot = _snapshot()
    result = snapshot.overview(
        OverviewFilters(
            page=1,
            page_size=10,
            decision="Flagged",
            min_score=80,
            country="US",
            sort="amount",
            order="asc",
        )
    )

    assert result.transactions.total > 0
    assert len(result.transactions.items) <= 10
    assert all(item.status == "Flagged" for item in result.transactions.items)
    assert all(item.country == "US" for item in result.transactions.items)
    assert all(item.score >= 80 for item in result.transactions.items)
    assert [item.amount for item in result.transactions.items] == sorted(
        item.amount for item in result.transactions.items
    )


def test_real_snapshot_page_beyond_last_page_is_clamped() -> None:
    snapshot = _snapshot()
    result = snapshot.overview(OverviewFilters(page=99_999, page_size=100))

    assert result.transactions.page == result.transactions.total_pages
    assert len(result.transactions.items) == 100
