from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import xgboost as xgb

from app.core.errors import ServiceUnavailableError
from app.core.logging import get_logger
from app.ml.sparkov import CardHistory, CardProfile

logger = get_logger(__name__)


class ArtifactStore:
    """Loads and owns the immutable model artifacts for the process lifetime."""

    def __init__(
        self,
        *,
        model: xgb.XGBClassifier,
        history: CardHistory,
        contract: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        self.model = model
        self.history = history
        self.contract = contract
        self.metadata = metadata

    @classmethod
    def load(
        cls,
        *,
        model_path: Path,
        card_history_path: Path,
        card_profiles_path: Path,
        contract_path: Path,
        metadata_path: Path,
    ) -> ArtifactStore:
        paths = [model_path, card_history_path, card_profiles_path, contract_path, metadata_path]
        missing = [str(path) for path in paths if not path.exists()]
        if missing:
            raise ServiceUnavailableError(
                "Los artefactos del modelo no están disponibles.",
                {"missing": missing},
            )
        try:
            # Formato nativo de XGBoost: portable entre sistemas operativos (sin pickle).
            model = xgb.XGBClassifier()
            model.load_model(model_path)
            transactions = pd.read_parquet(card_history_path)
            transactions["category"] = transactions["category"].astype(str)
            profiles = [
                CardProfile(
                    card_id=item["cardId"],
                    gender=item["gender"],
                    dob=datetime.fromisoformat(item["dob"]),
                    city=item["city"],
                    state=item["state"],
                    city_pop=int(item["cityPop"]),
                )
                for item in json.loads(card_profiles_path.read_text(encoding="utf-8"))
            ]
            history = CardHistory(transactions, profiles)
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
                "cards": history.card_count,
                "historyRows": len(transactions),
            },
        )
        return cls(model=model, history=history, contract=contract, metadata=metadata)

    @property
    def feature_names(self) -> list[str]:
        return list(self.contract["featureNames"])

    @property
    def category_medians(self) -> dict[str, float]:
        return {key: float(value) for key, value in self.contract["categoryMedians"].items()}

    @property
    def model_version(self) -> str:
        return str(self.metadata["modelVersion"])

    @property
    def calibrated_threshold(self) -> float:
        return float(self.metadata["calibratedThreshold"])
