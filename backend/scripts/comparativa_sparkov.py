#!/usr/bin/env python3
"""Comparativa de familias de modelos sobre Sparkov (página "Comparativa IA").

Mismas variables (``app.ml.sparkov``) y misma división temporal que el modelo en
producción. Cada modelo elige su umbral con la validación (último 20 % del
entrenamiento) y se evalúa una sola vez en la prueba (jun–dic 2020).

* Red neuronal: perceptrón multicapa (scikit-learn), variables estandarizadas.
* ML clásico: regresión logística, Random Forest, LightGBM y XGBoost (producción).
* Ensambles: votación suave (promedio) y stacking con regresión logística. El
  stacking aprende con la primera mitad de la validación y fija el umbral con la
  segunda, para no reutilizar los mismos datos.

Salida: ``frontend/src/features/benchmark/benchmark-data.json``.
Uso: ``python backend/scripts/comparativa_sparkov.py`` desde la raíz (requiere lightgbm).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.sparkov import FEATURE_NAMES, batch_features, haversine_km  # noqa: E402

DATA_DIR = ROOT / "data" / "raw" / "sparkov"
OUTPUT = ROOT / "frontend" / "src" / "features" / "benchmark" / "benchmark-data.json"
SEED = 42


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def best_threshold(y: np.ndarray, p: np.ndarray) -> float:
    precision, recall, thresholds = precision_recall_curve(y, p)
    f1 = 2 * precision * recall / np.clip(precision + recall, 1e-12, None)
    return float(thresholds[int(np.argmax(f1[:-1]))])


def main() -> None:
    started = time.time()
    df = pd.concat(
        [pd.read_csv(DATA_DIR / "fraudTrain.csv").assign(split="train"), pd.read_csv(DATA_DIR / "fraudTest.csv").assign(split="test")],
        ignore_index=True,
    )
    df["ts"] = pd.to_datetime(df["trans_date_trans_time"])
    df["dob"] = pd.to_datetime(df["dob"])
    df["distancia_km"] = haversine_km(df["lat"], df["long"], df["merch_lat"], df["merch_long"])
    cards = sorted(df["cc_num"].unique())
    df["card_id"] = df["cc_num"].map({cc: f"TARJ-{i + 1:04d}" for i, cc in enumerate(cards)})
    is_train = (df["split"] == "train").to_numpy()
    medians = {k: float(v) for k, v in df.loc[is_train].groupby("category")["amt"].median().items()}
    x = batch_features(df, medians).to_numpy(dtype=np.float32)
    y = df["is_fraud"].to_numpy()

    cutoff = df.loc[is_train, "ts"].quantile(0.8)
    fit = is_train & (df["ts"] < cutoff).to_numpy()
    val = is_train & (df["ts"] >= cutoff).to_numpy()
    tst = ~is_train
    val_idx = np.flatnonzero(val)
    half = len(val_idx) // 2  # la validación está en orden temporal
    val_a, val_b = np.zeros_like(val), np.zeros_like(val)
    val_a[val_idx[:half]] = True
    val_b[val_idx[half:]] = True
    log(f"Ajuste {fit.sum():,} · validación {val.sum():,} · prueba {tst.sum():,}")

    scaler = StandardScaler().fit(x[fit])
    xs = scaler.transform(x).astype(np.float32)

    probs: dict[str, np.ndarray] = {}
    timings: dict[str, float] = {}

    def run(name: str, train_fn) -> None:  # type: ignore[no-untyped-def]
        t = time.time()
        probs[name] = train_fn()
        timings[name] = round(time.time() - t, 1)
        log(f"{name}: listo en {timings[name]} s")

    run("logistic", lambda: LogisticRegression(max_iter=2000, C=1.0).fit(xs[fit], y[fit]).predict_proba(xs)[:, 1])
    run(
        "mlp",
        lambda: MLPClassifier(
            hidden_layer_sizes=(128, 64, 32), alpha=1e-4, batch_size=1024, learning_rate_init=1e-3,
            max_iter=40, early_stopping=True, n_iter_no_change=5, random_state=SEED,
        ).fit(xs[fit], y[fit]).predict_proba(xs)[:, 1],
    )
    run(
        "random_forest",
        lambda: RandomForestClassifier(n_estimators=200, min_samples_leaf=2, n_jobs=-1, random_state=SEED)
        .fit(x[fit], y[fit]).predict_proba(x)[:, 1],
    )
    run(
        "lightgbm",
        lambda: lgb.LGBMClassifier(n_estimators=1500, learning_rate=0.05, num_leaves=63, subsample=0.8, subsample_freq=1,
                                   colsample_bytree=0.8, n_jobs=-1, random_state=SEED, verbose=-1)
        .fit(x[fit], y[fit], eval_set=[(x[val], y[val])], eval_metric="average_precision",
             callbacks=[lgb.early_stopping(150, verbose=False)]).predict_proba(x)[:, 1],
    )

    def production() -> np.ndarray:
        model = xgb.XGBClassifier()
        model.load_model(ROOT / "models_saved" / "xgboost_sparkov.json")
        return model.predict_proba(pd.DataFrame(x, columns=list(FEATURE_NAMES)))[:, 1]

    run("xgboost", production)

    bases = ["mlp", "random_forest", "lightgbm", "xgboost"]
    probs["voting"] = np.mean([probs[n] for n in bases], axis=0)
    logit = lambda p: np.log(np.clip(p, 1e-6, 1 - 1e-6) / (1 - np.clip(p, 1e-6, 1 - 1e-6)))  # noqa: E731
    stack_x = np.column_stack([logit(probs[n]) for n in bases])
    meta = LogisticRegression(max_iter=1000).fit(stack_x[val_a], y[val_a])
    probs["stacking"] = meta.predict_proba(stack_x)[:, 1]

    info = {
        "mlp": ("Red neuronal (MLP)", "neural", "Perceptrón multicapa 128-64-32 (scikit-learn)"),
        "logistic": ("Regresión logística", "classic", "Modelo lineal, variables estandarizadas"),
        "random_forest": ("Random Forest", "classic", "200 árboles en paralelo (bagging)"),
        "lightgbm": ("LightGBM", "classic", "Gradient boosting por hojas"),
        "xgboost": ("XGBoost", "classic", "Gradient boosting de árboles · modelo en producción"),
        "voting": ("Ensamble soft voting", "ensemble", "Promedio de red neuronal, RF, LightGBM y XGBoost"),
        "stacking": ("Ensamble stacking", "ensemble", "Regresión logística sobre los 4 modelos"),
    }
    results = []
    y_test = y[tst]
    for key, (name, family, detail) in info.items():
        threshold_mask = val_b if key == "stacking" else val
        threshold = best_threshold(y[threshold_mask], probs[key][threshold_mask])
        p_test = probs[key][tst]
        pred = p_test >= threshold
        results.append(
            {
                "id": key.replace("_", "-"),
                "name": name,
                "family": family,
                "detail": detail,
                "precision": round(float(precision_score(y_test, pred)), 4),
                "recall": round(float(recall_score(y_test, pred)), 4),
                "f1": round(float(f1_score(y_test, pred)), 4),
                "aucRoc": round(float(roc_auc_score(y_test, p_test)), 4),
                "averagePrecision": round(float(average_precision_score(y_test, p_test)), 4),
                "threshold": round(threshold, 4),
                "trainSeconds": timings.get(key),
                **({"selected": True} if key == "xgboost" else {}),
            }
        )
        r = results[-1]
        log(f"{name:24} F1 {r['f1']:.4f} · precisión {r['precision']:.3f} · recall {r['recall']:.3f} · AP {r['averagePrecision']:.4f}")

    results.sort(key=lambda r: r["f1"], reverse=True)
    OUTPUT.write_text(
        json.dumps(
            {
                "dataset": "Sparkov · prueba jun–dic 2020 (555,719 transacciones, 2,145 fraudes)",
                "note": "Todos los modelos usan las mismas 36 variables; el umbral de cada uno se eligió en la validación, no en la prueba.",
                "results": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    log(f"Listo en {(time.time() - started) / 60:.1f} min")


if __name__ == "__main__":
    main()
