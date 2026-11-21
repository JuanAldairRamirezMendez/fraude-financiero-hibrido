#!/usr/bin/env python3
"""Pipeline completo del modelo de detección de fraude (dataset Sparkov).

Fases:

1. Descarga del dataset: ``fraudTrain.csv`` y ``fraudTest.csv`` desde Hugging Face
   (``SlimG/transactions``, copia del dataset "Credit Card Transactions Fraud
   Detection"). Si ya están en ``data/raw/sparkov/`` no se vuelven a descargar.
2. Exploración: tamaño, nulos, duplicados y desbalance de clases.
3. Limpieza: se quitan los datos personales e identificadores; el número de
   tarjeta se reemplaza por un alias (``TARJ-0001`` … ``TARJ-0999``).
4. Transformación: 36 variables (``app.ml.sparkov``, las mismas que usa la API):
   24 de la compra y 12 del historial de la tarjeta, solo con compras anteriores.
5. División temporal: el propio dataset separa entrenamiento (primeros 18 meses) y
   prueba (últimos 6 meses). Del entrenamiento, el último 20 % en el tiempo es la
   validación.
6. Entrenamiento: XGBoost con parada temprana en la validación. Sin SMOTE ni
   pesos: aprende con la proporción real de fraude.
7. Umbral: el que maximiza el F1 en la validación.
8. Evaluación: se mide una sola vez en la prueba (F1, precisión, recall, AP, AUC).
9. Historial de tarjetas y verificación: se guarda el historial que usa la API y
   se comprueba que las variables en vivo coinciden con las del entrenamiento.
10. Exportación: modelo y artefactos del backend, y los datos de la web.

Salidas:

* ``models_saved/xgboost_sparkov.json``: modelo XGBoost (formato nativo, portable).
* ``backend/artifacts/``: ``model_metadata.json``, ``feature_contract.json``,
  ``card_history.parquet``, ``card_profiles.json``, ``overview_snapshot.json`` y
  ``overview_transactions.parquet``.
* ``frontend/src/features/``: datos de Evaluación, muestras reales, escenarios,
  catálogo de tarjetas y "Anatomía de un fraude".

Uso: ``python backend/scripts/build_sparkov_artifacts.py`` desde la raíz.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import shap
import xgboost as xgb
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.ml.sparkov import (  # noqa: E402
    CATEGORIES,
    FEATURE_NAMES,
    HISTORY_FEATURES,
    TRANSACTION_FEATURES,
    CardHistory,
    CardProfile,
    batch_features,
    channel_of,
    haversine_km,
)

DATA_DIR = ROOT / "data" / "raw" / "sparkov"
DATASET_URL = "https://huggingface.co/datasets/SlimG/transactions/resolve/main/{name}"
DATASET_FILES = ("fraudTrain.csv", "fraudTest.csv")
MODEL_PATH = ROOT / "models_saved" / "xgboost_sparkov.json"
ARTIFACTS = ROOT / "backend" / "artifacts"
FRONTEND = ROOT / "frontend" / "src" / "features"
DATASET_SOURCE = "Hugging Face · SlimG/transactions (Sparkov, Credit Card Transactions Fraud Detection)"
SEED = 42
VALIDATION_SHARE = 0.2
SHAP_SAMPLE_SIZE = 4000
SAMPLES_PER_CLASS = 100
CURVE_POINTS = 120

# Columnas que no ayudan a detectar fraude o identifican a la persona.
PERSONAL_COLUMNS = ["first", "last", "street", "zip", "job"]
IDENTIFIER_COLUMNS = ["Unnamed: 0", "merchant", "unix_time"]

CATEGORY_ES = {
    "entertainment": "entretenimiento",
    "food_dining": "restaurante",
    "gas_transport": "gasolina y transporte",
    "grocery_net": "supermercado en línea",
    "grocery_pos": "supermercado",
    "health_fitness": "salud y deporte",
    "home": "hogar",
    "kids_pets": "niños y mascotas",
    "misc_net": "compras varias en línea",
    "misc_pos": "compras varias",
    "personal_care": "cuidado personal",
    "shopping_net": "tienda en línea",
    "shopping_pos": "tienda",
    "travel": "viajes",
}


# =============================================================================
# Utilidades
# =============================================================================


def log(message: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)


def fase(numero: int, titulo: str) -> None:
    print(flush=True)
    log("=" * 70)
    log(f"FASE {numero}: {titulo.upper()}")
    log("=" * 70)


def _round(value: float, digits: int = 4) -> float:
    return float(round(float(value), digits))


def _downsample(xs: np.ndarray, ys: np.ndarray, points: int) -> list[list[float]]:
    idx = np.arange(len(xs)) if len(xs) <= points else np.unique(np.linspace(0, len(xs) - 1, points).round().astype(int))
    return [[_round(xs[i]), _round(ys[i])] for i in idx]


def _write_json(path: Path, data: object, **options: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, **options) + "\n", encoding="utf-8")


def confusion(y: np.ndarray, predicted: np.ndarray, amounts: np.ndarray) -> dict:
    tp = predicted & (y == 1)
    fn = ~predicted & (y == 1)
    return {
        "tp": int(tp.sum()),
        "fp": int((predicted & (y == 0)).sum()),
        "fn": int(fn.sum()),
        "tn": int((~predicted & (y == 0)).sum()),
        "caughtAmount": _round(amounts[tp].sum(), 2),
        "missedAmount": _round(amounts[fn].sum(), 2),
    }


def rate_by(frame: pd.DataFrame, column: str) -> list[dict]:
    grouped = frame.groupby(column, observed=True)["is_fraud"].agg(["count", "sum"]).reset_index().sort_values(column)
    return [
        {
            "key": str(row[column]),
            "transactions": int(row["count"]),
            "frauds": int(row["sum"]),
            "fraudRate": _round(row["sum"] / row["count"], 5),
        }
        for _, row in grouped.iterrows()
    ]


def psi(expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> float:
    edges = np.unique(np.quantile(expected, np.linspace(0, 1, buckets + 1)))
    if edges.size < 3:
        return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    e = np.clip(np.histogram(expected, edges)[0] / len(expected), 1e-4, None)
    a = np.clip(np.histogram(actual, edges)[0] / len(actual), 1e-4, None)
    return float(np.sum((a - e) * np.log(a / e)))


@dataclass
class Split:
    is_train: np.ndarray
    fit: np.ndarray
    val: np.ndarray
    tst: np.ndarray


@dataclass
class TrainedModel:
    model: xgb.XGBClassifier
    trees: int
    sha: str
    version: str


# =============================================================================
# FASE 1: Descarga del dataset
# =============================================================================


def fase1_descarga() -> pd.DataFrame:
    fase(1, "Descarga del dataset")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for name in DATASET_FILES:
        path = DATA_DIR / name
        if path.exists():
            log(f"{name}: ya descargado ({path.stat().st_size / 1e6:,.0f} MB)")
            continue
        log(f"{name}: descargando desde Hugging Face…")
        partial = path.with_suffix(".part")
        urllib.request.urlretrieve(DATASET_URL.format(name=name), partial)  # noqa: S310 (URL fija)
        partial.replace(path)
        log(f"{name}: listo ({path.stat().st_size / 1e6:,.0f} MB)")

    train = pd.read_csv(DATA_DIR / "fraudTrain.csv")
    test = pd.read_csv(DATA_DIR / "fraudTest.csv")
    # El dataset ya viene separado en el tiempo: se marca de qué archivo es cada fila.
    return pd.concat([train.assign(split="train"), test.assign(split="test")], ignore_index=True)


# =============================================================================
# FASE 2: Exploración
# =============================================================================


def fase2_exploracion(df: pd.DataFrame) -> None:
    fase(2, "Exploración y calidad de datos")
    columns = [c for c in df.columns if c not in ("split", "Unnamed: 0")]
    frauds = int(df["is_fraud"].sum())
    legit = len(df) - frauds
    log(f"Transacciones: {len(df):,} · columnas: {len(columns)} · tarjetas: {df['cc_num'].nunique()}")
    log(f"Valores nulos: {int(df[columns].isna().sum().sum())} · filas duplicadas: {int(df.duplicated(subset=columns).sum())}")
    log(f"Legítimas: {legit:,} ({legit / len(df):.2%}) · fraudes: {frauds:,} ({frauds / len(df):.2%})")
    log(f"Desbalance: 1 fraude por cada {legit / frauds:,.0f} legítimas")
    log(f"Periodo: {df['trans_date_trans_time'].min()} → {df['trans_date_trans_time'].max()}")


# =============================================================================
# FASE 3: Limpieza
# =============================================================================


def fase3_limpieza(df: pd.DataFrame) -> pd.DataFrame:
    fase(3, "Limpieza")
    before = len(df)
    df = df.drop_duplicates(subset=[c for c in df.columns if c != "Unnamed: 0"]).dropna().reset_index(drop=True)
    log(f"Filas eliminadas por nulos o duplicados: {before - len(df)}")

    df = df.drop(columns=PERSONAL_COLUMNS + IDENTIFIER_COLUMNS)
    log(f"Columnas quitadas: {', '.join(PERSONAL_COLUMNS + IDENTIFIER_COLUMNS)}")

    df["ts"] = pd.to_datetime(df["trans_date_trans_time"])
    df["dob"] = pd.to_datetime(df["dob"])
    # Alias estable por tarjeta: el número de tarjeta real nunca sale de este script.
    cards = sorted(df["cc_num"].unique())
    alias = {cc: f"TARJ-{i + 1:04d}" for i, cc in enumerate(cards)}
    df["card_id"] = df["cc_num"].map(alias)
    df["tx_id"] = "TX-" + df["trans_num"].str[:10].str.upper()
    df = df.drop(columns=["cc_num", "trans_num", "trans_date_trans_time"])
    log(f"Número de tarjeta reemplazado por alias: {len(cards)} tarjetas (TARJ-0001 … TARJ-{len(cards):04d})")
    return df


# =============================================================================
# FASE 4: Transformación (variables)
# =============================================================================


def fase4_transformacion(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    fase(4, "Transformación: creación de variables")
    df["distancia_km"] = haversine_km(df["lat"], df["long"], df["merch_lat"], df["merch_long"])
    log("4 coordenadas (cliente y comercio) → distancia al comercio en km")

    # Mediana de monto por categoría, calculada solo con el entrenamiento.
    is_train = (df["split"] == "train").to_numpy()
    medians = {k: float(v) for k, v in df.loc[is_train].groupby("category")["amt"].median().items()}

    features = batch_features(df, medians)
    log(f"{len(FEATURE_NAMES)} variables: {len(TRANSACTION_FEATURES)} de la compra y {len(HISTORY_FEATURES)} del historial de la tarjeta")
    log("El historial solo usa compras anteriores de la misma tarjeta (nunca el futuro ni las etiquetas)")
    return features, medians


# =============================================================================
# FASE 5: División temporal
# =============================================================================


def fase5_division(df: pd.DataFrame) -> Split:
    fase(5, "División temporal")
    is_train = (df["split"] == "train").to_numpy()
    cutoff = df.loc[is_train, "ts"].quantile(1 - VALIDATION_SHARE)
    split = Split(
        is_train=is_train,
        fit=is_train & (df["ts"] < cutoff).to_numpy(),
        val=is_train & (df["ts"] >= cutoff).to_numpy(),
        tst=~is_train,
    )
    y = df["is_fraud"].to_numpy()
    for name, mask, purpose in [
        ("Entrenamiento", split.fit, "el modelo aprende"),
        ("Validación", split.val, "parada temprana y umbral"),
        ("Prueba", split.tst, "se mide una sola vez"),
    ]:
        log(f"{name}: {int(mask.sum()):,} compras · {int(y[mask].sum()):,} fraudes · {mask.sum() / len(df):.0%} → {purpose}")
    return split


# =============================================================================
# FASE 6: Entrenamiento
# =============================================================================


def fase6_entrenamiento(features: pd.DataFrame, y: np.ndarray, split: Split) -> TrainedModel:
    fase(6, "Entrenamiento (XGBoost)")
    model = xgb.XGBClassifier(
        n_estimators=3000,
        learning_rate=0.05,
        max_depth=7,
        min_child_weight=3,
        subsample=0.8,
        colsample_bytree=0.8,
        tree_method="hist",
        eval_metric="aucpr",
        early_stopping_rounds=150,
        n_jobs=-1,
        random_state=SEED,
    )
    log("Entrenando con parada temprana (se detiene cuando deja de mejorar en la validación)…")
    model.fit(features[split.fit], y[split.fit], eval_set=[(features[split.val], y[split.val])], verbose=False)
    trees = int(model.best_iteration) + 1
    log(f"Mejor modelo: {trees} árboles")

    # Se guarda solo hasta el mejor árbol: el archivo predice igual sin depender de best_iteration.
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    model.get_booster()[:trees].save_model(MODEL_PATH)
    final = xgb.XGBClassifier()
    final.load_model(MODEL_PATH)
    sha = hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()
    log(f"Modelo guardado en {MODEL_PATH.relative_to(ROOT)}")
    return TrainedModel(model=final, trees=trees, sha=sha, version=f"xgboost-sparkov-{sha[:12]}")


# =============================================================================
# FASE 7: Umbral de decisión
# =============================================================================


def fase7_umbral(trained: TrainedModel, features: pd.DataFrame, y: np.ndarray, split: Split) -> tuple[float, float]:
    fase(7, "Elección del umbral")
    p_val = trained.model.predict_proba(features[split.val])[:, 1]
    precision, recall, thresholds = precision_recall_curve(y[split.val], p_val)
    f1 = 2 * precision * recall / np.clip(precision + recall, 1e-12, None)
    best = int(np.argmax(f1[:-1]))
    threshold = float(thresholds[best])
    log(f"Umbral que maximiza el F1 en la validación: {threshold:.4f} (F1 validación {f1[best]:.4f})")
    return threshold, float(f1[best])


# =============================================================================
# FASE 8: Evaluación en la prueba
# =============================================================================


def fase8_evaluacion(
    df: pd.DataFrame, trained: TrainedModel, features: pd.DataFrame, y: np.ndarray, split: Split, threshold: float, validation_f1: float
) -> tuple[np.ndarray, dict[str, float], pd.DataFrame]:
    fase(8, "Evaluación en la prueba (datos nunca vistos)")
    p_all = trained.model.predict_proba(features)[:, 1]
    p_test, y_test = p_all[split.tst], y[split.tst]
    pred_test = p_test >= threshold
    metrics = {
        "testF1": f1_score(y_test, pred_test),
        "testPrecision": precision_score(y_test, pred_test),
        "testRecall": recall_score(y_test, pred_test),
        "testAveragePrecision": average_precision_score(y_test, p_test),
        "testAucRoc": roc_auc_score(y_test, p_test),
        "validationF1": validation_f1,
    }
    tp = int((pred_test & (y_test == 1)).sum())
    fp = int((pred_test & (y_test == 0)).sum())
    log(f"F1 {metrics['testF1']:.4f} · precisión {metrics['testPrecision']:.4f} · recall {metrics['testRecall']:.4f}")
    log(f"AP {metrics['testAveragePrecision']:.4f} · AUC-ROC {metrics['testAucRoc']:.4f}")
    log(f"Fraudes detectados: {tp:,} de {int(y_test.sum()):,} · legítimas bloqueadas por error: {fp:,}")

    test = df.loc[split.tst].copy()
    test["probability"] = p_test
    test["blocked"] = pred_test
    return p_all, metrics, test


# =============================================================================
# FASE 9: Historial de tarjetas y verificación entrenamiento/API
# =============================================================================


def fase9_historial(
    df: pd.DataFrame, features: pd.DataFrame, medians: dict[str, float], test: pd.DataFrame
) -> list[dict]:
    fase(9, "Historial de tarjetas y verificación")
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    history = pd.DataFrame(
        {
            "card_id": df["card_id"],
            # Segundos Unix explícitos: pandas 3 guarda las fechas en microsegundos.
            "ts": df["ts"].astype("datetime64[s]").astype("int64"),
            "amt": df["amt"].astype("float64"),
            "category": df["category"].astype("category"),
        }
    ).sort_values(["card_id", "ts"])
    history.to_parquet(ARTIFACTS / "card_history.parquet", index=False, compression="zstd")
    profiles_frame = df.sort_values("ts").groupby("card_id").first()
    profiles = [
        {
            "cardId": card,
            "gender": row["gender"],
            "dob": row["dob"].date().isoformat(),
            "city": row["city"],
            "state": row["state"],
            "cityPop": int(row["city_pop"]),
        }
        for card, row in profiles_frame.iterrows()
    ]
    _write_json(ARTIFACTS / "card_profiles.json", profiles)
    log(f"Historial guardado: {len(history):,} compras de {len(profiles)} tarjetas")

    # Verificación: las variables en vivo deben coincidir con las del entrenamiento.
    card_history = CardHistory(
        history.assign(category=history["category"].astype(str)),
        [
            CardProfile(p["cardId"], p["gender"], datetime.fromisoformat(p["dob"]), p["city"], p["state"], p["cityPop"])
            for p in profiles
        ],
    )
    check = test.sample(300, random_state=SEED)
    worst = 0.0
    for idx, row in check.iterrows():
        online, _ = card_history.features_for(
            card_id=row["card_id"],
            when=row["ts"].to_pydatetime(),
            amount=float(row["amt"]),
            category=row["category"],
            distance_km=float(row["distancia_km"]),
            category_medians=medians,
        )
        diff = np.abs(online.to_numpy(dtype=float)[0] - features.loc[idx].to_numpy(dtype=float))
        worst = max(worst, float(np.max(diff / (np.abs(features.loc[idx].to_numpy(dtype=float)) + 1))))
    log(f"Paridad entrenamiento/API en 300 compras: diferencia relativa máxima {worst:.2e}")
    if worst > 1e-6:
        raise SystemExit("Las variables en vivo no coinciden con las de entrenamiento")
    return profiles


# =============================================================================
# FASE 10: Exportación de artefactos
# =============================================================================


def exportar_metadata(
    df: pd.DataFrame, split: Split, trained: TrainedModel, threshold: float, metrics: dict, medians: dict, profiles: list[dict], generated: str
) -> None:
    card_ids = [p["cardId"] for p in profiles]
    metadata = {
        "version": "2.0.0",
        "generatedAt": generated,
        "modelId": "xgboost-sparkov",
        "modelVersion": trained.version,
        "artifact": "models_saved/xgboost_sparkov.json",
        "artifactSha256": trained.sha,
        "algorithm": f"XGBoost ({trained.trees} árboles) con historial de la tarjeta",
        "calibration": "none",
        "featureCount": len(FEATURE_NAMES),
        "calibratedThreshold": _round(threshold, 6),
        "calibrationF1": _round(metrics["validationF1"], 6),
        "calibrationNote": (
            "El umbral maximiza el F1 en la validación temporal (último 20 % del entrenamiento). "
            "La prueba (jun–dic 2020) no se usó para ajustar nada."
        ),
        "metrics": {k: _round(v, 6) for k, v in metrics.items()},
        "dataset": {
            "source": DATASET_SOURCE,
            "rows": int(len(df)),
            "fraudRate": _round(df["is_fraud"].mean(), 5),
            "trainRows": int(split.is_train.sum()),
            "testRows": int(split.tst.sum()),
            "split": "temporal: ene 2019–jun 2020 entrenamiento, jun–dic 2020 prueba",
        },
    }
    _write_json(ARTIFACTS / "model_metadata.json", metadata, indent=2)

    contract = {
        "version": "2.0.0",
        "generatedAt": generated,
        "labelColumn": "is_fraud",
        "featureNames": list(FEATURE_NAMES),
        "categoryMedians": medians,
        "categories": {"category": list(CATEGORIES), "cardId": card_ids},
        "defaults": {
            "cardId": card_ids[0],
            "transactionTime": "2020-07-01T12:00:00",
            "amount": 50.0,
            "category": "grocery_pos",
            "merchantDistanceKm": 75.0,
        },
        "decisionThreshold": {"default": _round(threshold, 6), "min": 0.0, "max": 1.0, "step": 0.001},
        "fields": [
            {"name": "cardId", "label": "Tarjeta", "group": "Cliente", "kind": "category", "default": card_ids[0], "options": card_ids},
            {"name": "transactionTime", "label": "Fecha y hora", "group": "Transacción", "kind": "datetime", "default": "2020-07-01T12:00:00"},
            {"name": "amount", "label": "Monto", "group": "Transacción", "kind": "number", "default": 50.0, "min": 0.01, "max": 50000, "step": 0.01,
             "observedMin": _round(df["amt"].min(), 2), "observedMax": _round(df["amt"].max(), 2)},
            {"name": "category", "label": "Categoría del comercio", "group": "Comercio", "kind": "category", "default": "grocery_pos", "options": list(CATEGORIES)},
            {"name": "merchantDistanceKm", "label": "Distancia al comercio (km)", "group": "Comercio", "kind": "number", "default": 75.0, "min": 0, "max": 1000, "step": 0.1,
             "observedMin": _round(df["distancia_km"].min(), 2), "observedMax": _round(df["distancia_km"].max(), 2)},
        ],
    }
    _write_json(ARTIFACTS / "feature_contract.json", contract, indent=2)
    log("Backend: model_metadata.json y feature_contract.json")


def exportar_resumen(
    df: pd.DataFrame, features: pd.DataFrame, split: Split, test: pd.DataFrame, trained: TrainedModel, threshold: float, metrics: dict, generated: str
) -> None:
    test_sorted = test.sort_values(["probability", "amt"], ascending=[False, False], kind="stable")
    overview = pd.DataFrame(
        {
            "id": test_sorted["tx_id"].to_numpy(),
            "customerId": test_sorted["card_id"].to_numpy(),
            "transactionHour": test_sorted["ts"].dt.hour.astype("int16").to_numpy(),
            "transactionDayOfWeek": test_sorted["ts"].dt.day_of_week.astype("int16").to_numpy(),
            "amount": test_sorted["amt"].round(2).to_numpy(),
            "country": test_sorted["state"].to_numpy(),
            "region": test_sorted["city"].to_numpy(),
            "merchantCategory": test_sorted["category"].to_numpy(),
            "transactionType": test_sorted["category"].map(channel_of).to_numpy(),
            "deviceType": "tarjeta",
            "score": np.clip(np.rint(test_sorted["probability"] * 100), 0, 100).astype("int16"),
            "status": np.where(test_sorted["blocked"], "Flagged", "Approved"),
            "riskLabel": test_sorted["is_fraud"].astype("int8").to_numpy(),
            "probability": test_sorted["probability"].round(6).to_numpy(),
            "occurredAt": test_sorted["ts"].dt.strftime("%Y-%m-%dT%H:%M:%S").to_numpy(),
        }
    )
    for column in ["country", "region", "merchantCategory", "transactionType", "deviceType", "status"]:
        overview[column] = overview[column].astype("category")
    overview.to_parquet(ARTIFACTS / "overview_transactions.parquet", index=False, compression="zstd")

    train_frame = df.loc[split.is_train]
    psi_amount = psi(train_frame["amt"].to_numpy(), test["amt"].to_numpy())
    psi_velocity = psi(features.loc[split.is_train, "monto_24h"].to_numpy(), features.loc[split.tst, "monto_24h"].to_numpy())
    shift = (test["amt"].mean() - train_frame["amt"].mean()) / train_frame["amt"].mean() * 100
    blocked = int(test["blocked"].sum())
    snapshot = {
        "generatedAt": generated,
        "windowLabel": f"Periodo de prueba jun–dic 2020 · {len(test):,} transacciones",
        "totalTransactions": int(len(test)),
        "kpis": [
            {"id": "transactions", "label": "Total transactions", "value": f"{len(test):,}", "trend": "Test period Jun–Dec 2020",
             "dataPoints": [int(v) for v in test.groupby(test["ts"].dt.month).size().tolist()]},
            {"id": "fraud-rate", "label": "Fraud rate", "value": f"{test['is_fraud'].mean() * 100:.2f}%",
             "trend": f"{int(test['is_fraud'].sum())} labelled fraud cases",
             "dataPoints": [round(float(v), 6) for v in test.groupby(test["ts"].dt.month)["is_fraud"].mean().tolist()]},
            {"id": "f1-score", "label": "Model F1-score", "value": f"{metrics['testF1']:.3f}",
             "trend": f"Test set · threshold {threshold:.3f}", "dataPoints": [round(metrics["testF1"], 6)] * 6},
            {"id": "pending-alerts", "label": "Pending alerts", "value": f"{blocked:,}",
             "trend": f"{blocked:,} blocked at threshold {threshold:.3f}", "dataPoints": [blocked] * 6},
        ],
        "drift": {"psi": round(psi_amount, 6), "psiThreshold": 0.2, "driftShiftPct": round(float(shift), 4), "velocityPsi": round(psi_velocity, 6)},
        "statusCounts": {"Flagged": blocked, "Approved": int(len(test) - blocked)},
        "alerts": [
            {"id": "ALT-SNAPSHOT-AMOUNT", "occurredAt": generated, "modelId": "XGB-SPARKOV", "alertType": "Feature drift",
             "detail": f"Transaction amount PSI {psi_amount:.3f} remains within the 0.20 warning threshold." if psi_amount <= 0.2 else f"Transaction amount PSI {psi_amount:.3f} exceeds 0.20.",
             "status": "RESOLVED" if psi_amount <= 0.2 else "UNACKNOWLEDGED"},
            {"id": "ALT-SNAPSHOT-VELOCITY", "occurredAt": generated, "modelId": "XGB-SPARKOV", "alertType": "Feature drift",
             "detail": f"24h transaction velocity PSI {psi_velocity:.3f} remains within the configured threshold." if psi_velocity <= 0.2 else f"24h transaction velocity PSI is {psi_velocity:.3f}.",
             "status": "RESOLVED" if psi_velocity <= 0.2 else "UNACKNOWLEDGED"},
            {"id": "ALT-SNAPSHOT-ARTIFACT", "occurredAt": generated, "modelId": "XGB-SPARKOV", "alertType": "Performance",
             "detail": f"Artifact {trained.version} loaded with {len(FEATURE_NAMES)} features.", "status": "RESOLVED"},
        ],
    }
    _write_json(ARTIFACTS / "overview_snapshot.json", snapshot, indent=2)
    log(f"Backend: snapshot del Resumen ({len(overview):,} filas · PSI monto {psi_amount:.3f} · PSI velocidad {psi_velocity:.3f})")


def exportar_evaluacion(
    df: pd.DataFrame, features: pd.DataFrame, split: Split, test: pd.DataFrame, trained: TrainedModel, threshold: float, metrics: dict, generated: str
) -> None:
    y_test = test["is_fraud"].to_numpy()
    p_test = test["probability"].to_numpy()
    amounts = test["amt"].to_numpy()
    fpr, tpr, _ = roc_curve(y_test, p_test)
    prec, rec, _ = precision_recall_curve(y_test, p_test)
    sample = features.loc[split.tst].sample(SHAP_SAMPLE_SIZE, random_state=SEED)
    values = np.asarray(shap.TreeExplainer(trained.model).shap_values(sample))
    owner = ["categoria" if name.startswith("cat_") else name for name in FEATURE_NAMES]
    importance = pd.DataFrame(np.abs(values), columns=list(FEATURE_NAMES)).T.groupby(owner).sum().T.mean().sort_values(ascending=False)
    total = float(importance.sum()) or 1.0
    df = df.assign(
        hora=df["ts"].dt.hour,
        canal=df["category"].map(channel_of),
        grupo_edad=pd.cut(((df["ts"] - df["dob"]).dt.days / 365.25), [0, 25, 35, 50, 65, 120], labels=["<25", "25-34", "35-49", "50-64", "65+"]),
    )
    evaluation = {
        "generatedAt": generated,
        "modelVersion": trained.version,
        "dataset": {
            "source": DATASET_SOURCE,
            "rows": int(len(df)),
            "fraudRate": _round(df["is_fraud"].mean(), 5),
            "split": "temporal: entrenamiento ene 2019–jun 2020, prueba jun–dic 2020",
            "testRows": int(len(test)),
            "testFrauds": int(y_test.sum()),
            "avgFraudAmount": _round(amounts[y_test == 1].mean(), 2),
        },
        "calibratedThreshold": _round(threshold, 6),
        "calibrated": {"threshold": _round(threshold, 6), **confusion(y_test, test["blocked"].to_numpy(), amounts)},
        "aucRoc": _round(metrics["testAucRoc"]),
        "averagePrecision": _round(metrics["testAveragePrecision"]),
        "thresholds": [
            {"threshold": _round(t, 2), **confusion(y_test, p_test >= t, amounts)} for t in np.round(np.arange(0, 1.0001, 0.01), 2)
        ],
        "roc": _downsample(fpr, tpr, CURVE_POINTS),
        "precisionRecall": _downsample(rec[::-1], prec[::-1], CURVE_POINTS),
        "globalImportance": [
            {"feature": f, "meanAbsShap": _round(v, 5), "share": _round(v / total, 4)} for f, v in importance.items()
        ],
        "shapSampleSize": SHAP_SAMPLE_SIZE,
        "profile": {
            "category": rate_by(df, "category"),
            "hour": rate_by(df, "hora"),
            "channel": rate_by(df, "canal"),
            "ageGroup": rate_by(df, "grupo_edad"),
        },
    }
    _write_json(FRONTEND / "evaluation" / "evaluation-data.json", evaluation, separators=(",", ":"))
    top = ", ".join(f"{f} {v / total:.1%}" for f, v in importance.head(3).items())
    log(f"Web: página Evaluación (importancia SHAP: {top})")


def exportar_analizador(
    df: pd.DataFrame, features: pd.DataFrame, split: Split, test: pd.DataFrame, p_all: np.ndarray, threshold: float, profiles: list[dict]
) -> None:
    def form_values(row: pd.Series) -> dict:
        return {
            "cardId": row["card_id"],
            "transactionTime": row["ts"].strftime("%Y-%m-%dT%H:%M:%S"),
            "amount": _round(row["amt"], 2),
            "category": row["category"],
            "merchantDistanceKm": _round(row["distancia_km"], 1),
        }

    # Muestras reales del periodo de prueba.
    frauds = test[test["is_fraud"] == 1].sample(SAMPLES_PER_CLASS, random_state=SEED)
    legit = test[test["is_fraud"] == 0].sample(SAMPLES_PER_CLASS, random_state=SEED)
    picked = pd.concat([frauds, legit]).sample(frac=1, random_state=SEED)
    samples = [{"id": row["tx_id"], "isFraud": bool(row["is_fraud"]), "values": form_values(row)} for _, row in picked.iterrows()]
    _write_json(
        FRONTEND / "analyzer" / "real-samples.json",
        {"source": DATASET_SOURCE, "note": f"{SAMPLES_PER_CLASS} fraudes y {SAMPLES_PER_CLASS} legítimas del periodo de prueba.", "samples": samples},
        separators=(",", ":"),
    )

    # Escenarios de ejemplo: habitual, sospechosa y fraude probable.
    feats_test = features.loc[split.tst]
    rng = np.random.default_rng(SEED)

    def pick(mask: np.ndarray) -> pd.Series:
        candidates = test[mask]
        return candidates.iloc[int(rng.integers(len(candidates)))]

    normal = pick(((test["is_fraud"] == 0) & (test["probability"] < 0.001) & (test["category"] == "grocery_pos") & test["ts"].dt.hour.between(10, 18)).to_numpy())
    suspicious = pick(((test["is_fraud"] == 1) & test["probability"].between(threshold + 0.05, 0.85)).to_numpy())
    fraud = pick(((test["is_fraud"] == 1) & (test["probability"] > 0.99) & (test["ts"].dt.hour.isin([22, 23, 0, 1, 2, 3]))).to_numpy())

    def describe(row: pd.Series) -> str:
        f = feats_test.loc[row.name]
        return (
            f"{CATEGORY_ES[row['category']].capitalize()} por US$ {row['amt']:,.2f} a las {row['ts']:%H:%M}; "
            f"la tarjeta lleva {int(f['compras_24h'])} compras (US$ {f['monto_24h']:,.0f}) en 24 h."
        )

    scenarios = [
        {"id": "normal", "label": "Compra habitual", "expectedRisk": "low", "description": describe(normal), "values": form_values(normal)},
        {"id": "suspicious", "label": "Sospechosa", "expectedRisk": "medium", "description": describe(suspicious), "values": form_values(suspicious)},
        {"id": "fraud", "label": "Fraude probable", "expectedRisk": "high", "description": describe(fraud), "values": form_values(fraud)},
    ]
    for item, row in zip(scenarios, [normal, suspicious, fraud], strict=True):
        item["expectedScore"] = int(round(row["probability"] * 100))
    _write_json(FRONTEND / "analyzer" / "scenarios.json", scenarios, indent=2)

    # Catálogo de tarjetas del formulario.
    catalog = [
        {"id": p["cardId"], "gender": p["gender"], "birthYear": int(p["dob"][:4]), "city": p["city"], "state": p["state"]}
        for p in profiles
    ]
    _write_json(FRONTEND / "analyzer" / "cards.json", catalog, separators=(",", ":"))
    log("Web: Analizador (" + ", ".join(f"{s['label']} {s['expectedScore']}%" for s in scenarios) + ")")

    exportar_anatomia(df, p_all, threshold, profiles, fraud)


def exportar_anatomia(df: pd.DataFrame, p_all: np.ndarray, threshold: float, profiles: list[dict], fraud: pd.Series) -> None:
    """Resumen: "Anatomía de un fraude", la tarjeta del escenario de fraude."""
    card_rows = df[df["card_id"] == fraud["card_id"]].assign(probability=p_all[(df["card_id"] == fraud["card_id"]).to_numpy()])
    episode = card_rows[(card_rows["is_fraud"] == 1) & ((card_rows["ts"] - fraud["ts"]).abs() <= pd.Timedelta(days=3))]
    first_fraud, last_fraud = episode["ts"].min(), episode["ts"].max()
    start, end = first_fraud - pd.Timedelta(days=4), last_fraud + pd.Timedelta(days=1)
    window = card_rows[(card_rows["ts"] >= start) & (card_rows["ts"] <= end)].sort_values("ts")
    before = window[window["ts"] < first_fraud]
    blocked_window = window["probability"] >= threshold
    profile = next(p for p in profiles if p["cardId"] == fraud["card_id"])
    anatomy = {
        "cardId": fraud["card_id"],
        "gender": profile["gender"],
        "age": int((first_fraud - pd.Timestamp(profile["dob"])).days // 365.25),
        "city": profile["city"],
        "state": profile["state"],
        "threshold": _round(threshold, 4),
        "start": start.strftime("%Y-%m-%dT%H:%M:%S"),
        "end": end.strftime("%Y-%m-%dT%H:%M:%S"),
        "before": {"purchases": int(len(before)), "averageAmount": _round(before["amt"].mean(), 2), "maxAmount": _round(before["amt"].max(), 2)},
        "burst": {
            "purchases": int(len(episode)),
            "totalAmount": _round(episode["amt"].sum(), 2),
            "hours": _round((last_fraud - first_fraud).total_seconds() / 3600, 1),
            "firstAt": first_fraud.strftime("%Y-%m-%dT%H:%M:%S"),
        },
        "model": {
            "fraudsBlocked": int((blocked_window & (window["is_fraud"] == 1)).sum()),
            "frauds": int((window["is_fraud"] == 1).sum()),
            "falseAlarms": int((blocked_window & (window["is_fraud"] == 0)).sum()),
            "legitimate": int((window["is_fraud"] == 0).sum()),
        },
        "purchases": [
            {
                "time": row["ts"].strftime("%Y-%m-%dT%H:%M:%S"),
                "amount": _round(row["amt"], 2),
                "category": row["category"],
                "score": int(round(row["probability"] * 100)),
                "isFraud": bool(row["is_fraud"]),
            }
            for _, row in window.iterrows()
        ],
    }
    _write_json(FRONTEND / "overview" / "anatomy.json", anatomy, indent=1)
    log(
        f"Web: Anatomía de un fraude ({anatomy['cardId']} · ráfaga de {anatomy['burst']['purchases']} fraudes "
        f"en {anatomy['burst']['hours']} h · bloqueó {anatomy['model']['fraudsBlocked']}/{anatomy['model']['frauds']} · "
        f"falsas alarmas {anatomy['model']['falseAlarms']})"
    )


def fase10_exportacion(
    df: pd.DataFrame,
    features: pd.DataFrame,
    medians: dict[str, float],
    split: Split,
    trained: TrainedModel,
    threshold: float,
    p_all: np.ndarray,
    metrics: dict,
    test: pd.DataFrame,
    profiles: list[dict],
) -> None:
    fase(10, "Exportación de artefactos")
    generated = datetime.now(UTC).isoformat()
    exportar_metadata(df, split, trained, threshold, metrics, medians, profiles, generated)
    exportar_resumen(df, features, split, test, trained, threshold, metrics, generated)
    exportar_evaluacion(df, features, split, test, trained, threshold, metrics, generated)
    exportar_analizador(df, features, split, test, p_all, threshold, profiles)


# =============================================================================
# Pipeline
# =============================================================================


def main() -> None:
    # La consola de Windows no usa UTF-8 por defecto (tildes, "→", "·").
    sys.stdout.reconfigure(encoding="utf-8")
    started = datetime.now(UTC)

    raw = fase1_descarga()
    fase2_exploracion(raw)
    df = fase3_limpieza(raw)
    features, medians = fase4_transformacion(df)
    y = df["is_fraud"].to_numpy()
    split = fase5_division(df)
    trained = fase6_entrenamiento(features, y, split)
    threshold, val_f1 = fase7_umbral(trained, features, y, split)
    p_all, metrics, test = fase8_evaluacion(
        df, trained, features, y, split, threshold, val_f1
    )
    profiles = fase9_historial(df, features, medians, test)
    fase10_exportacion(
        df, features, medians, split, trained,
        threshold, p_all, metrics, test, profiles,
    )

    print(flush=True)
    log(f"Pipeline completo en {(datetime.now(UTC) - started).total_seconds() / 60:.1f} min · modelo {trained.version}")


if __name__ == "__main__":
    main()
