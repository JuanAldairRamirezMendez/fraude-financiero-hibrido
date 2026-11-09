from __future__ import annotations

import time
import uuid
from typing import Any

import numpy as np
import pandas as pd
import shap

from app.core.errors import ServiceUnavailableError
from app.domain.transaction import (
    Assessment,
    ShapContribution,
    TransactionFeatures,
    count_signals,
    risk_level,
)
from app.schemas.api import AnalyzeRequest
from app.services.artifacts import ArtifactStore


def _extract_shap_vector(raw: Any, feature_count: int) -> np.ndarray:
    """Normalise SHAP output across shap/sklearn/xgboost versions."""

    values = np.asarray(raw, dtype=float)
    if values.ndim == 1:
        vector = values
    elif values.ndim == 2:
        if values.shape[0] == 1:
            vector = values[0]
        elif values.shape[1] == feature_count:
            vector = values[0]
        else:
            vector = values.reshape(-1)[:feature_count]
    elif values.ndim == 3:
        if values.shape[0] == 1 and values.shape[1] == feature_count:
            vector = values[0, :, -1]
        elif values.shape[1] == 1 and values.shape[2] == feature_count:
            vector = values[0, 0, :]
        elif values.shape[0] == feature_count:
            vector = values[:, 0, -1]
        elif values.shape[1] == feature_count:
            vector = values[0, :, -1]
        else:
            vector = values.reshape(-1)[:feature_count]
    else:
        vector = values.reshape(-1)[:feature_count]

    if vector.size != feature_count:
        raise ServiceUnavailableError(
            "La explicación SHAP devolvió una dimensión inesperada.",
            {"expected": feature_count, "received": int(vector.size)},
        )
    return vector


class InferenceService:
    def __init__(self, store: ArtifactStore) -> None:
        self._store = store
        base_estimator = store.model.calibrated_classifiers_[0].estimator
        self._explainer = shap.TreeExplainer(base_estimator)
        self._raw_features = list(store.contract["rawFeatures"])
        self._feature_names = store.feature_names

    @property
    def ready(self) -> bool:
        return True

    @property
    def model_version(self) -> str:
        return self._store.model_version

    def analyze(self, request: AnalyzeRequest) -> Assessment:
        started = time.perf_counter()
        values = request.to_feature_values()
        frame = pd.DataFrame([values], columns=self._raw_features)
        transformed = self._store.preprocessor.transform(frame)
        probability = float(self._store.model.predict_proba(transformed)[0, 1])

        shap_vector = _extract_shap_vector(
            self._explainer.shap_values(transformed), len(self._feature_names)
        )
        contributions = self._top_contributions(shap_vector)
        total_abs = float(np.sum(np.abs(shap_vector))) or 1.0
        top = contributions[0]
        latency_ms = max(1, round((time.perf_counter() - started) * 1000))
        score = int(np.clip(round(probability * 100), 0, 100))

        return Assessment(
            decision_id=f"DEC-{uuid.uuid4().hex[:12].upper()}",
            probability=round(probability, 6),
            score=score,
            level=risk_level(score),
            blocked=probability >= request.decision_threshold,
            signals_triggered=count_signals(values),
            latency_ms=latency_ms,
            shap=tuple(contributions),
            top_driver_feature=top.feature,
            top_driver_impact_pct=round(abs(top.impact) / total_abs * 100, 2),
            model_version=self.model_version,
        )

    def _top_contributions(self, vector: np.ndarray, limit: int = 8) -> list[ShapContribution]:
        pairs = sorted(
            zip(self._feature_names, vector, strict=True),
            key=lambda item: abs(float(item[1])),
            reverse=True,
        )[:limit]
        return [
            ShapContribution(
                feature=feature,
                impact=round(abs(float(value)), 6),
                direction="increases" if float(value) >= 0 else "decreases",
            )
            for feature, value in pairs
        ]

    def score_frame(self, frame: pd.DataFrame) -> np.ndarray:
        """Used by snapshot builders and deterministic smoke tests."""

        transformed = self._store.preprocessor.transform(frame[self._raw_features])
        return self._store.model.predict_proba(transformed)[:, 1]

    @staticmethod
    def from_features(features: TransactionFeatures) -> None:
        """Keeps the domain type discoverable without coupling it to FastAPI."""
        _ = features
