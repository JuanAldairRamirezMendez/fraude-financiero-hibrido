from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import func, select

from app.db.database import Database
from app.db.models import (
    AlertRecord,
    AuditLogRecord,
    CaseNoteRecord,
    DecisionRecord,
    FraudCaseRecord,
    IdempotencyRecord,
    OutboxEventRecord,
)
from app.domain.assessment import Alert

from .protocols import IdempotencyEntry, PersistedCase, PersistedDecision, PersistedEvent


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
            self._add_decision(session, decision)
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
            self._add_decision(session, decision, idempotency_key=key)
            session.merge(
                IdempotencyRecord(
                    key=key,
                    request_hash=request_hash,
                    response_payload=response_payload,
                    expires_at=expires_at,
                )
            )
            session.flush()

    @staticmethod
    def _add_decision(session, decision: PersistedDecision, *, idempotency_key: str | None = None):  # type: ignore[no-untyped-def]
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
        details = {
            "score": decision.score,
            "level": decision.level,
            "blocked": decision.blocked,
            "modelVersion": decision.model_version,
        }
        if idempotency_key:
            details["idempotencyKey"] = idempotency_key
        session.add(
            AuditLogRecord(
                request_id=decision.request_id,
                action="analyze_transaction",
                entity_id=decision.decision_id,
                details=details,
            )
        )
        session.add(
            OutboxEventRecord(
                id=str(uuid4()),
                event_type="decision.created",
                aggregate_id=decision.decision_id,
                payload={
                    "decisionId": decision.decision_id,
                    "probability": decision.probability,
                    "score": decision.score,
                    "level": decision.level,
                    "blocked": decision.blocked,
                    "modelVersion": decision.model_version,
                    "transactionAmount": decision.transaction_amount,
                    "requestPayload": decision.request_payload,
                    "responsePayload": decision.response_payload,
                },
            )
        )

    def list_pending_events(self, limit: int = 100) -> list[PersistedEvent]:
        now = datetime.now(UTC)
        with self._database.session() as session:
            rows = session.scalars(
                select(OutboxEventRecord)
                .where(
                    OutboxEventRecord.status == "pending",
                    OutboxEventRecord.available_at <= now,
                )
                .order_by(OutboxEventRecord.created_at.asc())
                .limit(limit)
            ).all()
            return [
                PersistedEvent(
                    id=row.id,
                    event_type=row.event_type,
                    aggregate_id=row.aggregate_id,
                    payload=dict(row.payload),
                    status=row.status,
                    attempts=row.attempts,
                    available_at=row.available_at,
                    created_at=row.created_at,
                    published_at=row.published_at,
                )
                for row in rows
            ]

    def mark_event_published(self, event_id: str) -> None:
        with self._database.session() as session:
            event = session.get(OutboxEventRecord, event_id)
            if event is None:
                return
            event.status = "published"
            event.published_at = datetime.now(UTC)
            event.attempts += 1
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

    def get_decision(self, decision_id: str) -> PersistedDecision | None:
        with self._database.session() as session:
            record = session.scalar(
                select(DecisionRecord).where(DecisionRecord.decision_id == decision_id)
            )
            if record is None:
                return None
            return PersistedDecision(
                id=record.id,
                decision_id=record.decision_id,
                probability=record.probability,
                score=record.score,
                level=record.level,
                blocked=record.blocked,
                transaction_amount=record.transaction_amount,
                model_version=record.model_version,
                request_payload=dict(record.request_payload),
                response_payload=dict(record.response_payload),
                request_id="",
            )

    @staticmethod
    def _case_from_record(session, record: FraudCaseRecord) -> PersistedCase:  # type: ignore[no-untyped-def]
        notes = tuple(
            {
                "author": note.author,
                "content": note.content,
                "createdAt": note.created_at.isoformat(),
            }
            for note in session.scalars(
                select(CaseNoteRecord)
                .where(CaseNoteRecord.case_id == record.id)
                .order_by(CaseNoteRecord.created_at.asc())
            ).all()
        )
        return PersistedCase(
            id=record.id,
            case_number=record.case_number,
            decision_id=record.decision_id,
            status=record.status,
            assigned_to=record.assigned_to,
            verdict=record.verdict,
            feedback_comment=record.feedback_comment,
            created_at=record.created_at,
            updated_at=record.updated_at,
            resolved_at=record.resolved_at,
            notes=notes,
        )

    def create_case(self, case: PersistedCase, actor: str) -> None:
        with self._database.session() as session:
            session.add(
                FraudCaseRecord(
                    id=case.id,
                    case_number=case.case_number,
                    decision_id=case.decision_id,
                    status=case.status,
                    assigned_to=case.assigned_to,
                    verdict=case.verdict,
                    feedback_comment=case.feedback_comment,
                    created_at=case.created_at,
                    updated_at=case.updated_at,
                )
            )
            session.add(
                AuditLogRecord(
                    request_id="case-api",
                    action="create_fraud_case",
                    entity_id=case.id,
                    details={"actor": actor, "decisionId": case.decision_id},
                )
            )
            session.flush()

    def get_case(self, case_id: str) -> PersistedCase | None:
        with self._database.session() as session:
            record = session.get(FraudCaseRecord, case_id)
            return self._case_from_record(session, record) if record is not None else None

    def list_cases(
        self, *, status: str | None = None, assigned_to: str | None = None
    ) -> list[PersistedCase]:
        with self._database.session() as session:
            query = select(FraudCaseRecord).order_by(FraudCaseRecord.updated_at.desc())
            if status:
                query = query.where(FraudCaseRecord.status == status)
            if assigned_to:
                query = query.where(FraudCaseRecord.assigned_to == assigned_to)
            return [self._case_from_record(session, record) for record in session.scalars(query).all()]

    def update_case(self, case: PersistedCase, actor: str) -> None:
        with self._database.session() as session:
            record = session.get(FraudCaseRecord, case.id)
            if record is None:
                return
            record.status = case.status
            record.assigned_to = case.assigned_to
            record.verdict = case.verdict
            record.feedback_comment = case.feedback_comment
            record.updated_at = case.updated_at
            record.resolved_at = case.resolved_at
            session.add(
                AuditLogRecord(
                    request_id="case-api",
                    action="update_fraud_case",
                    entity_id=case.id,
                    details={
                        "actor": actor,
                        "status": case.status,
                        "assignedTo": case.assigned_to,
                        "verdict": case.verdict,
                    },
                )
            )
            session.flush()

    def add_case_note(self, case_id: str, author: str, content: str) -> None:
        with self._database.session() as session:
            session.add(
                CaseNoteRecord(id=str(uuid4()), case_id=case_id, author=author, content=content)
            )
            session.flush()
