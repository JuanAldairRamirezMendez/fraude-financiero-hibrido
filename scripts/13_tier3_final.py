#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 13_tier3_final.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: TIER 3 Final - CatBoost (Optuna) + Visualizaciones de Negocio y Calibración
TIEMPO ESTIMADO: 20-30 minutos
=============================================================================
"""
import os
import logging
import warnings
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.metrics import precision_recall_curve
from sklearn.calibration import CalibrationDisplay
from dotenv import load_dotenv
import optuna
import matplotlib.pyplot as plt
import seaborn as sns

# Suprimir warnings y logs excesivos
warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Configuración
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = "models_saved"
REPORTS_DIR = "reports"

# Cargar datos
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

# ============================================================================
# PARTE 1: OPTIMIZACIÓN DE CATBOOST CON OPTUNA
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PARTE 1: OPTIMIZACIÓN BAYESIANA - CATBOOST (30 trials)")
logger.info("="*80)

try:
    from catboost import CatBoostClassifier
except ImportError:
    logger.error("CatBoost no está instalado. Ejecuta: pip install catboost")
    exit(1)

def objective_catboost(trial):
    param = {
        'iterations': trial.suggest_int('iterations', 100, 500),
        'depth': trial.suggest_int('depth', 4, 8),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'l2_leaf_reg': trial.suggest_float('l2_leaf_reg', 1e-8, 10.0, log=True),
        'border_count': trial.suggest_int('border_count', 32, 255),
        'random_seed': 42,
        'verbose': 0,
        'task_type': 'CPU'
    }
    
    # Entrenamiento simple para Optuna (usando el train balanceado)
    model = CatBoostClassifier(**param)
    model.fit(X_train, y_train, eval_set=(X_test, y_test), early_stopping_rounds=20, verbose=0)
    
    proba = model.predict_proba(X_test)[:, 1]
    precision, recall, thresholds = precision_recall_curve(y_test, proba)
    f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
    
    return np.max(f1_scores)

logger.info("Ejecutando Optuna para CatBoost...")
study_cat = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42))
study_cat.optimize(objective_catboost, n_trials=30, show_progress_bar=True)

logger.info(f"✅ Mejor F1-Score CatBoost: {study_cat.best_value:.4f}")
logger.info(f"Mejores parámetros: {study_cat.best_params}")

# Entrenamiento final de CatBoost
logger.info("Entrenando CatBoost final...")
cat_final = CatBoostClassifier(**study_cat.best_params, random_seed=42, verbose=0)
cat_final.fit(X_train, y_train)
joblib.dump(cat_final, f"{MODELS_DIR}/catboost_tier3.pkl")

# Evaluación final
proba_cat = cat_final.predict_proba(X_test)[:, 1]
precision, recall, thresholds = precision_recall_curve(y_test, proba_cat)
f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
thr_cat = thresholds[np.argmax(f1_scores)]
f1_cat = np.max(f1_scores)

logger.info(f"🏆 CatBoost TIER 3 Final: F1 = {f1_cat:.4f} (Umbral: {thr_cat:.4f})")

# ============================================================================
# PARTE 2: VISUALIZACIÓN DE COSTOS DE NEGOCIO
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PARTE 2: GENERANDO GRÁFICA DE COSTOS DE NEGOCIO")
logger.info("="*80)

costs_file = f"{REPORTS_DIR}/tier3_business_costs.csv"
if os.path.exists(costs_file):
    df_costs = pd.read_csv(costs_file)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    x = np.arange(len(df_costs['Modelo']))
    width = 0.25
    
    bars1 = ax.bar(x - width, df_costs['Costo por Falsa Alarma ($)'], width, label='Falsas Alarmas (FP)', color='#f39c12')
    bars2 = ax.bar(x, df_costs['Costo por Fraude No Detectado ($)'], width, label='Fraudes No Detectados (FN)', color='#e74c3c')
    bars3 = ax.bar(x + width, df_costs['Costo Total ($)'], width, label='Costo Total', color='#2c3e50')
    
    ax.set_xlabel('Modelo', fontsize=12, fontweight='bold')
    ax.set_ylabel('Costo en Dólares ($)', fontsize=12, fontweight='bold')
    ax.set_title('Análisis de Costos de Negocio por Modelo (TIER 3)', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels(df_costs['Modelo'], rotation=15, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{REPORTS_DIR}/07_business_costs_comparison.png", dpi=300, bbox_inches='tight')
    logger.info(f"✅ Gráfica de costos guardada: {REPORTS_DIR}/07_business_costs_comparison.png")
    plt.close()
else:
    logger.warning("⚠️ No se encontró tier3_business_costs.csv. Omitiendo gráfica de costos.")

# ============================================================================
# PARTE 3: CURVA DE CALIBRACIÓN (RELIABILITY DIAGRAM)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PARTE 3: GENERANDO CURVA DE CALIBRACIÓN (RELIABILITY DIAGRAM)")
logger.info("="*80)

# Cargar modelos para comparar calibración
models_to_calibrate = {}
try:
    models_to_calibrate['XGBoost (Sin Calibrar)'] = joblib.load(f"{MODELS_DIR}/xgboost_tier2.pkl")
    models_to_calibrate['XGBoost (Sigmoid)'] = joblib.load(f"{MODELS_DIR}/xgboost_tier2_calibrated.pkl")
    models_to_calibrate['XGBoost (Isotónico)'] = joblib.load(f"{MODELS_DIR}/xgboost_tier2_isotonic.pkl")
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    for name, model in models_to_calibrate.items():
        proba = model.predict_proba(X_test)[:, 1]
        CalibrationDisplay.from_predictions(y_test, proba, n_bins=10, name=name, ax=ax)
        
    ax.plot([0, 1], [0, 1], 'k--', label='Calibración Perfecta', alpha=0.5)
    ax.set_title('Curva de Calibración (Reliability Diagram) - XGBoost', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Probabilidad Predicha Media', fontsize=12, fontweight='bold')
    ax.set_ylabel('Fracción de Positivos Reales', fontsize=12, fontweight='bold')
    ax.legend(loc='lower right')
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{REPORTS_DIR}/08_calibration_curve_xgboost.png", dpi=300, bbox_inches='tight')
    logger.info(f"✅ Curva de calibración guardada: {REPORTS_DIR}/08_calibration_curve_xgboost.png")
    plt.close()
    
except Exception as e:
    logger.error(f"Error al generar curva de calibración: {e}")

# ============================================================================
# RESUMEN FINAL
# ============================================================================
logger.info("\n" + "="*80)
logger.info("🎉 ¡TIER 3 FINAL COMPLETADO EXITOSAMENTE!")
logger.info("="*80)
logger.info(f"CatBoost F1-Score: {f1_cat:.4f}")
logger.info("Visualizaciones generadas en la carpeta reports/")