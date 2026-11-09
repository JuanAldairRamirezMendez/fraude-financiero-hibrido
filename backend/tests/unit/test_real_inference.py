from __future__ import annotations

import json
from pathlib import Path

from app.core.settings import Settings
from app.schemas.api import AnalyzeRequest
from app.services.artifacts import ArtifactStore
from app.services.inference_service import InferenceService


def _store() -> ArtifactStore:
    settings = Settings(environment="test")
    return ArtifactStore.load(
        model_path=settings.model_path,
        preprocessor_path=settings.preprocessor_path,
        contract_path=settings.feature_contract_path,
        metadata_path=settings.model_metadata_path,
    )


def test_exported_contract_matches_calibrated_model() -> None:
    store = _store()

    assert len(store.feature_names) == 46
    assert len(store.contract["rawFeatures"]) == 18
    assert store.metadata["dataset"]["randomState"] == 42
    assert 0 < store.calibrated_threshold < 1


def test_real_inference_returns_calibrated_score_and_shap() -> None:
    settings = Settings(environment="test")
    contract = json.loads(settings.feature_contract_path.read_text(encoding="utf-8"))
    request = AnalyzeRequest(**contract["defaults"])
    assessment = InferenceService(_store()).analyze(request)

    assert 0 <= assessment.probability <= 1
    assert 0 <= assessment.score <= 100
    assert len(assessment.shap) == 8
    assert assessment.model_version.startswith("xgboost-tier2-isotonic-")
    assert assessment.latency_ms >= 1


def test_artifacts_are_located_under_backend_artifacts() -> None:
    settings = Settings(environment="test")

    assert settings.preprocessor_path.parent == Path(settings.feature_contract_path).parent
