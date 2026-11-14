#!/usr/bin/env python3
"""Build the offline evaluation data shown in the web "Evaluación" page.

Everything is computed on the *held-out* test split, reproduced exactly as in
``pipeline_completo.py`` (80/20, stratified, ``random_state=42``). Those 20,000
transactions were never used to train the model nor to fit SMOTE.

Outputs (consumed by the frontend as static JSON, no API call needed):

* ``frontend/src/features/evaluation/evaluation-data.json``: confusion matrix
  per threshold, ROC / precision-recall curves, global
  SHAP importance and a descriptive profile of the full dataset.
* ``frontend/src/features/analyzer/real-samples.json``: real test transactions
  (raw values + true label) for the "transacción real al azar" demo.

Requires the raw dataset at ``data/raw/financial_fraud_risk_raw.parquet``
(public: Hugging Face ``arun-gharami/lead-ai-fraud-detection-dataset-v2``).
Set ``MODEL_PATH`` to use another copy of the model (e.g. a Windows-compatible
re-export); it defaults to ``models_saved/xgboost_tier2_isotonic.pkl``.

Run from the repository root:

    python backend/scripts/build_evaluation.py
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.metrics import (
    average_precision_score,
    precision_recall_curve,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "financial_fraud_risk_raw.parquet"
MODEL_PATH = Path(
    os.environ.get("MODEL_PATH", PROJECT_ROOT / "models_saved" / "xgboost_tier2_isotonic.pkl")
)
ARTIFACTS_DIR = PROJECT_ROOT / "backend" / "artifacts"
PREPROCESSOR_PATH = ARTIFACTS_DIR / "preprocessor.joblib"
CONTRACT_PATH = ARTIFACTS_DIR / "feature_contract.json"
MODEL_METADATA_PATH = ARTIFACTS_DIR / "model_metadata.json"
FRONTEND_DIR = PROJECT_ROOT / "frontend" / "src" / "features"
EVALUATION_OUTPUT = FRONTEND_DIR / "evaluation" / "evaluation-data.json"
SAMPLES_OUTPUT = FRONTEND_DIR / "analyzer" / "real-samples.json"

DATASET_SOURCE = "arun-gharami/lead-ai-fraud-detection-dataset-v2"
RANDOM_STATE = 42
TEST_SIZE = 0.2
SHAP_SAMPLE_SIZE = 4000
SAMPLES_PER_CLASS = 100
CURVE_POINTS = 120

CAMEL_CASE = {
    "transaction_hour": "transactionHour",
    "transaction_day_of_week": "transactionDayOfWeek",
    "account_age_days": "accountAgeDays",
    "previous_chargebacks": "previousChargebacks",
    "merchant_category": "merchantCategory",
    "transaction_country": "transactionCountry",
    "device_type": "deviceType",
    "transaction_type": "transactionType",
    "geo_location_region": "geoLocationRegion",
    "is_international": "isInternational",
    "is_high_risk_merchant_category": "isHighRiskMerchantCategory",
    "is_weekend": "isWeekend",
    "customer_total_transactions_30d": "customerTotalTransactions30d",
    "customer_risk_score": "customerRiskScore",
    "transaction_amount": "transactionAmount",
    "avg_transaction_amount_30d_customer": "avgTransactionAmount30dCustomer",
    "transaction_velocity_1h": "transactionVelocity1h",
    "transaction_velocity_24h": "transactionVelocity24h",
}


def _round(value: float, digits: int = 4) -> float:
    return float(round(float(value), digits))


def _downsample(xs: np.ndarray, ys: np.ndarray, points: int) -> list[list[float]]:
    """Keep the curve shape with at most ``points`` vertices (always keeps the ends)."""
    if len(xs) <= points:
        idx = np.arange(len(xs))
    else:
        idx = np.unique(np.linspace(0, len(xs) - 1, points).round().astype(int))
    return [[_round(xs[i]), _round(ys[i])] for i in idx]


def confusion(y_true: np.ndarray, predicted: np.ndarray, amounts: np.ndarray) -> dict:
    tp_mask = predicted & (y_true == 1)
    fn_mask = ~predicted & (y_true == 1)
    return {
        "tp": int(tp_mask.sum()),
        "fp": int((predicted & (y_true == 0)).sum()),
        "fn": int(fn_mask.sum()),
        "tn": int((~predicted & (y_true == 0)).sum()),
        "caughtAmount": _round(amounts[tp_mask].sum(), 2),
        "missedAmount": _round(amounts[fn_mask].sum(), 2),
    }


def rate_by(frame: pd.DataFrame, column: str, label: str) -> list[dict]:
    grouped = frame.groupby(column, observed=True)[label].agg(["count", "sum"]).reset_index()
    grouped = grouped.sort_values(column)
    return [
        {
            "key": str(row[column]),
            "transactions": int(row["count"]),
            "frauds": int(row["sum"]),
            "fraudRate": _round(row["sum"] / row["count"], 5),
        }
        for _, row in grouped.iterrows()
    ]


def global_shap(model, preprocessor, frame: pd.DataFrame, raw_features: list[str], feature_names: list[str]) -> list[dict]:
    """Mean |SHAP| per raw feature (one-hot columns summed back into their source field)."""
    base_estimator = model.calibrated_classifiers_[0].estimator
    explainer = shap.TreeExplainer(base_estimator)
    values = explainer.shap_values(preprocessor.transform(frame[raw_features]))
    values = np.asarray(values[1] if isinstance(values, list) else values)
    if values.ndim == 3:
        values = values[..., -1]

    owner = []
    for name in feature_names:
        match = next(
            (raw for raw in raw_features if name == raw or name.startswith(f"{raw}_")), name
        )
        owner.append(match)

    per_row = pd.DataFrame(np.abs(values), columns=feature_names).T.groupby(owner).sum().T
    importance = per_row.mean().sort_values(ascending=False)
    total = float(importance.sum()) or 1.0
    return [
        {"feature": feature, "meanAbsShap": _round(value, 5), "share": _round(value / total, 4)}
        for feature, value in importance.items()
    ]


def main() -> None:
    for required in [DATA_PATH, MODEL_PATH, PREPROCESSOR_PATH, CONTRACT_PATH, MODEL_METADATA_PATH]:
        if not required.exists():
            raise SystemExit(f"Missing required file: {required}")

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    model = joblib.load(MODEL_PATH)
    raw_features: list[str] = contract["rawFeatures"]
    label = contract["labelColumn"]
    threshold = float(metadata["calibratedThreshold"])

    raw = pd.read_parquet(DATA_PATH)
    _, test = train_test_split(
        raw, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=raw[label]
    )
    y_true = test[label].to_numpy().astype(int)
    amounts = test["transaction_amount"].to_numpy().astype(float)
    probabilities = model.predict_proba(preprocessor.transform(test[raw_features]))[:, 1]

    # 1. Confusion matrix for every threshold between 0.00 and 1.00.
    thresholds = [
        {"threshold": _round(t, 2), **confusion(y_true, probabilities >= t, amounts)}
        for t in np.round(np.arange(0, 1.0001, 0.01), 2)
    ]
    calibrated = {"threshold": _round(threshold), **confusion(y_true, probabilities >= threshold, amounts)}

    # 2. ROC and precision-recall curves.
    fpr, tpr, _ = roc_curve(y_true, probabilities)
    precision, recall, _ = precision_recall_curve(y_true, probabilities)

    # 3. What the model learned overall (global SHAP on a reproducible sample).
    shap_sample = test.sample(n=min(SHAP_SAMPLE_SIZE, len(test)), random_state=RANDOM_STATE)
    importance = global_shap(model, preprocessor, shap_sample, raw_features, contract["featureNames"])

    # 4. Descriptive profile of the full dataset (descriptive, not a model metric).
    profile = {
        "merchantCategory": rate_by(raw, "merchant_category", label),
        "transactionHour": rate_by(raw, "transaction_hour", label),
        "transactionCountry": rate_by(raw, "transaction_country", label),
        "transactionType": rate_by(raw, "transaction_type", label),
    }

    evaluation = {
        "generatedAt": datetime.now(UTC).isoformat(),
        "modelVersion": metadata["modelVersion"],
        "dataset": {
            "source": DATASET_SOURCE,
            "rows": int(len(raw)),
            "fraudRate": _round(raw[label].mean(), 5),
            "split": f"80/20 estratificado, random_state={RANDOM_STATE}",
            "testRows": int(len(test)),
            "testFrauds": int(y_true.sum()),
            "avgFraudAmount": _round(amounts[y_true == 1].mean(), 2),
        },
        "calibratedThreshold": _round(threshold, 6),
        "calibrated": calibrated,
        "aucRoc": _round(roc_auc_score(y_true, probabilities)),
        "averagePrecision": _round(average_precision_score(y_true, probabilities)),
        "thresholds": thresholds,
        "roc": _downsample(fpr, tpr, CURVE_POINTS),
        "precisionRecall": _downsample(recall[::-1], precision[::-1], CURVE_POINTS),
        "globalImportance": importance,
        "shapSampleSize": int(len(shap_sample)),
        "profile": profile,
    }

    # 5. Real test transactions for the live demo (balanced so frauds appear often).
    frauds = test[test[label] == 1].sample(n=SAMPLES_PER_CLASS, random_state=RANDOM_STATE)
    legit = test[test[label] == 0].sample(n=SAMPLES_PER_CLASS, random_state=RANDOM_STATE)
    picked = pd.concat([frauds, legit]).sample(frac=1, random_state=RANDOM_STATE)
    samples = []
    for _, row in picked.iterrows():
        values = {}
        for column, key in CAMEL_CASE.items():
            value = row[column]
            values[key] = value.item() if hasattr(value, "item") else value
        samples.append(
            {"id": str(row["transaction_id"]), "isFraud": bool(row[label]), "values": values}
        )

    EVALUATION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    EVALUATION_OUTPUT.write_text(
        json.dumps(evaluation, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
    )
    SAMPLES_OUTPUT.write_text(
        json.dumps(
            {
                "source": DATASET_SOURCE,
                "note": f"{SAMPLES_PER_CLASS} fraudes y {SAMPLES_PER_CLASS} legítimas del conjunto de prueba.",
                "samples": samples,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"Test: {len(test)} filas, {int(y_true.sum())} fraudes · AUC {evaluation['aucRoc']}")
    print(f"Umbral {threshold:.4f}: {calibrated}")
    print("Top importancia:", [(i["feature"], i["share"]) for i in importance[:5]])
    print(f"Escrito {EVALUATION_OUTPUT.relative_to(PROJECT_ROOT)} y {SAMPLES_OUTPUT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
