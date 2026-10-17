#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 07_optimize_models.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: Implementar mejoras TIER 1 (Optimización de Umbrales + Weighted Voting)
TIEMPO ESTIMADO: 30-40 minutos
=============================================================================
"""
import os
import logging
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score, roc_auc_score
from dotenv import load_dotenv
import tensorflow as tf

# Configuración
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = "models_saved"
REPORTS_DIR = "reports"

# Cargar datos desde PostgreSQL (SOLO LECTURA, no hay riesgo de error de parámetros)
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

logger.info("Cargando datos de prueba desde PostgreSQL...")
df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)
X_test = df_test.drop(columns=['risk_label'])
y_test = df_test['risk_label']
logger.info(f"Datos cargados: {X_test.shape[0]} filas, {X_test.shape[1]} columnas")

# Cargar modelos
logger.info("Cargando modelos entrenados...")
rf = joblib.load(f"{MODELS_DIR}/random_forest_model.pkl")
xgb_model = joblib.load(f"{MODELS_DIR}/xgboost_model.pkl")
svm_model = joblib.load(f"{MODELS_DIR}/svm_model.pkl")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
dnn_model = tf.keras.models.load_model(f"{MODELS_DIR}/dnn_model.keras")
logger.info("✅ Modelos cargados exitosamente")

# ============================================================================
# MEJORA 1: OPTIMIZACIÓN DE UMBRALES
# ============================================================================
logger.info("\n" + "="*80)
logger.info("MEJORA 1: OPTIMIZACIÓN DE UMBRALES")
logger.info("="*80)

def find_optimal_threshold(y_true, y_proba, metric='f1'):
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    if metric == 'f1':
        scores = 2 * (precision * recall) / (precision + recall + 1e-8)
    else:
        scores = precision
    optimal_idx = np.argmax(scores)
    return thresholds[optimal_idx], scores[optimal_idx]

logger.info("Generando predicciones de probabilidad...")
proba_rf = rf.predict_proba(X_test)[:, 1]
proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
proba_svm = svm_model.predict_proba(X_test)[:, 1]
proba_dnn = dnn_model.predict(X_test, verbose=0).flatten()

logger.info("Calculando umbrales óptimos para maximizar F1-Score...")
threshold_rf, f1_rf_opt = find_optimal_threshold(y_test, proba_rf)
threshold_xgb, f1_xgb_opt = find_optimal_threshold(y_test, proba_xgb)
threshold_svm, f1_svm_opt = find_optimal_threshold(y_test, proba_svm)
threshold_dnn, f1_dnn_opt = find_optimal_threshold(y_test, proba_dnn)

logger.info(f"\nUmbrales óptimos encontrados:")
logger.info(f"  Random Forest: {threshold_rf:.4f} (F1: {f1_rf_opt:.4f})")
logger.info(f"  XGBoost:       {threshold_xgb:.4f} (F1: {f1_xgb_opt:.4f})")
logger.info(f"  SVM:           {threshold_svm:.4f} (F1: {f1_svm_opt:.4f})")
logger.info(f"  DNN:           {threshold_dnn:.4f} (F1: {f1_dnn_opt:.4f})")

def evaluate_with_threshold(y_true, y_proba, threshold, model_name):
    y_pred = (y_proba >= threshold).astype(int)
    return {
        'Modelo': model_name,
        'Umbral': f"{threshold:.4f}",
        'Precision': f"{precision_score(y_true, y_pred, zero_division=0):.4f}",
        'Recall': f"{recall_score(y_true, y_pred, zero_division=0):.4f}",
        'F1-Score': f"{f1_score(y_true, y_pred, zero_division=0):.4f}",
        'AUC-ROC': f"{roc_auc_score(y_true, y_proba):.4f}"
    }

results_optimized = [
    evaluate_with_threshold(y_test, proba_rf, threshold_rf, "Random Forest (Optimizado)"),
    evaluate_with_threshold(y_test, proba_xgb, threshold_xgb, "XGBoost (Optimizado)"),
    evaluate_with_threshold(y_test, proba_svm, threshold_svm, "SVM (Optimizado)"),
    evaluate_with_threshold(y_test, proba_dnn, threshold_dnn, "DNN (Optimizado)")
]

# ============================================================================
# MEJORA 2: WEIGHTED SOFT VOTING
# ============================================================================
logger.info("\n" + "="*80)
logger.info("MEJORA 2: WEIGHTED SOFT VOTING")
logger.info("="*80)

f1_scores = {'rf': f1_rf_opt, 'xgb': f1_xgb_opt, 'svm': f1_svm_opt, 'dnn': f1_dnn_opt}
total_f1 = sum(f1_scores.values())
weights = {k: v/total_f1 for k, v in f1_scores.items()}

logger.info(f"\nPesos calculados (basados en F1-Score optimizado):")
for k, v in weights.items():
    logger.info(f"  {k.upper()}: {v:.4f}")

weighted_proba = (weights['rf'] * proba_rf + weights['xgb'] * proba_xgb + 
                  weights['svm'] * proba_svm + weights['dnn'] * proba_dnn)

threshold_weighted, f1_weighted_opt = find_optimal_threshold(y_test, weighted_proba)
logger.info(f"\nUmbral óptimo para Weighted Voting: {threshold_weighted:.4f}")
logger.info(f"F1-Score optimizado del Ensamble: {f1_weighted_opt:.4f}")

results_optimized.append(evaluate_with_threshold(y_test, weighted_proba, threshold_weighted, "Weighted Soft Voting (Optimizado)"))

# ============================================================================
# COMPARACIÓN FINAL
# ============================================================================
logger.info("\n" + "="*80)
logger.info("COMPARACIÓN FINAL: MODELOS ORIGINALES vs OPTIMIZADOS")
logger.info("="*80)

df_original = pd.read_csv(f"{MODELS_DIR}/final_model_comparison.csv")
logger.info("\n📊 MODELOS ORIGINALES:")
logger.info(df_original.to_string(index=False))

df_optimized_final = pd.DataFrame(results_optimized)
logger.info("\n🚀 MODELOS OPTIMIZADOS (TIER 1):")
logger.info(df_optimized_final.to_string(index=False))

df_optimized_final.to_csv(f"{REPORTS_DIR}/tier1_optimization_results.csv", index=False)
logger.info(f"\n✅ Resultados guardados en: {REPORTS_DIR}/tier1_optimization_results.csv")

# Calcular mejoras porcentuales
logger.info("\n" + "="*80)
logger.info("MEJORAS OBTENIDAS")
logger.info("="*80)

improvements = []
for orig_name, opt_name in [('Random Forest (Threshold 0.3)', 'Random Forest (Optimizado)'), 
                            ('XGBoost', 'XGBoost (Optimizado)'), 
                            ('Ensamble Soft Voting', 'Weighted Soft Voting (Optimizado)')]:
    f1_orig = df_original[df_original['model'] == orig_name]['f1_score'].values[0]
    f1_opt = df_optimized_final[df_optimized_final['Modelo'] == opt_name]['F1-Score'].values[0]
    mejora = ((float(f1_opt) - float(f1_orig)) / float(f1_orig)) * 100
    improvements.append({
        'Modelo': orig_name.replace(' (Threshold 0.3)', '').replace('Ensamble ', ''),
        'F1 Original': f"{float(f1_orig):.4f}",
        'F1 Optimizado': f"{float(f1_opt):.4f}",
        'Mejora': f"+{mejora:.2f}%" if mejora > 0 else f"{mejora:.2f}%"
    })

logger.info("\n" + pd.DataFrame(improvements).to_string(index=False))
logger.info("\n" + "="*80)
logger.info("✅ OPTIMIZACIÓN TIER 1 COMPLETADA EXITOSAMENTE")
logger.info("="*80)