from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]
Direction = Literal["increases", "decreases"]

NUMERIC_FEATURES = (
    "transaction_hour",
    "transaction_day_of_week",
    "account_age_days",
    "previous_chargebacks",
    "is_international",
    "is_high_risk_merchant_category",
    "is_weekend",
    "customer_total_transactions_30d",
    "customer_risk_score",
    "transaction_amount",
    "avg_transaction_amount_30d_customer",
    "transaction_velocity_1h",
    "transaction_velocity_24h",
)

CATEGORICAL_FEATURES = (
    "merchant_category",
    "transaction_country",
    "device_type",
    "transaction_type",
    "geo_location_region",
)


@dataclass(frozen=True, slots=True)
class TransactionFeatures:
    """Validated raw transaction, independent of HTTP and Pydantic."""

    values: dict[str, float | int | str]

    @property
    def feature_columns(self) -> tuple[str, ...]:
        return NUMERIC_FEATURES + CATEGORICAL_FEATURES


@dataclass(frozen=True, slots=True)
class ShapContribution:
    feature: str
    impact: float
    direction: Direction


@dataclass(frozen=True, slots=True)
class Assessment:
    decision_id: str
    probability: float
    score: int
    level: RiskLevel
    blocked: bool
    signals_triggered: int
    latency_ms: int
    shap: tuple[ShapContribution, ...]
    top_driver_feature: str
    top_driver_impact_pct: float
    model_version: str


def risk_level(score: int) -> RiskLevel:
    if score >= 75:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def count_signals(values: dict[str, float | int | str]) -> int:
    """Count interpretable risk flags, not model internals."""

    flags = [
        float(values["transaction_amount"]) >= 3_000,
        float(values["previous_chargebacks"]) >= 2,
        float(values["customer_risk_score"]) >= 0.65,
        int(values["transaction_velocity_1h"]) >= 4,
        int(values["transaction_velocity_24h"]) >= 10,
        int(values["is_high_risk_merchant_category"]) == 1,
        int(values["is_international"]) == 1,
        int(values["account_age_days"]) < 30,
    ]
    return sum(1 for flag in flags if flag)
