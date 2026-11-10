from __future__ import annotations

import json
import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.dependencies import (  # noqa: E402
    get_analyze_service,
    get_metadata_service,
    get_models_service,
    get_snapshot_service,
)
from app.core.settings import Settings  # noqa: E402
from app.domain.assessment import Alert  # noqa: E402
from app.domain.transaction import Assessment, ShapContribution, risk_level  # noqa: E402
from app.main import create_app  # noqa: E402
from app.repositories.protocols import (  # noqa: E402
    IdempotencyEntry,
    PersistedCase,
    PersistedDecision,
    PersistedEvent,
)
from app.schemas.api import (  # noqa: E402
    AnalyzeRequest,
    DecisionThresholdMetadata,
    FieldMetadata,
    MetadataResponse,
    ModelInfo,
)
from app.services.analyze_service import AnalyzeService  # noqa: E402
from app.services.models_service import ModelsService  # noqa: E402
from app.services.snapshot_service import SnapshotService  # noqa: E402


def _decision_event(decision: PersistedDecision) -> PersistedEvent:
    now = datetime.now(UTC)
    return PersistedEvent(
        id=decision.id,
        event_type="decision.created",
        aggregate_id=decision.decision_id,
        payload={
            "decisionId": decision.decision_id,
            "score": decision.score,
            "level": decision.level,
            "blocked": decision.blocked,
        },
        status="pending",
        attempts=0,
        available_at=now,
        created_at=now,
        published_at=None,
    )


class FakeInferenceService:
    ready = True
    model_version = "fake-xgboost-1.0.0"

    def __init__(self) -> None:
        self.calls = 0

    def analyze(self, request: AnalyzeRequest) -> Assessment:
        self.calls += 1
        probability = 0.91 if request.transaction_amount >= 3_000 else 0.12
        score = round(probability * 100)
        return Assessment(
            decision_id=f"DEC-FAKE-{self.calls:04d}",
            probability=probability,
            score=score,
            level=risk_level(score),
            blocked=probability >= request.decision_threshold,
            signals_triggered=2,
            latency_ms=12,
            shap=(
                ShapContribution("transaction_amount", 1.25, "increases"),
                ShapContribution("customer_risk_score", 0.31, "decreases"),
            ),
            top_driver_feature="transaction_amount",
            top_driver_impact_pct=80.1,
            model_version=self.model_version,
        )


