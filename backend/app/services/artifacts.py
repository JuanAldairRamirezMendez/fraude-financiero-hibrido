from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib

from app.core.errors import ServiceUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ArtifactStore:
    """Loads and owns the immutable model artifacts for the process lifetime."""

    def __init__(
        self,
        *,
        model: Any,
        preprocessor: Any,
        contract: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        self.model = model
        self.preprocessor = preprocessor
        self.contract = contract
        self.metadata = metadata

    @classmethod
    def load(
        cls,
        *,
        model_path: Path,
        preprocessor_path: Path,
        contract_path: Path,
        metadata_path: Path,
    ) -> "ArtifactStore":
        missing = [
            str(path)
            for path in [model_path, preprocessor_path, contract_path, metadata_path]
            if not path.exists()
        ]
        if missing:
            raise ServiceUnavailableError(
                "Los artefactos del modelo no están disponibles.",
                {"missing": missing},
            )
        try:
            model = joblib.load(model_path)
            preprocessor = joblib.load(preprocessor_path)
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as exc:  # pragma: no cover - only broken deployments
            raise ServiceUnavailableError(
                "No se pudieron cargar los artefactos del modelo.",
                {"error": str(exc)},
            ) from exc

        logger.info(
            "artifacts loaded",
            extra={
                "modelVersion": metadata.get("modelVersion"),
                "featureCount": len(contract.get("featureNames", [])),
            },
        )
        return cls(model=model, preprocessor=preprocessor, contract=contract, metadata=metadata)

    @property
    def feature_names(self) -> list[str]:
        return list(self.contract["featureNames"])

    @property
    def model_version(self) -> str:
        return str(self.metadata["modelVersion"])

    @property
    def calibrated_threshold(self) -> float:
        return float(self.metadata["calibratedThreshold"])
