from __future__ import annotations

from dataclasses import dataclass

from .transaction import Assessment


@dataclass(frozen=True, slots=True)
class Alert:
    id: str
    occurred_at: str
    model_id: str
    alert_type: str
    detail: str
    status: str


@dataclass(frozen=True, slots=True)
class DecisionAudit:
    request_id: str
    action: str
    assessment: Assessment