class FakeRepository:
    def __init__(self) -> None:
        self.decisions: list[PersistedDecision] = []
        self.idempotency: dict[str, IdempotencyEntry] = {}
        self.cases: dict[str, PersistedCase] = {}
        self.events: list[PersistedEvent] = []
        self.alerts = [
            Alert(
                id="ALT-TEST-1",
                occurred_at="2026-01-01T00:00:00+00:00",
                model_id="fake-xgboost-1.0.0",
                alert_type="Feature drift",
                detail="PSI within threshold",
                status="RESOLVED",
            )
        ]

    def ping(self) -> bool:
        return True

    def save_decision(self, decision: PersistedDecision) -> None:
        self.decisions.append(decision)
        self.events.append(_decision_event(decision))

    def save_decision_with_idempotency(
        self,
        decision: PersistedDecision,
        key: str,
        request_hash: str,
        response_payload: dict,
        expires_at: datetime,
    ) -> None:
        self.decisions.append(decision)
        self.events.append(_decision_event(decision))
        self.idempotency[key] = IdempotencyEntry(
            key=key,
            request_hash=request_hash,
            response_payload=response_payload,
            expires_at=expires_at,
        )

    def get_idempotency(self, key: str) -> IdempotencyEntry | None:
        return self.idempotency.get(key)

    def save_idempotency(
        self, key: str, request_hash: str, response_payload: dict, expires_at: datetime
    ) -> None:
        self.idempotency[key] = IdempotencyEntry(key, request_hash, response_payload, expires_at)

    def list_pending_events(self, limit: int = 100) -> list[PersistedEvent]:
        return [event for event in self.events if event.status == "pending"][:limit]

    def mark_event_published(self, event_id: str) -> None:
        self.events = [
            replace(
                event,
                status="published",
                published_at=datetime.now(UTC),
                attempts=event.attempts + 1,
            )
            if event.id == event_id
            else event
            for event in self.events
        ]

    def list_alerts(self, limit: int = 100) -> list[Alert]:
        return self.alerts[:limit]

    def seed_alerts(self, alerts: list[Alert]) -> int:
        return 0

    def average_latency_ms(self, window: int = 100) -> float:
        return 12.0

    def count_decisions(self) -> int:
        return len(self.decisions)

    def get_decision(self, decision_id: str) -> PersistedDecision | None:
        return next(
            (decision for decision in self.decisions if decision.decision_id == decision_id),
            None,
        )

    def create_case(self, case: PersistedCase, actor: str) -> None:
        _ = actor
        self.cases[case.id] = case

    def get_case(self, case_id: str) -> PersistedCase | None:
        return self.cases.get(case_id)

    def list_cases(
        self, *, status: str | None = None, assigned_to: str | None = None
    ) -> list[PersistedCase]:
        cases = list(self.cases.values())
        if status:
            cases = [case for case in cases if case.status == status]
        if assigned_to:
            cases = [case for case in cases if case.assigned_to == assigned_to]
        return cases

    def update_case(self, case: PersistedCase, actor: str) -> None:
        _ = actor
        self.cases[case.id] = case

    def add_case_note(self, case_id: str, author: str, content: str) -> None:
        case = self.cases[case_id]
        note = {
            "author": author,
            "content": content,
            "createdAt": datetime.now(UTC).isoformat(),
        }
        self.cases[case_id] = replace(case, notes=(*case.notes, note))


def _metadata() -> MetadataResponse:
    fields = [
        FieldMetadata(
            name="transaction_amount",
            label="Transaction amount",
            group="Transaction",
            kind="number",
            required=True,
            default=500.0,
            minimum=0.01,
            maximum=1_000_000,
            step=0.01,
        ),
        FieldMetadata(
            name="merchant_category",
            label="Merchant category",
            group="Merchant",
            kind="category",
            required=True,
            default="travel",
            options=["gambling", "travel"],
        ),
    ]
    return MetadataResponse(
        version="test",
        generated_at="2026-01-01T00:00:00+00:00",
        model=ModelInfo(
            model_id="fake-xgboost",
            model_version="fake-xgboost-1.0.0",
            algorithm="XGBoost",
            calibration="isotonic",
            feature_count=46,
            calibrated_threshold=0.25,
            calibration_f1=0.72,
            disclaimer="SHAP explains the base estimator.",
            metrics={"tier2F1": 0.73},
        ),
        fields=fields,
        categories={"merchant_category": ["gambling", "travel"]},
        defaults={"transaction_amount": 500.0, "merchant_category": "travel"},
        decision_threshold=DecisionThresholdMetadata(
            default=0.5, minimum=0.0, maximum=1.0, step=0.01
        ),
        feature_names=["transaction_amount", "merchant_category_travel"],
    )


