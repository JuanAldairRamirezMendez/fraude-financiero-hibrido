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
    values = {
        "transaction_amount": 4_000,
        "previous_chargebacks": 3,
        "customer_risk_score": 0.8,
        "transaction_velocity_1h": 5,
        "transaction_velocity_24h": 14,
        "is_high_risk_merchant_category": 1,
        "is_international": 1,
        "account_age_days": 5,
    }
    assert count_signals(values) == 8


def test_count_signals_returns_zero_for_low_risk() -> None:
    values = {
        "transaction_amount": 10,
        "previous_chargebacks": 0,
        "customer_risk_score": 0.1,
        "transaction_velocity_1h": 0,
        "transaction_velocity_24h": 1,
        "is_high_risk_merchant_category": 0,
        "is_international": 0,
        "account_age_days": 900,
    }
    assert count_signals(values) == 0


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
