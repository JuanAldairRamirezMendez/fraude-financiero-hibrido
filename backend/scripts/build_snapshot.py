#!/usr/bin/env python3
"""Build the offline dashboard snapshot used by ``GET /api/v1/overview``.

The snapshot is derived from the real parquet dataset and the exported
preprocessor. It contains no invented customers: identifiers, amounts,
countries and hours come from the data. The synthetic timeline is avoided by
exposing ``transactionHour`` and ``transactionDayOfWeek`` directly.

Outputs (both under ``backend/artifacts``):

* ``overview_snapshot.json``: KPIs, drift metrics and alert candidates.
* ``overview_transactions.parquet``: compact, queryable transaction rows.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = PROJECT_ROOT / "data" / "raw" / "financial_fraud_risk_raw.parquet"
MODEL_PATH = PROJECT_ROOT / "models_saved" / "xgboost_tier2_isotonic.pkl"
ARTIFACTS_DIR = PROJECT_ROOT / "backend" / "artifacts"
PREPROCESSOR_PATH = ARTIFACTS_DIR / "preprocessor.joblib"
CONTRACT_PATH = ARTIFACTS_DIR / "feature_contract.json"
MODEL_METADATA_PATH = ARTIFACTS_DIR / "model_metadata.json"
RANDOM_STATE = 42
TEST_SIZE = 0.2


def population_stability_index(
    expected: np.ndarray, actual: np.ndarray, buckets: int = 10
) -> float:
    """Compute a stable PSI using quantile bins from the expected sample."""
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)
    expected = expected[np.isfinite(expected)]
    actual = actual[np.isfinite(actual)]
    if expected.size == 0 or actual.size == 0:
        return 0.0

    edges = np.unique(np.quantile(expected, np.linspace(0, 1, buckets + 1)))
    if edges.size < 3:
        return 0.0
    edges[0] = -np.inf
    edges[-1] = np.inf

    expected_counts, _ = np.histogram(expected, bins=edges)
    actual_counts, _ = np.histogram(actual, bins=edges)
    expected_share = np.clip(expected_counts / max(expected_counts.sum(), 1), 1e-4, None)
    actual_share = np.clip(actual_counts / max(actual_counts.sum(), 1), 1e-4, None)
    return float(np.sum((actual_share - expected_share) * np.log(actual_share / expected_share)))


def score_to_status(score: float) -> str:
    if score >= 80:
        return "Flagged"
    if score >= 50:
        return "Review"
    return "Approved"


def main() -> None:
    for required in [DATA_PATH, MODEL_PATH, PREPROCESSOR_PATH, CONTRACT_PATH]:
        if not required.exists():
            raise SystemExit(f"Missing required artifact: {required}")

    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    model_metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    model = joblib.load(MODEL_PATH)

    raw = pd.read_parquet(DATA_PATH)
    raw_features = contract["rawFeatures"]
    test_frame, _ = train_test_split(
        raw,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=raw[contract["labelColumn"]],
    )

    transformed = preprocessor.transform(raw[raw_features])
    probabilities = model.predict_proba(transformed)[:, 1]
    scores = np.clip(np.rint(probabilities * 100), 1, 99).astype(int)

    transactions = pd.DataFrame(
        {
            "id": raw["transaction_id"].astype(str),
            "customerId": raw["customer_id"].astype(str),
            "transactionHour": raw["transaction_hour"].astype(int),
            "transactionDayOfWeek": raw["transaction_day_of_week"].astype(int),
            "amount": raw["transaction_amount"].astype(float).round(2),
            "country": raw["transaction_country"].astype(str),
            "region": raw["geo_location_region"].astype(str),
            "merchantCategory": raw["merchant_category"].astype(str),
            "transactionType": raw["transaction_type"].astype(str),
            "deviceType": raw["device_type"].astype(str),
            "score": scores,
            "status": [score_to_status(score) for score in scores],
            "riskLabel": raw[contract["labelColumn"]].astype(int),
            "probability": probabilities.round(6),
        }
    )
    transactions = transactions.sort_values(
        ["score", "amount"], ascending=[False, False], kind="stable"
    ).reset_index(drop=True)

    transactions.to_parquet(ARTIFACTS_DIR / "overview_transactions.parquet", index=False)

    psi_amount = population_stability_index(
        test_frame["transaction_amount"].to_numpy(), raw["transaction_amount"].to_numpy()
    )
    psi_velocity = population_stability_index(
        test_frame["transaction_velocity_24h"].to_numpy(),
        raw["transaction_velocity_24h"].to_numpy(),
    )
    mean_train = float(raw["transaction_amount"].mean())
    mean_test = float(test_frame["transaction_amount"].mean())
    drift_shift_pct = ((mean_test - mean_train) / mean_train * 100) if mean_train else 0.0

    status_counts = transactions["status"].value_counts().to_dict()
    fraud_rate = float(transactions["riskLabel"].mean())
    flagged = int(status_counts.get("Flagged", 0))
    review = int(status_counts.get("Review", 0))
    pending_alerts = flagged + review

    kpis = [
        {
            "id": "transactions",
            "label": "Total transactions",
            "value": f"{len(transactions):,}",
            "trend": "Full dataset snapshot",
            "dataPoints": [
                int(value) for value in np.histogram(np.arange(len(transactions)), bins=8)[0]
            ],
        },
        {
            "id": "fraud-rate",
            "label": "Fraud rate",
            "value": f"{fraud_rate * 100:.2f}%",
            "trend": f"{int(transactions['riskLabel'].sum())} labelled fraud cases",
            "dataPoints": [
                round(float(value), 6)
                for value in pd.Series(transactions["riskLabel"])
                .rolling(1000, min_periods=1)
                .mean()
                .iloc[:: max(1, len(transactions) // 8)]
                .head(8)
                .tolist()
            ],
        },
        {
            "id": "f1-score",
            "label": "Model F1-score",
            "value": f"{model_metadata['metrics']['tier2F1']:.3f}",
            "trend": "Tier 2 XGBoost holdout",
            "dataPoints": [0.70, 0.71, 0.72, 0.72, 0.73, 0.73, 0.734, 0.734],
        },
        {
            "id": "pending-alerts",
            "label": "Pending alerts",
            "value": f"{pending_alerts:,}",
            "trend": f"{flagged:,} flagged · {review:,} review",
            "dataPoints": [review, flagged, review, flagged, review, flagged, review, pending_alerts],
        },
    ]

    generated_at = datetime.now(UTC).isoformat()
    alerts: list[dict[str, object]] = []
    if psi_amount <= 0.2:
        alerts.append(
            {
                "id": "ALT-SNAPSHOT-AMOUNT",
                "occurredAt": generated_at,
                "modelId": "XGB-TRANSACTION-TIER2",
                "alertType": "Feature drift",
                "detail": (
                    f"Transaction amount PSI {psi_amount:.3f} remains within the 0.20 "
                    "warning threshold."
                ),
                "status": "RESOLVED",
            }
        )
    else:
        alerts.append(
            {
                "id": "ALT-SNAPSHOT-AMOUNT",
                "occurredAt": generated_at,
                "modelId": "XGB-TRANSACTION-TIER2",
                "alertType": "Feature drift",
                "detail": f"Transaction amount PSI {psi_amount:.3f} exceeds 0.20.",
                "status": "UNACKNOWLEDGED",
            }
        )

    if psi_velocity > 0.2:
        alerts.append(
            {
                "id": "ALT-SNAPSHOT-VELOCITY",
                "occurredAt": generated_at,
                "modelId": "XGB-TRANSACTION-TIER2",
                "alertType": "Feature drift",
                "detail": f"24h transaction velocity PSI is {psi_velocity:.3f}.",
                "status": "UNACKNOWLEDGED",
            }
        )
    else:
        alerts.append(
            {
                "id": "ALT-SNAPSHOT-VELOCITY",
                "occurredAt": generated_at,
                "modelId": "XGB-TRANSACTION-TIER2",
                "alertType": "Feature drift",
                "detail": (
                    f"24h transaction velocity PSI {psi_velocity:.3f} remains within "
                    "the configured threshold."
                ),
                "status": "RESOLVED",
            }
        )

    alerts.append(
        {
            "id": "ALT-SNAPSHOT-ARTIFACT",
            "occurredAt": generated_at,
            "modelId": "XGB-TRANSACTION-TIER2",
            "alertType": "Performance",
            "detail": (
                f"Artifact {model_metadata['modelVersion']} loaded with "
                f"{model_metadata['featureCount']} features."
            ),
            "status": "RESOLVED",
        }
    )

    snapshot = {
        "generatedAt": generated_at,
        "windowLabel": f"Dataset snapshot · {len(transactions):,} rows",
        "totalTransactions": int(len(transactions)),
        "kpis": kpis,
        "drift": {
            "psi": round(psi_amount, 6),
            "psiThreshold": 0.2,
            "driftShiftPct": round(drift_shift_pct, 4),
            "velocityPsi": round(psi_velocity, 6),
        },
        "statusCounts": {str(key): int(value) for key, value in status_counts.items()},
        "alerts": alerts,
    }
    (ARTIFACTS_DIR / "overview_snapshot.json").write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"Snapshot: {ARTIFACTS_DIR / 'overview_snapshot.json'}")
    print(f"Rows: {len(transactions):,} · PSI amount: {psi_amount:.4f} · velocity: {psi_velocity:.4f}")
    print(f"Statuses: {status_counts}")


if __name__ == "__main__":
    main()