@pytest.fixture
def snapshot_service(tmp_path: Path) -> SnapshotService:
    frame = pd.DataFrame(
        {
            "id": ["TXN-1", "TXN-2", "TXN-3", "TXN-4"],
            "customerId": ["CUST-1", "CUST-2", "CUST-3", "CUST-4"],
            "transactionHour": [1, 2, 3, 4],
            "transactionDayOfWeek": [0, 1, 2, 3],
            "amount": [120.0, 4_500.0, 900.0, 15_000.0],
            "country": ["US", "PE", "US", "DE"],
            "region": ["North America", "South America", "North America", "Europe"],
            "merchantCategory": ["travel", "gambling", "travel", "gambling"],
            "transactionType": ["online", "pos", "online", "online"],
            "deviceType": ["mobile", "desktop", "mobile", "mobile"],
            "score": [12, 88, 40, 96],
            "status": ["Approved", "Flagged", "Review", "Flagged"],
            "riskLabel": [0, 1, 0, 1],
            "probability": [0.12, 0.88, 0.4, 0.96],
        }
    )
    transactions_path = tmp_path / "transactions.parquet"
    frame.to_parquet(transactions_path, index=False)
    snapshot = {
        "generatedAt": "2026-01-01T00:00:00+00:00",
        "windowLabel": "Test snapshot",
        "totalTransactions": 4,
        "kpis": [
            {
                "id": "transactions",
                "label": "Total transactions",
                "value": "4",
                "trend": "Test",
                "dataPoints": [1, 2, 3, 4],
            }
        ],
        "drift": {
            "psi": 0.01,
            "psiThreshold": 0.2,
            "driftShiftPct": 0.5,
            "velocityPsi": 0.02,
        },
        "alerts": [
            {
                "id": "ALT-SNAPSHOT",
                "occurredAt": "2026-01-01T00:00:00+00:00",
                "modelId": "fake-xgboost",
                "alertType": "Feature drift",
                "detail": "PSI within threshold",
                "status": "RESOLVED",
            }
        ],
    }
    snapshot_path = tmp_path / "snapshot.json"
    snapshot_path.write_text(json.dumps(snapshot), encoding="utf-8")
    return SnapshotService(snapshot_path, transactions_path)


@pytest.fixture
def fake_repository() -> FakeRepository:
    return FakeRepository()


@pytest.fixture
def client(
    tmp_path: Path,
    fake_repository: FakeRepository,
    snapshot_service: SnapshotService,
) -> TestClient:
    settings = Settings(
        environment="test",
        fail_fast=False,
        enable_docs=True,
        expose_prometheus=False,
        seed_snapshot_alerts=False,
        database_url=f"sqlite:///{tmp_path / 'test.db'}",
        static_dir=tmp_path / "dist",
        model_path=tmp_path / "missing-model.pkl",
        preprocessor_path=tmp_path / "missing-preprocessor.joblib",
        feature_contract_path=tmp_path / "missing-contract.json",
        model_metadata_path=tmp_path / "missing-metadata.json",
        snapshot_path=tmp_path / "missing-snapshot.json",
        transactions_path=tmp_path / "missing-transactions.parquet",
    )
    app = create_app(settings)
    inference = FakeInferenceService()
    analyze_service = AnalyzeService(
        inference,  # type: ignore[arg-type]
        fake_repository,
        calibrated_threshold=0.25,
        idempotency_ttl_hours=24,
    )
    models_service = ModelsService(fake_repository, snapshot_service, datetime.now(UTC))

    app.dependency_overrides[get_analyze_service] = lambda: analyze_service
    app.dependency_overrides[get_snapshot_service] = lambda: snapshot_service
    class FakeMetadataService:
        def get(self) -> MetadataResponse:
            return _metadata()

    app.dependency_overrides[get_metadata_service] = lambda: FakeMetadataService()
    app.dependency_overrides[get_models_service] = lambda: models_service
    from app.core.dependencies import get_case_service
    from app.services.case_service import CaseService

    app.dependency_overrides[get_case_service] = lambda: CaseService(fake_repository)

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def valid_payload() -> dict[str, object]:
    return {
        "transactionHour": 14,
        "transactionDayOfWeek": 2,
        "accountAgeDays": 10,
        "previousChargebacks": 3,
        "merchantCategory": "gambling",
        "transactionCountry": "US",
        "deviceType": "mobile",
        "transactionType": "online",
        "geoLocationRegion": "North America",
        "isInternational": 1,
        "isHighRiskMerchantCategory": 1,
        "isWeekend": 0,
        "customerTotalTransactions30d": 20,
        "customerRiskScore": 0.8,
        "transactionAmount": 9000,
        "avgTransactionAmount30dCustomer": 500,
        "transactionVelocity1h": 6,
        "transactionVelocity24h": 15,
        "decisionThreshold": 0.5,
    }


@pytest.fixture
def idempotency_ttl() -> timedelta:
    return timedelta(hours=24)
