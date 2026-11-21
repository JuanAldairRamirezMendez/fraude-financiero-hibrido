from __future__ import annotations

import time
import uuid
from typing import Any

import numpy as np
import shap

from app.core.errors import NotFoundError, ServiceUnavailableError
from app.domain.transaction import (
    Assessment,
    CardActivity,
    ShapContribution,
    count_signals,
    risk_level,
)
from app.schemas.api import AnalyzeRequest
from app.services.artifacts import ArtifactStore


def _extract_shap_vector(raw: Any, feature_count: int) -> np.ndarray:
    """Normaliza la salida de SHAP entre versiones de shap/xgboost."""

    values = np.asarray(raw, dtype=float)
    if values.ndim == 3:  # (filas, variables, clases): se toma la clase "fraude"
        values = values[..., -1]
    vector = values[0] if values.ndim == 2 else values
    if vector.size != feature_count:
        raise ServiceUnavailableError(
            "La explicación SHAP devolvió una dimensión inesperada.",
            {"expected": feature_count, "received": int(vector.size)},
        )
    return vector


def _shap_owner(feature: str) -> str:
    """Las columnas One-Hot de categoría se explican como una sola variable."""
    return "categoria" if feature.startswith("cat_") else feature


class InferenceService:
    def __init__(self, store: ArtifactStore) -> None:
        self._store = store
        self._explainer = shap.TreeExplainer(store.model)
        self._feature_names = store.feature_names

    @property
    def ready(self) -> bool:
        return True

    @property
    def model_version(self) -> str:
        return self._store.model_version

    def analyze(self, request: AnalyzeRequest) -> Assessment:
        started = time.perf_counter()
        history = self._store.history
        if request.card_id not in history:
            raise NotFoundError("La tarjeta indicada no existe.", {"cardId": request.card_id})

        frame, context = history.features_for(
            card_id=request.card_id,
            when=request.transaction_time,
            amount=request.amount,
            category=request.category,
            distance_km=request.merchant_distance_km,
            category_medians=self._store.category_medians,
        )
        probability = float(self._store.model.predict_proba(frame)[0, 1])
        shap_vector = _extract_shap_vector(
            self._explainer.shap_values(frame), len(self._feature_names)
        )
        contributions = self._top_contributions(shap_vector)
        total_abs = float(np.sum(np.abs(shap_vector))) or 1.0
        top = contributions[0]
        threshold = request.decision_threshold if request.decision_threshold is not None else self._store.calibrated_threshold
        score = int(np.clip(round(probability * 100), 0, 100))

        # La compra queda en el historial: varias compras seguidas elevan la velocidad de uso.
        history.record(
            card_id=request.card_id,
            when=request.transaction_time,
            amount=request.amount,
            category=request.category,
        )
        latency_ms = max(1, round((time.perf_counter() - started) * 1000))

        return Assessment(
            decision_id=f"DEC-{uuid.uuid4().hex[:12].upper()}",
            probability=round(probability, 6),
            score=score,
            level=risk_level(score),
            blocked=probability >= threshold,
            signals_triggered=count_signals(frame.iloc[0].to_dict()),
            latency_ms=latency_ms,
            shap=tuple(contributions),
            top_driver_feature=top.feature,
            top_driver_impact_pct=round(abs(top.impact) / total_abs * 100, 2),
            model_version=self.model_version,
            card=CardActivity(
                previous_purchases=context.previous_purchases,
                seconds_since_previous=context.seconds_since_previous,
                average_amount=context.average_amount,
                purchases_1h=context.purchases_1h,
                amount_1h=context.amount_1h,
                purchases_24h=context.purchases_24h,
                amount_24h=context.amount_24h,
                customer_age=context.customer_age,
                customer_gender=context.customer_gender,
                city=context.city,
                state=context.state,
            ),
        )

    def _top_contributions(self, vector: np.ndarray, limit: int = 8) -> list[ShapContribution]:
        grouped: dict[str, float] = {}
        for feature, value in zip(self._feature_names, vector, strict=True):
            owner = _shap_owner(feature)
            grouped[owner] = grouped.get(owner, 0.0) + float(value)
        pairs = sorted(grouped.items(), key=lambda item: abs(item[1]), reverse=True)[:limit]
        return [
            ShapContribution(
                feature=feature,
                impact=round(abs(value), 6),
                direction="increases" if value >= 0 else "decreases",
            )
            for feature, value in pairs
        ]
