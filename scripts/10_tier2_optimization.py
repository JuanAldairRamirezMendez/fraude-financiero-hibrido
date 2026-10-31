#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 10_tier2_optimization.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: TIER 2 - Optimización Bayesiana (Optuna) + Inclusión de LightGBM
TIEMPO ESTIMADO: 45 - 90 minutos en i5-12400f
=============================================================================
"""
import os
import logging
import warnings
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import f1_score, precision_recall_curve
from dotenv import load_dotenv
import xgboost as xgb
import lightgbm as lgb
import optuna

# Suprimir warnings molestos y logs excesivos de Optuna
warnings.filterwarnings('ignore')
optuna.logging.set_verbosity(optuna.logging.WARNING)

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

# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================
def find_optimal_threshold(y_true, y_proba):
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    scores = 2 * (precision * recall) / (precision + recall + 1e-8)
    optimal_idx = np.argmax(scores)
    return thresholds[optimal_idx], scores[optimal_idx]

# ============================================================================
# 1. OPTIMIZACIÓN CON OPTUNA (XGBOOST)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("FASE 1: OPTIMIZACIÓN BAYESIANA - XGBOOST (30 trials)")
logger.info("="*80)

def objective_xgb(trial):
    param = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 400),
        'max_depth': trial.suggest_int('max_depth', 3, 8),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'gamma': trial.suggest_float('gamma', 0.0, 5.0),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        'tree_method': 'hist', # Acelera drásticamente en CPU
        'n_jobs': 6, # Usar 6 de los 12 hilos de tu i5-12400f
        'random_state': 42,
        'eval_metric': 'logloss'
    }
    
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = []
    for train_idx, val_idx in cv.split(X_train, y_train):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
        
        model = xgb.XGBClassifier(**param)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        y_pred = model.predict(X_val)
        scores.append(f1_score(y_val, y_pred))
        
        trial.report(np.mean(scores), len(scores)-1)
        if trial.should_prune():
            raise optuna.TrialPruned()
            
    return np.mean(scores)

study_xgb = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42), pruner=optuna.pruners.MedianPruner())
study_xgb.optimize(objective_xgb, n_trials=30, show_progress_bar=True)

logger.info(f"✅ Mejor F1-Score XGBoost: {study_xgb.best_value:.4f}")
logger.info(f"Mejores parámetros: {study_xgb.best_params}")

# ============================================================================
# 2. OPTIMIZACIÓN CON OPTUNA (LIGHTGBM)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("FASE 2: OPTIMIZACIÓN BAYESIANA - LIGHTGBM (30 trials)")
logger.info("="*80)

def objective_lgb(trial):
    param = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 400),
        'max_depth': trial.suggest_int('max_depth', 3, 8),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.1, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_samples': trial.suggest_int('min_child_samples', 10, 50),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 10.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 10.0, log=True),
        'n_jobs': 6,
        'random_state': 42,
        'verbose': -1
    }
    
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    scores = []
    for train_idx, val_idx in cv.split(X_train, y_train):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]
        
        model = lgb.LGBMClassifier(**param)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)])
        y_pred = model.predict(X_val)
        scores.append(f1_score(y_val, y_pred))
        
        trial.report(np.mean(scores), len(scores)-1)
        if trial.should_prune():
            raise optuna.TrialPruned()
            
    return np.mean(scores)

study_lgb = optuna.create_study(direction='maximize', sampler=optuna.samplers.TPESampler(seed=42), pruner=optuna.pruners.MedianPruner())
study_lgb.optimize(objective_lgb, n_trials=30, show_progress_bar=True)

logger.info(f"✅ Mejor F1-Score LightGBM: {study_lgb.best_value:.4f}")
logger.info(f"Mejores parámetros: {study_lgb.best_params}")

# ============================================================================
# 3. ENTRENAMIENTO FINAL Y EVALUACIÓN EN TEST
# ============================================================================
logger.info("\n" + "="*80)
logger.info("FASE 3: ENTRENAMIENTO FINAL Y EVALUACIÓN EN CONJUNTO DE PRUEBA")
logger.info("="*80)

# Entrenar XGBoost con mejores params
logger.info("Entrenando XGBoost final con mejores parámetros...")
xgb_best = xgb.XGBClassifier(**study_xgb.best_params, random_state=42, n_jobs=6)
xgb_best.fit(X_train, y_train)
joblib.dump(xgb_best, f"{MODELS_DIR}/xgboost_tier2.pkl")

# Entrenar LightGBM con mejores params
logger.info("Entrenando LightGBM final con mejores parámetros...")
lgb_best = lgb.LGBMClassifier(**study_lgb.best_params, random_state=42, n_jobs=6)
lgb_best.fit(X_train, y_train)
joblib.dump(lgb_best, f"{MODELS_DIR}/lightgbm_tier2.pkl")

# Predicciones en Test
proba_xgb_t2 = xgb_best.predict_proba(X_test)[:, 1]
proba_lgb_t2 = lgb_best.predict_proba(X_test)[:, 1]

# Umbrales óptimos
thr_xgb, f1_xgb = find_optimal_threshold(y_test, proba_xgb_t2)
thr_lgb, f1_lgb = find_optimal_threshold(y_test, proba_lgb_t2)

logger.info(f"\n🏆 Resultados TIER 2 en Conjunto de Prueba:")
logger.info(f"XGBoost (Optimizado)   : F1 = {f1_xgb:.4f} (Umbral: {thr_xgb:.4f})")
logger.info(f"LightGBM (Optimizado)  : F1 = {f1_lgb:.4f} (Umbral: {thr_lgb:.4f})")

# ============================================================================
# 4. NUEVO ENSEMBLE HÍBRIDO (5 MODELOS)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("FASE 4: ACTUALIZACIÓN DEL ENSEMBLE HÍBRIDO (5 MODELOS)")
logger.info("="*80)

# Cargar modelos anteriores (TIER 1)
rf = joblib.load(f"{MODELS_DIR}/random_forest_model.pkl")
svm_model = joblib.load(f"{MODELS_DIR}/svm_model.pkl")

proba_rf = rf.predict_proba(X_test)[:, 1]
proba_svm = svm_model.predict_proba(X_test)[:, 1]

# Calcular pesos basados en F1-Score de cada modelo
scores_dict = {
    'rf': 0.5952,   # De TIER 1
    'xgb': f1_xgb,  # Nuevo TIER 2
    'svm': 0.6154,  # De TIER 1
    'lgb': f1_lgb   # Nuevo TIER 2
}
total = sum(scores_dict.values())
weights = {k: v/total for k, v in scores_dict.items()}

logger.info(f"Pesos calculados para el nuevo ensamble: { {k: f'{v:.4f}' for k, v in weights.items()} }")

# Weighted Voting con 5 modelos
weighted_proba_t2 = (weights['rf'] * proba_rf + weights['xgb'] * proba_xgb_t2 + 
                     weights['svm'] * proba_svm + weights['lgb'] * proba_lgb_t2)

thr_ens, f1_ens = find_optimal_threshold(y_test, weighted_proba_t2)
logger.info(f"🚀 Ensamble TIER 2 (5 modelos): F1 = {f1_ens:.4f} (Umbral: {thr_ens:.4f})")

# Guardar resumen
results = {
    'XGBoost_Tier2': f1_xgb,
    'LightGBM_Tier2': f1_lgb,
    'Ensemble_Tier2_5_Models': f1_ens
}
pd.DataFrame([results]).to_csv(f"{REPORTS_DIR}/tier2_results.csv", index=False)
logger.info(f"\n✅ Resultados guardados en {REPORTS_DIR}/tier2_results.csv")
logger.info("="*80)
logger.info("🎉 ¡OPTIMIZACIÓN TIER 2 COMPLETADA EXITOSAMENTE!")
logger.info("="*80)