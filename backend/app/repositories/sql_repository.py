from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import func, select

from app.db.database import Database
from app.db.models import AlertRecord, AuditLogRecord, DecisionRecord, IdempotencyRecord
from app.domain.assessment import Alert

from .protocols import IdempotencyEntry, PersistedDecision


class SqlFraudRepository:
    """SQLAlchemy implementation of the repository protocol.

    The service layer only sees :class:`FraudRepository`; swapping SQLite for
    PostgreSQL is therefore a configuration change plus the Alembic migration.
    """

    def __init__(self, database: Database) -> None:
        self._database = database

    def ping(self) -> bool:
        return self._database.ping()

    def save_decision(self, decision: PersistedDecision) -> None:
        with self._database.session() as session:
            session.add(
                DecisionRecord(
                    id=decision.id,
                    decision_id=decision.decision_id,
                    probability=decision.probability,
                    score=decision.score,
                    level=decision.level,
                    blocked=decision.blocked,
                    transaction_amount=decision.transaction_amount,
                    model_version=decision.model_version,
                    request_payload=decision.request_payload,
                    response_payload=decision.response_payload,
                )
            )
            session.add(
                AuditLogRecord(
                    request_id=decision.request_id,
                    action="analyze_transaction",
                    entity_id=decision.decision_id,
                    details={
                        "score": decision.score,
                        "level": decision.level,
                        "blocked": decision.blocked,
                        "modelVersion": decision.model_version,
                    },
                )
            )
            session.flush()

    def save_decision_with_idempotency(
        self,
        decision: PersistedDecision,
        key: str,
        request_hash: str,
        response_payload: dict,
        expires_at: datetime,
    ) -> None:
        with self._database.session() as session:
            session.add(
                DecisionRecord(
                    id=decision.id,
                    decision_id=decision.decision_id,
                    probability=decision.probability,
                    score=decision.score,
                    level=decision.level,
                    blocked=decision.blocked,
                    transaction_amount=decision.transaction_amount,
                    model_version=decision.model_version,
                    request_payload=decision.request_payload,
                    response_payload=decision.response_payload,
                )
            )
            session.add(
                AuditLogRecord(
                    request_id=decision.request_id,
                    action="analyze_transaction",
                    entity_id=decision.decision_id,
                    details={
                        "score": decision.score,
                        "level": decision.level,
                        "blocked": decision.blocked,
                        "modelVersion": decision.model_version,
                        "idempotencyKey": key,
                    },
                )
            )
            session.merge(
                IdempotencyRecord(
                    key=key,
                    request_hash=request_hash,
                    response_payload=response_payload,
                    expires_at=expires_at,
                )
            )
            session.flush()

    def get_idempotency(self, key: str) -> IdempotencyEntry | None:
        with self._database.session() as session:
            record = session.get(IdempotencyRecord, key)
            if record is None:
                return None
            expires_at = record.expires_at
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at <= datetime.now(UTC):
                session.delete(record)
                return None
            return IdempotencyEntry(
                key=record.key,
                request_hash=record.request_hash,
                response_payload=dict(record.response_payload),
                expires_at=expires_at,
            )

    def save_idempotency(
        self, key: str, request_hash: str, response_payload: dict, expires_at: datetime
    ) -> None:
        with self._database.session() as session:
            session.merge(
                IdempotencyRecord(
                    key=key,
                    request_hash=request_hash,
                    response_payload=response_payload,
                    expires_at=expires_at,
                )
            )
            session.flush()

    def list_alerts(self, limit: int = 100) -> list[Alert]:
        with self._database.session() as session:
            rows = session.scalars(
                select(AlertRecord).order_by(AlertRecord.occurred_at.desc()).limit(limit)
            ).all()
            return [
                Alert(
                    id=row.id,
                    occurred_at=row.occurred_at.isoformat(),
                    model_id=row.model_id,
                    alert_type=row.alert_type,
                    detail=row.detail,
                    status=row.status,
                )
                for row in rows
            ]

    def seed_alerts(self, alerts: list[Alert]) -> int:
        if not alerts:
            return 0
        created = 0
        with self._database.session() as session:
            existing = set(session.scalars(select(AlertRecord.id)).all())
            for alert in alerts:
                if alert.id in existing:
                    continue
                occurred_at = datetime.fromisoformat(alert.occurred_at)
                if occurred_at.tzinfo is None:
                    occurred_at = occurred_at.replace(tzinfo=UTC)
                session.add(
                    AlertRecord(
                        id=alert.id,
                        occurred_at=occurred_at,
                        model_id=alert.model_id,
                        alert_type=alert.alert_type,
                        detail=alert.detail,
                        status=alert.status,
                    )
                )
                created += 1
            session.flush()
        return created

    def average_latency_ms(self, window: int = 100) -> float:
        with self._database.session() as session:
            rows = session.execute(
                select(DecisionRecord.response_payload)
                .order_by(DecisionRecord.created_at.desc())
                .limit(window)
            ).scalars()
            latencies = [
                float(payload.get("latencyMs", 0))
                for payload in rows
                if isinstance(payload, dict)
            ]
        if not latencies:
            return 0.0
        return round(sum(latencies) / len(latencies), 2)

    def count_decisions(self) -> int:
        with self._database.session() as session:
            return int(session.scalar(select(func.count()).select_from(DecisionRecord)) or 0)
