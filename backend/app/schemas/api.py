from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic.alias_generators import to_camel

RiskLevel = Literal["low", "medium", "high"]
ShapDirection = Literal["increases", "decreases"]
TransactionStatus = Literal["Flagged", "Review", "Approved"]
AlertStatus = Literal["UNACKNOWLEDGED", "ACKNOWLEDGED", "RESOLVED"]
AlertType = Literal["Feature drift", "Data quality", "Prediction drift", "Performance"]


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class AnalyzeRequest(ApiModel):
    transaction_hour: int = Field(ge=0, le=23)
    transaction_day_of_week: int = Field(ge=0, le=6)
    account_age_days: int = Field(ge=0, le=3650)
    previous_chargebacks: int = Field(ge=0, le=50)
    merchant_category: str = Field(min_length=1, max_length=64)
    transaction_country: str = Field(min_length=1, max_length=64)
    device_type: str = Field(min_length=1, max_length=64)
    transaction_type: str = Field(min_length=1, max_length=64)
    geo_location_region: str = Field(min_length=1, max_length=64)
    is_international: int = Field(ge=0, le=1)
    is_high_risk_merchant_category: int = Field(ge=0, le=1)
    is_weekend: int = Field(ge=0, le=1)
    customer_total_transactions_30d: int = Field(
        ge=0, le=500, alias="customerTotalTransactions30d"
    )
    customer_risk_score: float = Field(ge=0, le=1)
    transaction_amount: float = Field(gt=0, le=1_000_000)
    avg_transaction_amount_30d_customer: float = Field(
        ge=0, le=1_000_000, alias="avgTransactionAmount30dCustomer"
    )
    transaction_velocity_1h: int = Field(ge=0, le=100, alias="transactionVelocity1h")
    transaction_velocity_24h: int = Field(ge=0, le=500, alias="transactionVelocity24h")
    decision_threshold: float = Field(default=0.5, ge=0, le=1)

    @field_validator(
        "merchant_category",
        "transaction_country",
        "device_type",
        "transaction_type",
        "geo_location_region",
    )
    @classmethod
    def strip_categories(cls, value: str) -> str:
        return value.strip()

    def to_feature_values(self) -> dict[str, float | int | str]:
        return {
            "transaction_hour": self.transaction_hour,
            "transaction_day_of_week": self.transaction_day_of_week,
            "account_age_days": self.account_age_days,
            "previous_chargebacks": self.previous_chargebacks,
            "merchant_category": self.merchant_category,
            "transaction_country": self.transaction_country,
            "device_type": self.device_type,
            "transaction_type": self.transaction_type,
            "geo_location_region": self.geo_location_region,
            "is_international": self.is_international,
            "is_high_risk_merchant_category": self.is_high_risk_merchant_category,
            "is_weekend": self.is_weekend,
            "customer_total_transactions_30d": self.customer_total_transactions_30d,
            "customer_risk_score": self.customer_risk_score,
            "transaction_amount": self.transaction_amount,
            "avg_transaction_amount_30d_customer": self.avg_transaction_amount_30d_customer,
            "transaction_velocity_1h": self.transaction_velocity_1h,
            "transaction_velocity_24h": self.transaction_velocity_24h,
        }


class ShapContribution(ApiModel):
    feature: str
    impact: float
    direction: ShapDirection


class TopDriver(ApiModel):
    feature: str
    impact_pct: float = Field(ge=0, le=100)


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


class FieldMetadata(ApiModel):
    name: str
    label: str
    group: str
    kind: Literal["integer", "number", "binary", "category"]
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
