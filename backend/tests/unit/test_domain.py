from __future__ import annotations

import numpy as np
import pytest

from app.core.errors import ServiceUnavailableError
from app.domain.transaction import count_signals, risk_level
from app.services.inference_service import _extract_shap_vector


@pytest.mark.parametrize(
    ("score", "expected"),
    [(0, "low"), (39, "low"), (40, "medium"), (74, "medium"), (75, "high"), (100, "high")],
)
def test_risk_level_boundaries(score: int, expected: str) -> None:
    assert risk_level(score) == expected


def test_count_signals_detects_multiple_flags() -> None:
    features = {
        "nocturna": 1,
        "monto_vs_promedio_tarjeta": 6.0,
        "monto_vs_categoria": 9.0,
        "compras_1h": 4,
        "compras_24h": 11,
        "seg_desde_anterior": 120,
        "monto_24h": 4_800,
    }
    assert count_signals(features) == 7


def test_count_signals_returns_zero_for_low_risk() -> None:
    features = {
        "nocturna": 0,
        "monto_vs_promedio_tarjeta": 0.9,
        "monto_vs_categoria": 1.1,
        "compras_1h": 1,
        "compras_24h": 3,
        "seg_desde_anterior": 20_000,
        "monto_24h": 180,
    }
    assert count_signals(features) == 0


def test_extract_shap_vector_handles_two_dimensions() -> None:
    vector = _extract_shap_vector(np.array([[0.1, -0.2, 0.3]]), 3)
    assert vector.tolist() == [0.1, -0.2, 0.3]


def test_extract_shap_vector_handles_class_axis() -> None:
    raw = np.array([[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]]])
    vector = _extract_shap_vector(raw, 3)
    assert vector.tolist() == [0.2, 0.4, 0.6]


def test_extract_shap_vector_rejects_wrong_size() -> None:
    with pytest.raises(ServiceUnavailableError):
        _extract_shap_vector(np.array([0.1, 0.2]), 3)


def test_decide_applies_three_level_policy() -> None:
    from app.domain.transaction import decide

    assert decide(0.10, 0.247, 0.75) == "approve"
    assert decide(0.247, 0.247, 0.75) == "review"
    assert decide(0.74, 0.247, 0.75) == "review"
    assert decide(0.75, 0.247, 0.75) == "block"
    # Con un único umbral (política por defecto) solo hay aprobar o bloquear.
    assert decide(0.246, 0.247, 0.247) == "approve"
    assert decide(0.247, 0.247, 0.247) == "block"


def test_case_summary_of_decision_saved_before_the_policy_change() -> None:
    """Las decisiones antiguas (p. ej. en la base de la nube) no guardaban la acción."""
    from app.repositories.protocols import PersistedDecision
    from app.services.case_service import _decision_summary

    old = PersistedDecision(
        id="1",
        decision_id="DEC-OLD",
        probability=0.55,
        score=55,
        level="medium",
        blocked=True,
        transaction_amount=900.0,
        model_version="v-old",
        request_payload={"transactionAmount": 900.0, "decisionThreshold": 0.5},
        response_payload={"level": "medium", "shap": []},
        request_id="req",
    )

    summary = _decision_summary(old)
    assert summary is not None
    assert summary.decision == "block"
    assert summary.level == "high"
    assert "decisionThreshold" not in summary.transaction
