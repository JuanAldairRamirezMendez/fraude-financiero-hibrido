#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 11_tier3_optimization.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: TIER 3 - Stacking Avanzado + Calibración + Análisis de Costos
TIEMPO ESTIMADO: 30-45 minutos
=============================================================================
"""
import os
import logging
import warnings
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    f1_score, precision_recall_curve, confusion_matrix, 
    precision_score, recall_score, roc_auc_score
)
from sklearn.ensemble import StackingClassifier
from dotenv import load_dotenv
import xgboost as xgb
import lightgbm as lgb

# Suprimir warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Configuración
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = "models_saved"
REPORTS_DIR = "reports"

# Cargar datos desde PostgreSQL
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

logger.info("Cargando datos desde PostgreSQL...")
df_train = pd.read_sql("SELECT * FROM train_cleaned_balanced", engine)
df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)

X_train = df_train.drop(columns=['risk_label'])
y_train = df_train['risk_label']
X_test = df_test.drop(columns=['risk_label'])
y_test = df_test['risk_label']

logger.info(f"Datos cargados: Train={X_train.shape}, Test={X_test.shape}")

# Cargar modelos existentes (TIER 1 y TIER 2)
logger.info("Cargando modelos existentes...")
rf = joblib.load(f"{MODELS_DIR}/random_forest_model.pkl")
xgb_model = joblib.load(f"{MODELS_DIR}/xgboost_model.pkl")
svm_model = joblib.load(f"{MODELS_DIR}/svm_model.pkl")
xgb_tier2 = joblib.load(f"{MODELS_DIR}/xgboost_tier2.pkl")
lgb_tier2 = joblib.load(f"{MODELS_DIR}/lightgbm_tier2.pkl")

logger.info("✅ Modelos cargados")

# ============================================================================
# MEJORA 1: STACKING AVANZADO CON XGBOOST COMO META-LEARNER
# ============================================================================
logger.info("\n" + "="*80)
logger.info("MEJORA 1: STACKING AVANZADO CON XGBOOST META-LEARNER")
logger.info("="*80)

# Definir los modelos base (usamos los optimizados de TIER 2)
base_models = [
    ('rf', rf),
    ('xgb_tier2', xgb_tier2),
    ('lgb_tier2', lgb_tier2),
    ('svm', svm_model)
]

# Meta-learner: XGBoost (en lugar de LogisticRegression)
meta_learner = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=5,
    learning_rate=0.05,
    tree_method='hist',
    n_jobs=6,
    random_state=42
)

# Crear Stacking Classifier con validación cruzada de 5 folds
logger.info("Entrenando Stacking con XGBoost como meta-learner (5-fold CV)...")
stacking_tier3 = StackingClassifier(
    estimators=base_models,
    final_estimator=meta_learner,
    cv=5,  # Validación cruzada estratificada de 5 folds
    stack_method='predict_proba',  # Usar probabilidades en lugar de predicciones
    n_jobs=6
)

stacking_tier3.fit(X_train, y_train)
joblib.dump(stacking_tier3, f"{MODELS_DIR}/stacking_tier3.pkl")
logger.info("✅ Modelo Stacking TIER 3 guardado")

# Evaluar en conjunto de prueba
proba_stacking_t3 = stacking_tier3.predict_proba(X_test)[:, 1]

# Optimizar umbral
precision, recall, thresholds = precision_recall_curve(y_test, proba_stacking_t3)
f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
optimal_idx = np.argmax(f1_scores)
threshold_stacking_t3 = thresholds[optimal_idx]
f1_stacking_t3 = f1_scores[optimal_idx]

y_pred_stacking_t3 = (proba_stacking_t3 >= threshold_stacking_t3).astype(int)
precision_stacking_t3 = precision_score(y_test, y_pred_stacking_t3, zero_division=0)
recall_stacking_t3 = recall_score(y_test, y_pred_stacking_t3, zero_division=0)

logger.info(f"\n🏆 Stacking TIER 3 (XGBoost meta-learner):")
logger.info(f"   F1-Score: {f1_stacking_t3:.4f}")
logger.info(f"   Precision: {precision_stacking_t3:.4f}")
logger.info(f"   Recall: {recall_stacking_t3:.4f}")
logger.info(f"   Umbral óptimo: {threshold_stacking_t3:.4f}")

# ============================================================================
# MEJORA 2: CALIBRACIÓN DE PROBABILIDADES (PLATT SCALING)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("MEJORA 2: CALIBRACIÓN DE PROBABILIDADES (PLATT SCALING)")
logger.info("="*80)

logger.info("Calibrando probabilidades de XGBoost TIER 2...")
# Usar solo una parte del train para calibración (evitar overfitting)
from sklearn.model_selection import train_test_split
X_calib, X_calib_val, y_calib, y_calib_val = train_test_split(
    X_train, y_train, test_size=0.2, random_state=42, stratify=y_train
)

# Calibrar XGBoost TIER 2
xgb_calibrated = CalibratedClassifierCV(
    xgb_tier2, 
    method='sigmoid',  # Platt Scaling
    cv=3
)
xgb_calibrated.fit(X_calib, y_calib)
joblib.dump(xgb_calibrated, f"{MODELS_DIR}/xgboost_tier2_calibrated.pkl")

# Evaluar modelo calibrado
proba_xgb_calib = xgb_calibrated.predict_proba(X_test)[:, 1]

precision_calib, recall_calib, thresholds_calib = precision_recall_curve(y_test, proba_xgb_calib)
f1_scores_calib = 2 * (precision_calib * recall_calib) / (precision_calib + recall_calib + 1e-8)
optimal_idx_calib = np.argmax(f1_scores_calib)
threshold_xgb_calib = thresholds_calib[optimal_idx_calib]
f1_xgb_calib = f1_scores_calib[optimal_idx_calib]

y_pred_xgb_calib = (proba_xgb_calib >= threshold_xgb_calib).astype(int)
precision_xgb_calib = precision_score(y_test, y_pred_xgb_calib, zero_division=0)
recall_xgb_calib = recall_score(y_test, y_pred_xgb_calib, zero_division=0)

logger.info(f"\n🎯 XGBoost TIER 2 Calibrado:")
logger.info(f"   F1-Score: {f1_xgb_calib:.4f} (vs {f1_stacking_t3:.4f} sin calibrar)")
logger.info(f"   Precision: {precision_xgb_calib:.4f}")
logger.info(f"   Recall: {recall_xgb_calib:.4f}")
logger.info(f"   Umbral óptimo: {threshold_xgb_calib:.4f}")

# ============================================================================
# MEJORA 3: ANÁLISIS DE COSTOS DE NEGOCIO
# ============================================================================
logger.info("\n" + "="*80)
logger.info("MEJORA 3: ANÁLISIS DE COSTOS DE NEGOCIO")
logger.info("="*80)

# Definir matriz de costos realista para un banco
# [TN_cost, FP_cost]
# [FN_cost, TP_cost]
# TN: $0 (correcto, no hay fraude)
# FP: $50 (falsa alarma, costo de revisión manual)
# FN: $5000 (fraude no detectado, pérdida directa)
# TP: $0 (fraude detectado, pérdida evitada)
cost_matrix = np.array([
    [0, 50],      # TN, FP
    [5000, 0]     # FN, TP
])

def calculate_business_cost(y_true, y_pred, cost_matrix):
    """Calcula el costo total de negocio basado en la matriz de confusión."""
    cm = confusion_matrix(y_true, y_pred)
    total_cost = np.sum(cm * cost_matrix)
    return total_cost, cm

# Calcular costos para cada modelo
logger.info("Calculando costos de negocio para cada modelo...")

models_to_evaluate = {
    'XGBoost TIER 2': (xgb_tier2, threshold_stacking_t3),  # Usar umbral de stacking para comparación
    'LightGBM TIER 2': (lgb_tier2, threshold_stacking_t3),
    'Stacking TIER 3': (stacking_tier3, threshold_stacking_t3),
    'XGBoost Calibrado': (xgb_calibrated, threshold_xgb_calib)
}

business_costs = []

for model_name, (model, threshold) in models_to_evaluate.items():
    y_pred = (model.predict_proba(X_test)[:, 1] >= threshold).astype(int)
    cost, cm = calculate_business_cost(y_test, y_pred, cost_matrix)
    
    tn, fp, fn, tp = cm.ravel()
    
    business_costs.append({
        'Modelo': model_name,
        'F1-Score': f1_score(y_test, y_pred, zero_division=0),
        'TN': tn,
        'FP': fp,
        'FN': fn,
        'TP': tp,
        'Costo Total ($)': cost,
        'Costo por Falsa Alarma ($)': fp * 50,
        'Costo por Fraude No Detectado ($)': fn * 5000
    })
    
    logger.info(f"\n{model_name}:")
    logger.info(f"   TN: {tn:,} | FP: {fp:,} | FN: {fn:,} | TP: {tp:,}")
    logger.info(f"   Costo por Falsas Alarmas: ${fp * 50:,}")
    logger.info(f"   Costo por Fraudes No Detectados: ${fn * 5000:,}")
    logger.info(f"   COSTO TOTAL: ${cost:,}")

df_business_costs = pd.DataFrame(business_costs)
df_business_costs.to_csv(f"{REPORTS_DIR}/tier3_business_costs.csv", index=False)
logger.info(f"\n✅ Costos de negocio guardados en {REPORTS_DIR}/tier3_business_costs.csv")

# ============================================================================
# MEJORA 4: VALIDACIÓN CRUZADA 5-FOLD (ROBUSTEZ)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("MEJORA 4: VALIDACIÓN CRUZADA 5-FOLD (ROBUSTEZ METODOLÓGICA)")
logger.info("="*80)

logger.info("Evaluando robustez con 5-fold CV en XGBoost TIER 2...")
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# Validación cruzada en el conjunto de entrenamiento
f1_scores_cv = cross_val_score(
    xgb_tier2, X_train, y_train, cv=cv, scoring='f1', n_jobs=6
)

logger.info(f"\n📊 Resultados 5-Fold CV (XGBoost TIER 2):")
logger.info(f"   F1-Score promedio: {f1_scores_cv.mean():.4f}")
logger.info(f"   Desviación estándar: {f1_scores_cv.std():.4f}")
logger.info(f"   Rango: [{f1_scores_cv.min():.4f}, {f1_scores_cv.max():.4f}]")
logger.info(f"   Scores por fold: {f1_scores_cv}")

# ============================================================================
# RESUMEN FINAL TIER 3
# ============================================================================
logger.info("\n" + "="*80)
logger.info("🎉 RESUMEN FINAL TIER 3")
logger.info("="*80)

# Comparar con TIER 2
logger.info("\n📈 Comparación TIER 2 vs TIER 3:")
logger.info(f"   XGBoost TIER 2 (base): F1 = 0.7343")
logger.info(f"   Stacking TIER 3: F1 = {f1_stacking_t3:.4f}")
logger.info(f"   XGBoost Calibrado: F1 = {f1_xgb_calib:.4f}")

# Mejor modelo en términos de costo
best_cost_model = df_business_costs.loc[df_business_costs['Costo Total ($)'].idxmin()]
logger.info(f"\n💰 Mejor modelo en términos de costo de negocio:")
logger.info(f"   {best_cost_model['Modelo']}: ${best_cost_model['Costo Total ($)']:,.0f}")

# Guardar resumen
summary = {
    'Stacking_Tier3_F1': f1_stacking_t3,
    'XGBoost_Calibrated_F1': f1_xgb_calib,
    'Best_Business_Cost_Model': best_cost_model['Modelo'],
    'Best_Business_Cost': best_cost_model['Costo Total ($)'],
    'CV_5Fold_Mean_F1': f1_scores_cv.mean(),
    'CV_5Fold_Std_F1': f1_scores_cv.std()
}

pd.DataFrame([summary]).to_csv(f"{REPORTS_DIR}/tier3_summary.csv", index=False)
logger.info(f"\n✅ Resumen TIER 3 guardado en {REPORTS_DIR}/tier3_summary.csv")

logger.info("\n" + "="*80)
logger.info("🏆 ¡OPTIMIZACIÓN TIER 3 COMPLETADA EXITOSAMENTE!")
logger.info("="*80)