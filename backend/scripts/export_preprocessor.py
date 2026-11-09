#!/usr/bin/env python3
"""Reconstruct and export the inference artifacts without retraining.

The original pipeline fits a ``ColumnTransformer`` on the deterministic
80/20 stratified split (``random_state=42``). SMOTE is applied *after* the
transformer, so the transformer itself can be reconstructed from the raw
data alone. This script exports:

* ``preprocessor.joblib``: fitted numeric scaler + one-hot encoder.
* ``feature_contract.json``: raw fields, transformed feature names, ranges,
  categories and safe defaults for the API and the web form.
* ``model_metadata.json``: artifact hash, model details and the calibrated
  decision threshold.

Run from the repository root:

    venv/bin/python backend/scripts/export_preprocessor.py
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.metrics import precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "financial_fraud_risk_raw.parquet"
MODEL_PATH = PROJECT_ROOT / "models_saved" / "xgboost_tier2_isotonic.pkl"
ARTIFACTS_DIR = PROJECT_ROOT / "backend" / "artifacts"
RANDOM_STATE = 42
TEST_SIZE = 0.2
LABEL_COLUMN = "risk_label"
DROP_COLUMNS = ["transaction_id", "customer_id"]

NUMERIC_FIELDS = [
    "transaction_hour",
    "transaction_day_of_week",
    "account_age_days",
    "previous_chargebacks",
    "is_international",
    "is_high_risk_merchant_category",
    "is_weekend",
    "customer_total_transactions_30d",
    "customer_risk_score",
    "transaction_amount",
    "avg_transaction_amount_30d_customer",
    "transaction_velocity_1h",
    "transaction_velocity_24h",
]

CATEGORICAL_FIELDS = [
    "merchant_category",
    "transaction_country",
    "device_type",
    "transaction_type",
    "geo_location_region",
]

# Field metadata is deliberately explicit: the web form and the API
# documentation are generated from the same contract.
FIELD_SPECS: dict[str, dict[str, object]] = {
    "transaction_hour": {
        "label": "Transaction hour",
        "group": "Timing",
        "kind": "integer",
        "min": 0,
        "max": 23,
        "step": 1,
    },
    "transaction_day_of_week": {
        "label": "Day of week",
        "group": "Timing",
        "kind": "integer",
        "min": 0,
        "max": 6,
        "step": 1,
    },
    "account_age_days": {
        "label": "Account age (days)",
        "group": "Account",
        "kind": "integer",
        "min": 0,
        "max": 3650,
        "step": 1,
    },
    "previous_chargebacks": {
        "label": "Previous chargebacks",
        "group": "Account",
        "kind": "integer",
        "min": 0,
        "max": 50,
        "step": 1,
    },
    "is_international": {
        "label": "International transaction",
        "group": "Context",
        "kind": "binary",
        "min": 0,
        "max": 1,
        "step": 1,
        "options": ["0", "1"],
    },
    "is_high_risk_merchant_category": {
        "label": "High-risk merchant category",
        "group": "Merchant",
        "kind": "binary",
        "min": 0,
        "max": 1,
        "step": 1,
        "options": ["0", "1"],
    },
    "is_weekend": {
        "label": "Weekend transaction",
        "group": "Timing",
        "kind": "binary",
        "min": 0,
        "max": 1,
        "step": 1,
        "options": ["0", "1"],
    },
    "customer_total_transactions_30d": {
        "label": "Customer transactions (30d)",
        "group": "Customer",
        "kind": "integer",
        "min": 0,
        "max": 500,
        "step": 1,
    },
    "customer_risk_score": {
        "label": "Customer risk score",
        "group": "Customer",
        "kind": "number",
        "min": 0,
        "max": 1,
        "step": 0.01,
    },
    "transaction_amount": {
        "label": "Transaction amount",
        "group": "Transaction",
        "kind": "number",
        "min": 0.01,
        "max": 1_000_000,
        "step": 0.01,
    },
    "avg_transaction_amount_30d_customer": {
        "label": "Average amount (30d)",
        "group": "Customer",
        "kind": "number",
        "min": 0,
        "max": 1_000_000,
        "step": 0.01,
    },
    "transaction_velocity_1h": {
        "label": "Transaction velocity (1h)",
        "group": "Velocity",
        "kind": "integer",
        "min": 0,
        "max": 100,
        "step": 1,
    },
    "transaction_velocity_24h": {
        "label": "Transaction velocity (24h)",
        "group": "Velocity",
        "kind": "integer",
        "min": 0,
        "max": 500,
        "step": 1,
    },
    "merchant_category": {
        "label": "Merchant category",
        "group": "Merchant",
        "kind": "category",
    },
    "transaction_country": {
        "label": "Transaction country",
        "group": "Context",
        "kind": "category",
    },
    "device_type": {
        "label": "Device type",
        "group": "Context",
        "kind": "category",
    },
    "transaction_type": {
        "label": "Transaction type",
        "group": "Transaction",
        "kind": "category",
    },
    "geo_location_region": {
        "label": "Geographic region",
        "group": "Context",
        "kind": "category",
    },
}


def _json_number(value: object) -> int | float:
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (int, float)):
        return value
    raise TypeError(f"Unsupported numeric value: {type(value)!r}")


def _default_value(series: pd.Series) -> int | float | str:
    if series.dtype.kind in "ifu":
        value = series.median()
        if isinstance(value, (np.integer, np.floating)):
            return _json_number(value)
        return value
    mode = series.mode(dropna=True)
    return str(mode.iloc[0]) if not mode.empty else str(series.iloc[0])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(
            f"Dataset not found at {DATA_PATH}. Run the data pipeline first."
        )
    if not MODEL_PATH.exists():
        raise SystemExit(f"Model not found at {MODEL_PATH}.")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_parquet(DATA_PATH)
    missing = set(NUMERIC_FIELDS + CATEGORICAL_FIELDS + [LABEL_COLUMN]) - set(raw.columns)
    if missing:
        raise SystemExit(f"Dataset is missing required columns: {sorted(missing)}")

    features = raw.drop(columns=[c for c in DROP_COLUMNS if c in raw.columns])
    x = features.drop(columns=[LABEL_COLUMN])
    y = features[LABEL_COLUMN].astype(int)

    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y
    )

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUMERIC_FIELDS),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FIELDS,
            ),
        ]
    )
    preprocessor.fit(x_train)

    cat_encoder: OneHotEncoder = preprocessor.named_transformers_["cat"]
    cat_feature_names = cat_encoder.get_feature_names_out(CATEGORICAL_FIELDS).tolist()
    feature_names = NUMERIC_FIELDS + cat_feature_names
    if len(feature_names) != 46:
        raise SystemExit(f"Expected 46 transformed features, got {len(feature_names)}.")

    joblib.dump(preprocessor, ARTIFACTS_DIR / "preprocessor.joblib")

    model = joblib.load(MODEL_PATH)
    x_test_transformed = preprocessor.transform(x_test)
    probabilities = model.predict_proba(x_test_transformed)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_test, probabilities)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-12)
    best_index = int(np.argmax(f1_scores[:-1])) if len(thresholds) else 0
    calibrated_threshold = float(thresholds[best_index]) if len(thresholds) else 0.5

    fields: list[dict[str, object]] = []
    defaults: dict[str, object] = {}
    ranges: dict[str, dict[str, object]] = {}
    categories: dict[str, list[str]] = {}
    transformed_defaults = preprocessor.transform(
        pd.DataFrame([{name: _default_value(raw[name]) for name in x.columns}], columns=x.columns)
    )[0]

    for name in NUMERIC_FIELDS + CATEGORICAL_FIELDS:
        spec = dict(FIELD_SPECS[name])
        spec["name"] = name
        spec["required"] = True
        default = _default_value(raw[name])
        if spec["kind"] in {"integer", "binary"}:
            default = int(round(float(default)))
        spec["default"] = default
        if name in CATEGORICAL_FIELDS:
            options = sorted(str(value) for value in raw[name].dropna().unique())
            spec["options"] = options
            categories[name] = options
        else:
            numeric_values = raw[name].dropna()
            spec["observedMin"] = _json_number(numeric_values.min())
            spec["observedMax"] = _json_number(numeric_values.max())
            ranges[name] = {
                "min": spec["min"],
                "max": spec["max"],
                "step": spec["step"],
                "observedMin": spec["observedMin"],
                "observedMax": spec["observedMax"],
            }
        fields.append(spec)
        defaults[name] = spec["default"]

    contract = {
        "version": "1.0.0",
        "generatedAt": datetime.now(UTC).isoformat(),
        "labelColumn": LABEL_COLUMN,
        "droppedColumns": DROP_COLUMNS,
        "rawFeatures": NUMERIC_FIELDS + CATEGORICAL_FIELDS,
        "numericFeatures": NUMERIC_FIELDS,
        "categoricalFeatures": CATEGORICAL_FIELDS,
        "featureNames": feature_names,
        "categories": categories,
        "ranges": ranges,
        "defaults": defaults,
        "fields": fields,
        "decisionThreshold": {
            "default": 0.5,
            "min": 0.0,
            "max": 1.0,
            "step": 0.01,
        },
        "note": (
            "The transformed vector has "
            f"{len(feature_names)} dimensions: {len(NUMERIC_FIELDS)} scaled numeric "
            f"features plus {len(cat_feature_names)} one-hot columns."
        ),
    }

    metadata = {
        "version": "1.0.0",
        "generatedAt": datetime.now(UTC).isoformat(),
        "modelId": "xgboost-tier2-isotonic",
        "modelVersion": f"xgboost-tier2-isotonic-{_sha256(MODEL_PATH)[:12]}",
        "artifact": str(MODEL_PATH.relative_to(PROJECT_ROOT)),
        "artifactSha256": _sha256(MODEL_PATH),
        "algorithm": "XGBoost (Tier 2) + isotonic calibration",
        "calibration": "isotonic",
        "featureCount": len(feature_names),
        "calibratedThreshold": round(calibrated_threshold, 6),
        "calibrationF1": round(float(f1_scores[best_index]), 6),
        "calibrationNote": (
            "The threshold was selected on the deterministic 20% test split. "
            "SHAP values explain the base XGBoost estimator, not the calibrated "
            "isotonic probability."
        ),
        "metrics": {
            "tier2F1": 0.7342995119139305,
            "isotonicCalibrationF1": 0.726027392264027,
            "bootstrapMeanF1": 0.752084914708079,
            "bootstrapStdF1": 0.020291875381376508,
        },
        "dataset": {
            "path": str(DATA_PATH.relative_to(PROJECT_ROOT)),
            "rows": int(len(raw)),
            "fraudRate": round(float(y.mean()), 6),
            "randomState": RANDOM_STATE,
            "testSize": TEST_SIZE,
        },
        "defaults": {
            "transformedVectorSample": [round(float(v), 6) for v in transformed_defaults[:8]],
            "note": "First eight scaled/default feature values, useful for smoke checks.",
        },
    }

    (ARTIFACTS_DIR / "feature_contract.json").write_text(
        json.dumps(contract, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (ARTIFACTS_DIR / "model_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Preprocessor: {ARTIFACTS_DIR / 'preprocessor.joblib'}")
    print(f"Features: {len(feature_names)}")
    print(f"Calibrated threshold: {calibrated_threshold:.6f} (F1={f1_scores[best_index]:.6f})")
    print(f"Model version: {metadata['modelVersion']}")
    print(f"Defaults: {json.dumps(defaults, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
