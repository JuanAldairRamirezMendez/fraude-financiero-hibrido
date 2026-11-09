from __future__ import annotations

from typing import Any

from app.schemas.api import (
    DecisionThresholdMetadata,
    FieldMetadata,
    MetadataResponse,
    ModelInfo,
)
from app.services.artifacts import ArtifactStore


class MetadataService:
    def __init__(self, store: ArtifactStore) -> None:
        self._store = store

    def get(self) -> MetadataResponse:
        contract: dict[str, Any] = self._store.contract
        metadata: dict[str, Any] = self._store.metadata
        fields = [
            FieldMetadata(
                name=field["name"],
                label=field["label"],
                group=field["group"],
                kind=field["kind"],
                required=field.get("required", True),
                default=field["default"],
                options=list(field.get("options", [])),
                minimum=field.get("min"),
                maximum=field.get("max"),
                step=field.get("step"),
                observed_minimum=field.get("observedMin"),
                observed_maximum=field.get("observedMax"),
            )
            for field in contract["fields"]
        ]
        threshold = contract.get("decisionThreshold", {})
        return MetadataResponse(
            version=contract["version"],
            generated_at=contract["generatedAt"],
            model=ModelInfo(
                model_id=metadata["modelId"],
                model_version=metadata["modelVersion"],
                algorithm=metadata["algorithm"],
                calibration=metadata["calibration"],
                feature_count=metadata["featureCount"],
                calibrated_threshold=metadata["calibratedThreshold"],
                calibration_f1=metadata["calibrationF1"],
                disclaimer=metadata["calibrationNote"],
                metrics={key: float(value) for key, value in metadata["metrics"].items()},
            ),
            fields=fields,
            categories={
                name: list(values) for name, values in contract["categories"].items()
            },
            defaults=contract["defaults"],
            decision_threshold=DecisionThresholdMetadata(
                default=float(threshold.get("default", 0.5)),
                minimum=float(threshold.get("min", 0.0)),
                maximum=float(threshold.get("max", 1.0)),
                step=float(threshold.get("step", 0.01)),
            ),
            feature_names=self._store.feature_names,
        )
