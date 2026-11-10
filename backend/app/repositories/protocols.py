from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from app.domain.assessment import Alert


@dataclass(frozen=True, slots=True)
class PersistedDecision:
    id: str
    decision_id: str
    probability: float
    score: int
    level: str
    blocked: bool
    transaction_amount: float
    model_version: str
    request_payload: dict
    response_payload: dict
    request_id: str


@dataclass(frozen=True, slots=True)
class IdempotencyEntry:
    key: str
    request_hash: str
    response_payload: dict
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class PersistedCase:
    id: str
    case_number: str
    decision_id: str
    status: str
    assigned_to: str | None
    verdict: str | None
    feedback_comment: str | None
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    notes: tuple[dict[str, str], ...]


class FraudRepository(Protocol):
    def ping(self) -> bool: ...

    def save_decision(self, decision: PersistedDecision) -> None: ...

    def save_decision_with_idempotency(
        self,
        decision: PersistedDecision,
        key: str,
        request_hash: str,
        response_payload: dict,
        expires_at: datetime,
    ) -> None: ...

    def get_idempotency(self, key: str) -> IdempotencyEntry | None: ...

    def save_idempotency(
        self, key: str, request_hash: str, response_payload: dict, expires_at: datetime
    ) -> None: ...

    def list_alerts(self, limit: int = 100) -> list[Alert]: ...

    def seed_alerts(self, alerts: list[Alert]) -> int: ...

    def average_latency_ms(self, window: int = 100) -> float: ...

    def get_decision(self, decision_id: str) -> PersistedDecision | None: ...

    def create_case(self, case: PersistedCase, actor: str) -> None: ...

    def get_case(self, case_id: str) -> PersistedCase | None: ...

    def list_cases(
        self, *, status: str | None = None, assigned_to: str | None = None
    ) -> list[PersistedCase]: ...

    def update_case(self, case: PersistedCase, actor: str) -> None: ...

    def add_case_note(self, case_id: str, author: str, content: str) -> None: ...
