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
