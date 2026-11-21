from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel

RiskLevel = Literal["low", "medium", "high"]
ShapDirection = Literal["increases", "decreases"]
TransactionStatus = Literal["Flagged", "Review", "Approved"]
AlertStatus = Literal["UNACKNOWLEDGED", "ACKNOWLEDGED", "RESOLVED"]
AlertType = Literal["Feature drift", "Data quality", "Prediction drift", "Performance"]
CaseStatus = Literal["new", "in_review", "escalated", "resolved"]
CaseVerdict = Literal["confirmed_fraud", "false_positive", "inconclusive"]
DecisionAction = Literal["approve", "review", "block"]
MerchantCategory = Literal[
    "entertainment",
    "food_dining",
    "gas_transport",
    "grocery_net",
    "grocery_pos",
    "health_fitness",
    "home",
    "kids_pets",
    "misc_net",
    "misc_pos",
    "personal_care",
    "shopping_net",
    "shopping_pos",
    "travel",
]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class AnalyzeRequest(ApiModel):
    """Una compra con tarjeta. El historial de la tarjeta lo aporta el servidor."""

    card_id: str = Field(pattern=r"^TARJ-\d{4}$", examples=["TARJ-0471"])
    transaction_time: datetime = Field(examples=["2020-10-15T22:23:52"])
    amount: float = Field(gt=0, le=50_000)
    category: MerchantCategory
    merchant_distance_km: float = Field(ge=0, le=1_000)
    # Desde decision_threshold la transacción se bloquea y pasa a la cola del analista; si no se
    # envía, se usa el umbral calibrado del modelo. block_threshold es opcional: si se envía uno
    # mayor, la franja intermedia queda retenida para revisión (desactivada por defecto).
    decision_threshold: float | None = Field(default=None, ge=0, le=1)
    block_threshold: float | None = Field(default=None, ge=0, le=1)

    @field_validator("transaction_time")
    @classmethod
    def naive_time(cls, value: datetime) -> datetime:
        """El dataset usa hora local sin zona; una hora con zona se lleva a UTC sin zona."""
        if value.tzinfo is not None:
            value = value.astimezone(UTC).replace(tzinfo=None)
        return value

    @model_validator(mode="after")
    def thresholds_in_order(self) -> AnalyzeRequest:
        if (
            self.block_threshold is not None
            and self.decision_threshold is not None
            and self.block_threshold < self.decision_threshold
        ):
            raise ValueError("blockThreshold debe ser mayor o igual que decisionThreshold.")
        return self


class ShapContribution(ApiModel):
    feature: str
    impact: float
    direction: ShapDirection


class TopDriver(ApiModel):
    feature: str
    impact_pct: float = Field(ge=0, le=100)


class CardContext(ApiModel):
    """Historial reciente de la tarjeta usado por el modelo, en términos legibles."""

    previous_purchases: int = Field(ge=0)
    seconds_since_previous: float | None = None
    average_amount: float | None = None
    purchases_1h: int = Field(ge=0, alias="purchases1h")
    amount_1h: float = Field(alias="amount1h")
    purchases_24h: int = Field(ge=0, alias="purchases24h")
    amount_24h: float = Field(alias="amount24h")
    customer_age: int
    customer_gender: str
    city: str
    state: str


class AnalyzeResponse(ApiModel):
    decision_id: str
    probability: float = Field(ge=0, le=1)
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    blocked: bool
    signals_triggered: int = Field(ge=0)
    latency_ms: int = Field(ge=0)
    shap: list[ShapContribution]
    top_driver: TopDriver
    model_version: str
    calibrated_threshold: float = Field(ge=0, le=1)
    idempotent_replay: bool = False
    decision: DecisionAction = "approve"
    review_threshold: float = Field(default=0.5, ge=0, le=1)
    block_threshold: float = Field(default=0.5, ge=0, le=1)
    case_id: str | None = None
    case_number: str | None = None
    card: CardContext | None = None


class FieldMetadata(ApiModel):
    name: str
    label: str
    group: str
    kind: Literal["integer", "number", "binary", "category", "datetime"]
    required: bool
    default: float | int | str
    options: list[str] = Field(default_factory=list)
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    observed_minimum: float | None = None
    observed_maximum: float | None = None


