from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from app.core.settings import Settings
from app.ml.sparkov import FEATURE_NAMES, CardHistory, batch_features
from app.schemas.api import AnalyzeRequest
from app.services.artifacts import ArtifactStore
from app.services.inference_service import InferenceService

FRONTEND = Path(__file__).resolve().parents[3] / "frontend" / "src" / "features" / "analyzer"


def _store() -> ArtifactStore:
    settings = Settings(environment="test")
    return ArtifactStore.load(
        model_path=settings.model_path,
        card_history_path=settings.card_history_path,
        card_profiles_path=settings.card_profiles_path,
        contract_path=settings.feature_contract_path,
        metadata_path=settings.model_metadata_path,
    )


@pytest.fixture(scope="module")
def store() -> ArtifactStore:
    return _store()


def test_exported_contract_matches_model(store: ArtifactStore) -> None:
    assert store.feature_names == list(FEATURE_NAMES)
    assert store.model.n_features_in_ == len(FEATURE_NAMES)
    assert store.history.card_count == 999
    assert store.metadata["metrics"]["testF1"] > 0.9
    assert 0 < store.calibrated_threshold < 1


def test_demo_scenarios_reproduce_their_expected_score(store: ArtifactStore) -> None:
    """Los escenarios del Analizador deben dar el puntaje con el que se generaron."""
    service = InferenceService(store)
    for scenario in json.loads((FRONTEND / "scenarios.json").read_text(encoding="utf-8")):
        request = AnalyzeRequest(**scenario["values"])
        assessment = service.analyze(request)
        assert abs(assessment.score - scenario["expectedScore"]) <= 1, scenario["id"]
        assert assessment.card is not None
        assert len(assessment.shap) == 8


def test_online_features_match_training_features(store: ArtifactStore) -> None:
    """La API (una transacción) y el entrenamiento (vectorizado) calculan lo mismo."""
    history = pd.read_parquet(Settings(environment="test").card_history_path)
    card = "TARJ-0471"
    rows = history[history["card_id"] == card].head(400).copy()
    profile = store.history.profile(card)
    frame = pd.DataFrame(
        {
            "card_id": rows["card_id"].to_numpy(),
            "ts": pd.to_datetime(rows["ts"], unit="s").to_numpy(),
            "amt": rows["amt"].to_numpy(),
            "category": rows["category"].astype(str).to_numpy(),
            "gender": profile.gender,
            "dob": pd.Timestamp(profile.dob),
            "city_pop": profile.city_pop,
            "distancia_km": 42.0,
        }
    )
    expected = batch_features(frame, store.category_medians)
    fresh = CardHistory(frame.assign(ts=rows["ts"].to_numpy()), [profile])
    for i in [5, 120, 399]:
        row = frame.iloc[i]
        online, _ = fresh.features_for(
            card_id=card,
            when=row["ts"].to_pydatetime(),
            amount=float(row["amt"]),
            category=row["category"],
            distance_km=42.0,
            category_medians=store.category_medians,
        )
        assert online.iloc[0].to_numpy() == pytest.approx(expected.iloc[i].to_numpy(), rel=1e-9, abs=1e-9)


def test_artifacts_are_located_under_backend_artifacts() -> None:
    settings = Settings(environment="test")
    assert settings.card_history_path.parent == Path(settings.feature_contract_path).parent
