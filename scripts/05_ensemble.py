#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 05_ensemble.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
METODOLOGÍA: CRISP-DM - Fase 5 (Evaluación de Técnicas de Ensamble)
AUTOR: Ramirez Mendez, Juan Aldair
FECHA: 2026
=============================================================================
DESCRIPCIÓN:
    Implementa las técnicas de ensamble (Voting y Stacking) descritas en 
    las Secciones 3.4.1, 3.4.2 y 5.5.3 del documento. Combina las predicciones
    de los modelos base (RF, XGBoost, SVM, DNN) para mejorar la robustez 
    y el desempeño final del sistema.
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score

# TensorFlow / Keras
import tensorflow as tf

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
        logging.FileHandler(LOG_DIR / "ensemble.log", encoding="utf-8"),
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
    logger.info("Conectando a PostgreSQL para cargar los datos de ensamble...")
    engine = create_engine(DATABASE_URL)
    
    df_train = pd.read_sql("SELECT * FROM train_cleaned_balanced", engine)
    df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)
    
    X_train = df_train.drop(columns=['risk_label'])
    y_train = df_train['risk_label']
    X_test = df_test.drop(columns=['risk_label'])
    y_test = df_test['risk_label']
    
    logger.info(f"Datos cargados. Train: {X_train.shape}, Test: {X_test.shape}")
    return X_train, y_train, X_test, y_test


def load_base_models():
    """Carga los modelos previamente entrenados y guardados."""
    logger.info("Cargando modelos base desde disco...")
    
    rf = joblib.load(MODELS_DIR / "random_forest_model.pkl")
    xgb_model = joblib.load(MODELS_DIR / "xgboost_model.pkl")
    svm_model = joblib.load(MODELS_DIR / "svm_model.pkl")
    
    # Suprimir warnings de TensorFlow al cargar
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    dnn_model = tf.keras.models.load_model(MODELS_DIR / "dnn_model.keras")
    
    logger.info("✅ Todos los modelos base cargados exitosamente.")
    return rf, xgb_model, svm_model, dnn_model


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


# =========================================================================
# TÉCNICAS DE ENSAMBLE (Sección 5.5.3)
# =========================================================================

def soft_voting_ensemble(X_test, y_test, rf, xgb_model, svm_model, dnn_model):
    """
    Implementa Voting Classifier (Promedio de probabilidades) - Sección 3.4.1
    """
    logger.info("\n[1/2] Evaluando Ensamble por Votación (Soft Voting)...")
    
    # Obtener probabilidades de la clase positiva (fraude) de cada modelo
    proba_rf = rf.predict_proba(X_test)[:, 1]
    proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
    proba_svm = svm_model.predict_proba(X_test)[:, 1]
    proba_dnn = dnn_model.predict(X_test, verbose=0).flatten()
    
    # Promedio de probabilidades (Soft Voting)
    ensemble_proba = (proba_rf + proba_xgb + proba_svm + proba_dnn) / 4.0
    
    # Umbral de 0.5 para la decisión final (puede optimizarse, pero 0.5 es estándar para ensambles)
    ensemble_pred = (ensemble_proba >= 0.5).astype(int)
    
    metrics = evaluate_model(y_test, ensemble_pred, ensemble_proba, "Ensamble Soft Voting")
    return metrics