class DecisionThresholdMetadata(ApiModel):
    default: float
    minimum: float
    maximum: float
    step: float


class ModelInfo(ApiModel):
    model_id: str
    model_version: str
    algorithm: str
    calibration: str
    feature_count: int
    calibrated_threshold: float
    calibration_f1: float
    disclaimer: str
    metrics: dict[str, float]


class MetadataResponse(ApiModel):
    version: str
    generated_at: str
    model: ModelInfo
    fields: list[FieldMetadata]
    categories: dict[str, list[str]]
    defaults: dict[str, float | int | str]
    decision_threshold: DecisionThresholdMetadata
    feature_names: list[str]


class Kpi(ApiModel):
    id: str
    label: str
    value: str
    trend: str
    data_points: list[float]


class TransactionItem(ApiModel):
    id: str
    customer_id: str
    transaction_hour: int
    transaction_day_of_week: int
    amount: float
    country: str
    region: str
    merchant_category: str
    transaction_type: str
    device_type: str
    score: int
    status: TransactionStatus
    risk_label: int
    occurred_at: str | None = None


class TransactionPage(ApiModel):
    items: list[TransactionItem]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)


class OverviewResponse(ApiModel):
    kpis: list[Kpi]
    transactions: TransactionPage
    total_transactions: int
    updated_at: str
    window_label: str


class ModelHealth(ApiModel):
    status: Literal["stable", "degraded"]
    uptime_pct: float
    avg_latency_ms: float
    critical_issues: int
    psi: float
    drift_shift_pct: float
    psi_threshold: float
    window_label: str


class ModelAlert(ApiModel):
    id: str
    occurred_at: str
    model_id: str
    alert_type: str
    detail: str
    status: AlertStatus


class ModelsResponse(ApiModel):
    health: ModelHealth
    alerts: list[ModelAlert]
    updated_at: str


class HealthChecks(ApiModel):
    model_loaded: bool
    preprocessor_loaded: bool
    database_ok: bool
    snapshot_loaded: bool


class HealthResponse(ApiModel):
    status: Literal["ok", "degraded"]
    version: str
    environment: str
    uptime_seconds: float
    model_version: str | None
    checks: HealthChecks
    request_id: str


class ErrorDetail(ApiModel):
    field: str
    message: str
    type: str


class ErrorResponse(ApiModel):
    code: str
    message: str
    request_id: str
    details: list[ErrorDetail] | dict[str, str] | None = None


class ChatMessage(ApiModel):
    role: Literal["user", "model"]
    content: str = Field(min_length=1, max_length=4_000)


class ChatRequest(ApiModel):
    message: str = Field(min_length=1, max_length=4_000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=12)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()


class ChatResponse(ApiModel):
    message: str
    model: str


class CaseCreateRequest(ApiModel):
    decision_id: str = Field(min_length=1, max_length=40)
    assigned_to: str | None = Field(default=None, max_length=120)


class CaseUpdateRequest(ApiModel):
    status: CaseStatus | None = None
    assigned_to: str | None = Field(default=None, max_length=120)
    verdict: CaseVerdict | None = None
    feedback_comment: str | None = Field(default=None, max_length=4_000)
    note: str | None = Field(default=None, min_length=1, max_length=4_000)


class CaseNote(ApiModel):
    author: str
    content: str
    created_at: str


class CaseDecision(ApiModel):
    """Resumen de la decisión del modelo que originó el caso."""

    probability: float = Field(ge=0, le=1)
    score: int = Field(ge=0, le=100)
    level: RiskLevel
    decision: DecisionAction
    model_version: str
    transaction: dict[str, float | int | str]
    shap: list[ShapContribution]
    card: CardContext | None = None


class CaseResponse(ApiModel):
    id: str
    case_number: str
    decision_id: str
    status: CaseStatus
    assigned_to: str | None
    verdict: CaseVerdict | None
    feedback_comment: str | None
    created_at: str
    updated_at: str
    resolved_at: str | None
    notes: list[CaseNote]
    decision: CaseDecision | None = None


class CaseListResponse(ApiModel):
    items: list[CaseResponse]
    total: int
