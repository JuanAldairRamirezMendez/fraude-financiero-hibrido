#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 04_train_models.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
METODOLOGÍA: CRISP-DM - Fase 4 (Modelado)
AUTOR: Ramirez Mendez, Juan Aldair
FECHA: 2026
=============================================================================
DESCRIPCIÓN:
    Entrena los modelos individuales (Random Forest, XGBoost, SVM, DNN) 
    según las especificaciones de la Sección 5.5 del documento.
    Evalúa el desempeño en el conjunto de prueba original (desbalanceado).
=============================================================================
"""

import os
import logging
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Scikit-learn
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

# XGBoost
import xgboost as xgb

# TensorFlow / Keras
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.callbacks import EarlyStopping

# =========================================================================
# CONFIGURACIÓN INICIAL
# =========================================================================
load_dotenv()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

MODELS_DIR = Path("models_saved")
MODELS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "train_models.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configuración de Base de Datos
DB_USER = os.getenv("DB_USER", "fraud_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tu_password_seguro")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fraud_detection")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# =========================================================================
# FUNCIONES AUXILIARES
# =========================================================================

def load_data_from_db():
    """Carga los conjuntos de entrenamiento y prueba desde PostgreSQL."""
    logger.info("Conectando a PostgreSQL para cargar los datos...")
    engine = create_engine(DATABASE_URL)
    
    logger.info("Cargando 'train_cleaned_balanced'...")
    df_train = pd.read_sql("SELECT * FROM train_cleaned_balanced", engine)
    
    logger.info("Cargando 'test_cleaned_original'...")
    df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)
    
    # Separar X e y
    X_train = df_train.drop(columns=['risk_label'])
    y_train = df_train['risk_label']
    
    X_test = df_test.drop(columns=['risk_label'])
    y_test = df_test['risk_label']
    
    logger.info(f"Datos cargados. Train: {X_train.shape}, Test: {X_test.shape}")
    return X_train, y_train, X_test, y_test


def evaluate_model(y_true, y_pred, y_pred_proba, model_name):
    """Evalúa el modelo con las métricas de la Sección 3.6."""
    precision = precision_score(y_true, y_pred, zero_division=0)
    recall = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    auc_roc = roc_auc_score(y_true, y_pred_proba)
    
    logger.info(f"\n--- Métricas para {model_name} ---")
    logger.info(f"Precision: {precision:.4f}")
    logger.info(f"Recall   : {recall:.4f}")
    logger.info(f"F1-Score : {f1:.4f}")
    logger.info(f"AUC-ROC  : {auc_roc:.4f}")
    
    return {
        'model': model_name,
        'precision': round(precision, 4),
        'recall': round(recall, 4),
        'f1_score': round(f1, 4),
        'auc_roc': round(auc_roc, 4)
    }


def predict_with_threshold(y_pred_proba, threshold=0.3):
    """Aplica un umbral de probabilidad personalizado (Sección 5.5.1)."""
    return (y_pred_proba >= threshold).astype(int)


# =========================================================================
# ENTRENAMIENTO DE MODELOS
# =========================================================================

def train_random_forest(X_train, y_train, X_test, y_test):
    logger.info("\n[1/4] Entrenando Random Forest (Sección 5.5.1)...")
    rf = RandomForestClassifier(
        n_estimators=100,
        class_weight='balanced',
        random_state=42,
        n_jobs=-1
    )
    rf.fit(X_train, y_train)
    
    # Obtener probabilidades
    y_pred_proba = rf.predict_proba(X_test)[:, 1]
    
    # Aplicar umbral de 0.3 para favorecer la detección de la clase minoritaria
    y_pred = predict_with_threshold(y_pred_proba, threshold=0.3)
    
    metrics = evaluate_model(y_test, y_pred, y_pred_proba, "Random Forest (Threshold 0.3)")
    
    joblib.dump(rf, MODELS_DIR / "random_forest_model.pkl")
    logger.info("✅ Modelo Random Forest guardado en models_saved/")
    
    return rf, metrics


def train_xgboost(X_train, y_train, X_test, y_test):
    logger.info("\n[2/4] Entrenando XGBoost (Sección 3.3.2 / 5.5.1)...")
    xgb_model = xgb.XGBClassifier(
        n_estimators=100,
        learning_rate=0.1,
        max_depth=5,
        random_state=42,
        n_jobs=-1,
        eval_metric='auc'
    )
    xgb_model.fit(X_train, y_train)
    
    y_pred_proba = xgb_model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    metrics = evaluate_model(y_test, y_pred, y_pred_proba, "XGBoost")
    
    joblib.dump(xgb_model, MODELS_DIR / "xgboost_model.pkl")
    logger.info("✅ Modelo XGBoost guardado en models_saved/")
    
    return xgb_model, metrics


def train_svm(X_train, y_train, X_test, y_test):
    logger.info("\n[3/4] Entrenando SVM (Optimizado con LinearSVC + Calibración)...")
    
    # LinearSVC es mucho más rápido para datasets grandes que SVC(kernel='linear')
    base_svm = LinearSVC(
        class_weight='balanced', 
        random_state=42, 
        max_iter=2000, 
        dual='auto'
    )
    
    # CalibratedClassifierCV nos da las probabilidades (predict_proba) mediante Platt Scaling
    # Usamos cv=3 para mantener rigor metodológico pero con LinearSVC es rapidísimo.
    svm_model = CalibratedClassifierCV(base_svm, cv=3, method='sigmoid')
    
    logger.info("Entrenando SVM (esto tomará menos de 1 minuto con la optimización)...")
    svm_model.fit(X_train, y_train)
    
    y_pred_proba = svm_model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    metrics = evaluate_model(y_test, y_pred, y_pred_proba, "SVM (Linear Optimizado)")
    
    joblib.dump(svm_model, MODELS_DIR / "svm_model.pkl")
    logger.info("✅ Modelo SVM guardado en models_saved/")
    
    return svm_model, metrics


def train_dnn(X_train, y_train, X_test, y_test):
    logger.info("\n[4/4] Entrenando Red Neuronal Profunda (DNN) (Sección 3.2 / 5.5.2)...")
    
    # Arquitectura según Sección 3.2 del documento
    model = Sequential([
        Dense(256, activation='relu', input_shape=(X_train.shape[1],)),
        BatchNormalization(),
        Dropout(0.4),
        
        Dense(128, activation='relu'),
        BatchNormalization(),
        Dropout(0.4),
        
        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.4),
        
        Dense(1, activation='sigmoid')
    ])
    
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy', tf.keras.metrics.AUC(name='auc'), tf.keras.metrics.Recall(name='recall')]
    )
    
    # Early Stopping para evitar sobreajuste (Sección 3.2)
    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=5,
        restore_best_weights=True,
        verbose=1
    )
    
    # Entrenamiento
    logger.info("Iniciando entrenamiento de DNN...")
    history = model.fit(
        X_train, y_train,
        validation_split=0.1, # 10% del train para validación
        epochs=50,
        batch_size=256, # Optimizado para 16GB RAM
        callbacks=[early_stopping],
        verbose=1
    )
    
    # Evaluación
    y_pred_proba = model.predict(X_test, verbose=0).flatten()
    y_pred = (y_pred_proba >= 0.5).astype(int)
    
    metrics = evaluate_model(y_test, y_pred, y_pred_proba, "DNN (TensorFlow/Keras)")
    
    # Guardar modelo
    model.save(MODELS_DIR / "dnn_model.keras")
    logger.info("✅ Modelo DNN guardado en models_saved/")
    
    return model, metrics


def main():
    logger.info("=" * 80)
    logger.info("INICIANDO FASE 4: MODELADO (CRISP-DM)")
    logger.info("=" * 80)
    
    # 1. Cargar datos
    X_train, y_train, X_test, y_test = load_data_from_db()
    
    # 2. Entrenar y evaluar modelos
    results = []
    
    _, rf_metrics = train_random_forest(X_train, y_train, X_test, y_test)
    results.append(rf_metrics)
    
    _, xgb_metrics = train_xgboost(X_train, y_train, X_test, y_test)
    results.append(xgb_metrics)
    
    _, svm_metrics = train_svm(X_train, y_train, X_test, y_test)
    results.append(svm_metrics)
    
    _, dnn_metrics = train_dnn(X_train, y_train, X_test, y_test)
    results.append(dnn_metrics)
    
    # 3. Resumen de resultados
    logger.info("\n" + "=" * 80)
    logger.info("RESUMEN DE DESEMPEÑO DE MODELOS (Conjunto de Prueba)")
    logger.info("=" * 80)
    
    results_df = pd.DataFrame(results)
    logger.info("\n" + results_df.to_string(index=False))
    
    # Guardar resumen en CSV para el reporte
    results_df.to_csv(MODELS_DIR / "model_evaluation_summary.csv", index=False)
    logger.info(f"\n✅ Resumen guardado en: {MODELS_DIR / 'model_evaluation_summary.csv'}")
    
    logger.info("\n" + "=" * 80)
    logger.info("FASE 4: MODELADO COMPLETADA EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info("Próximos pasos:")
    logger.info("    Ejecutar: python scripts/05_ensemble.py (Técnica de Ensamble)")


if __name__ == "__main__":
    # Suprimir warnings informativos de TensorFlow para una salida más limpia
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    main()