def stacking_ensemble(X_train, y_train, X_test, y_test, rf, xgb_model, svm_model, dnn_model):
    """
    Implementa Stacking con Meta-Learner (Regresión Logística) - Sección 3.4.2
    """
    logger.info("\n[2/2] Entrenando y Evaluando Ensamble por Stacking (Meta-Learner)...")
    
    # PASO 1: Obtener predicciones de los modelos base en el conjunto de ENTRENAMIENTO
    logger.info("   Generando meta-características para el conjunto de entrenamiento...")
    proba_rf_train = rf.predict_proba(X_train)[:, 1].reshape(-1, 1)
    proba_xgb_train = xgb_model.predict_proba(X_train)[:, 1].reshape(-1, 1)
    proba_svm_train = svm_model.predict_proba(X_train)[:, 1].reshape(-1, 1)
    proba_dnn_train = dnn_model.predict(X_train, verbose=0).reshape(-1, 1)
    
    # Combinar en un solo DataFrame de meta-características
    X_train_meta = np.hstack([proba_rf_train, proba_xgb_train, proba_svm_train, proba_dnn_train])
    
    # PASO 2: Entrenar el Meta-Modelo (Regresión Logística)
    logger.info("   Entrenando Meta-Modelo (Regresión Logística)...")
    meta_model = LogisticRegression(random_state=42, class_weight='balanced')
    meta_model.fit(X_train_meta, y_train)
    
    # PASO 3: Obtener predicciones de los modelos base en el conjunto de PRUEBA
    logger.info("   Generando meta-características para el conjunto de prueba...")
    proba_rf_test = rf.predict_proba(X_test)[:, 1].reshape(-1, 1)
    proba_xgb_test = xgb_model.predict_proba(X_test)[:, 1].reshape(-1, 1)
    proba_svm_test = svm_model.predict_proba(X_test)[:, 1].reshape(-1, 1)
    proba_dnn_test = dnn_model.predict(X_test, verbose=0).reshape(-1, 1)
    
    X_test_meta = np.hstack([proba_rf_test, proba_xgb_test, proba_svm_test, proba_dnn_test])
    
    # PASO 4: Predicción final del Meta-Modelo
    ensemble_pred = meta_model.predict(X_test_meta)
    ensemble_proba = meta_model.predict_proba(X_test_meta)[:, 1]
    
    metrics = evaluate_model(y_test, ensemble_pred, ensemble_proba, "Ensamble Stacking (Logistic Regression)")
    
    # Guardar el meta-modelo
    joblib.dump(meta_model, MODELS_DIR / "stacking_meta_model.pkl")
    logger.info("   ✅ Meta-modelo de Stacking guardado en models_saved/")
    
    return metrics


def main():
    logger.info("=" * 80)
    logger.info("INICIANDO FASE 5: TÉCNICAS DE ENSAMBLE (CRISP-DM)")
    logger.info("=" * 80)
    
    # 1. Cargar datos
    X_train, y_train, X_test, y_test = load_data_from_db()
    
    # 2. Cargar modelos base
    rf, xgb_model, svm_model, dnn_model = load_base_models()
    
    # 3. Ejecutar técnicas de ensamble
    results = []
    
    voting_metrics = soft_voting_ensemble(X_test, y_test, rf, xgb_model, svm_model, dnn_model)
    results.append(voting_metrics)
    
    stacking_metrics = stacking_ensemble(X_train, y_train, X_test, y_test, rf, xgb_model, svm_model, dnn_model)
    results.append(stacking_metrics)
    
    # 4. Resumen final comparativo
    logger.info("\n" + "=" * 80)
    logger.info("RESUMEN FINAL: COMPARACIÓN DE MODELOS Y ENSAMBLES")
    logger.info("=" * 80)
    
    # Cargar resultados previos de modelos individuales para comparación
    individual_results_path = MODELS_DIR / "model_evaluation_summary.csv"
    if individual_results_path.exists():
        df_individual = pd.read_csv(individual_results_path)
        df_ensemble = pd.DataFrame(results)
        df_final = pd.concat([df_individual, df_ensemble], ignore_index=True)
    else:
        df_final = pd.DataFrame(results)
    
    logger.info("\n" + df_final.to_string(index=False))
    
    # Guardar resumen final
    df_final.to_csv(MODELS_DIR / "final_model_comparison.csv", index=False)
    logger.info(f"\n✅ Comparación final guardada en: {MODELS_DIR / 'final_model_comparison.csv'}")
    
    logger.info("\n" + "=" * 80)
    logger.info("FASE 5: EVALUACIÓN DE ENSAMBLES COMPLETADA EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info("🎉 ¡Felicidades! Has completado el pipeline de Machine Learning.")
    logger.info("Próximos pasos sugeridos:")
    logger.info("    1. Revisar 'models_saved/final_model_comparison.csv'")
    logger.info("    2. (Opcional) Ejecutar scripts de interpretabilidad (SHAP/LIME)")
    logger.info("    3. Redactar la Sección 6 (Resultados y Discusión) de tu tesis")


if __name__ == "__main__":
    main()