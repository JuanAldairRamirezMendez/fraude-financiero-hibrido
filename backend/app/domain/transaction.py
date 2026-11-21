from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]
Direction = Literal["increases", "decreases"]
DecisionAction = Literal["approve", "review", "block"]

# El nivel mostrado siempre coincide con la acción tomada.
LEVEL_BY_ACTION: dict[DecisionAction, RiskLevel] = {
    "approve": "low",
    "review": "medium",
    "block": "high",
}


@dataclass(frozen=True, slots=True)
class ShapContribution:
    feature: str
    impact: float
    direction: Direction


@dataclass(frozen=True, slots=True)
class CardActivity:
    """Historial reciente de la tarjeta, en términos legibles."""

    previous_purchases: int
    seconds_since_previous: float | None
    average_amount: float | None
    purchases_1h: int
    amount_1h: float
    purchases_24h: int
    amount_24h: float
    customer_age: int
    customer_gender: str
    city: str
    state: str


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
    card: CardActivity | None = None


def decide(probability: float, review_threshold: float, block_threshold: float) -> DecisionAction:
    """Aprobar, retener para revisión humana o bloquear de inmediato."""
    if probability >= block_threshold:
        return "block"
    if probability >= review_threshold:
        return "review"
    return "approve"


def risk_level(score: int) -> RiskLevel:
    if score >= 75:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def count_signals(features: dict[str, float]) -> int:
    """Señales de riesgo interpretables, calculadas sobre las variables del modelo."""

    flags = [
        features["nocturna"] >= 1,
        features["monto_vs_promedio_tarjeta"] >= 3,
        features["monto_vs_categoria"] >= 5,
        features["compras_1h"] >= 3,
        features["compras_24h"] >= 8,
        features["seg_desde_anterior"] < 600,
        features["monto_24h"] >= 1_500,
    ]
    return sum(1 for flag in flags if flag)
