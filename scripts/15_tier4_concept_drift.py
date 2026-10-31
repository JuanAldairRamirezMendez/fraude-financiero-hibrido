#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 15_tier4_concept_drift.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: TIER 4 - Simulación y Detección de Concept Drift
TIEMPO ESTIMADO: 2-5 minutos
=============================================================================
"""
import os
import logging
import warnings
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.metrics import f1_score, recall_score, precision_score
from scipy.stats import ks_2samp
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns

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

logger.info("Cargando datos de prueba y modelo XGBoost TIER 2...")
df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)
X_test = df_test.drop(columns=['risk_label'])
y_test = df_test['risk_label']

# Cargar el mejor modelo
xgb_tier2 = joblib.load(f"{MODELS_DIR}/xgboost_tier2.pkl")
threshold_xgb = 0.4412  # Umbral óptimo del TIER 2

logger.info("✅ Datos y modelo cargados correctamente")

# ============================================================================
# PASO 1: EVALUACIÓN BASELINE (Sin Drift)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PASO 1: EVALUACIÓN BASELINE (Distribución Original)")
logger.info("="*80)

proba_baseline = xgb_tier2.predict_proba(X_test)[:, 1]
y_pred_baseline = (proba_baseline >= threshold_xgb).astype(int)

f1_base = f1_score(y_test, y_pred_baseline)
recall_base = recall_score(y_test, y_pred_baseline)
prec_base = precision_score(y_test, y_pred_baseline)

logger.info(f"Baseline -> F1: {f1_base:.4f} | Recall: {recall_base:.4f} | Precision: {prec_base:.4f}")

# ============================================================================
# PASO 2: SIMULACIÓN DE CONCEPT DRIFT
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PASO 2: SIMULACIÓN DE CONCEPT DRIFT (Cambio de Patrones)")
logger.info("="*80)

# Simulamos un drift en 2 variables clave:
# 1. Los defraudadores ahora usan montos un 40% más altos en promedio.
# 2. El 'customer_risk_score' histórico ya no es tan predictivo (ruido añadido).
X_test_drifted = X_test.copy()

# Drift 1: Shift en la distribución del monto
X_test_drifted['transaction_amount'] = X_test_drifted['transaction_amount'] * 1.4

# Drift 2: Ruido en el risk_score (simulando que los scores históricos fueron comprometidos o cambiaron)
np.random.seed(42)
noise = np.random.normal(0, 0.15, size=len(X_test_drifted))
X_test_drifted['customer_risk_score'] = np.clip(X_test_drifted['customer_risk_score'] + noise, 0, 1)

logger.info("Distribución alterada para simular nuevas tácticas de fraude.")

# Evaluar modelo con datos con Drift
proba_drifted = xgb_tier2.predict_proba(X_test_drifted)[:, 1]
y_pred_drifted = (proba_drifted >= threshold_xgb).astype(int)

f1_drift = f1_score(y_test, y_pred_drifted)
recall_drift = recall_score(y_test, y_pred_drifted)
prec_drift = precision_score(y_test, y_pred_drifted)

logger.info(f"Con Drift  -> F1: {f1_drift:.4f} | Recall: {recall_drift:.4f} | Precision: {prec_drift:.4f}")

# ============================================================================
# PASO 3: DETECCIÓN ESTADÍSTICA DEL DRIFT (Kolmogorov-Smirnov Test)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PASO 3: DETECCIÓN ESTADÍSTICA (Kolmogorov-Smirnov)")
logger.info("="*80)

# El test KS compara si dos muestras vienen de la misma distribución.
# p-value < 0.05 indica que hay una diferencia estadísticamente significativa (Drift detectado).
ks_amount, p_value_amount = ks_2samp(X_test['transaction_amount'], X_test_drifted['transaction_amount'])
ks_risk, p_value_risk = ks_2samp(X_test['customer_risk_score'], X_test_drifted['customer_risk_score'])

logger.info(f"KS Test 'transaction_amount': statistic={ks_amount:.4f}, p-value={p_value_amount:.4e} {'[DRIFT DETECTADO]' if p_value_amount < 0.05 else '[Sin Drift]'}")
logger.info(f"KS Test 'customer_risk_score': statistic={ks_risk:.4f}, p-value={p_value_risk:.4e} {'[DRIFT DETECTADO]' if p_value_risk < 0.05 else '[Sin Drift]'}")

# ============================================================================
# PASO 4: VISUALIZACIÓN DEL IMPACTO DEL DRIFT
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PASO 4: GENERANDO VISUALIZACIÓN DE IMPACTO")
logger.info("="*80)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Gráfica 1: Degradación de Métricas
metrics = ['F1-Score', 'Recall', 'Precision']
baseline_vals = [f1_base, recall_base, prec_base]
drifted_vals = [f1_drift, recall_drift, prec_drift]

x = np.arange(len(metrics))
width = 0.35

axes[0].bar(x - width/2, baseline_vals, width, label='Baseline (Original)', color='#2ecc71')
axes[0].bar(x + width/2, drifted_vals, width, label='Con Concept Drift', color='#e74c3c')

axes[0].set_xlabel('Métrica', fontsize=12, fontweight='bold')
axes[0].set_ylabel('Valor', fontsize=12, fontweight='bold')
axes[0].set_title('Degradación del Rendimiento del Modelo ante Concept Drift', fontsize=13, fontweight='bold')
axes[0].set_xticks(x)
axes[0].set_xticklabels(metrics)
axes[0].set_ylim(0, 1.0)
axes[0].legend()
axes[0].grid(axis='y', alpha=0.3)

# Añadir valores en las barras
for i, v in enumerate(baseline_vals):
    axes[0].text(i - width/2, v + 0.02, f'{v:.2f}', ha='center', fontweight='bold')
for i, v in enumerate(drifted_vals):
    axes[0].text(i + width/2, v + 0.02, f'{v:.2f}', ha='center', fontweight='bold')

# Gráfica 2: Distribución de la variable con Drift
sns.kdeplot(X_test['transaction_amount'], ax=axes[1], label='Distribución Original', color='#2ecc71', fill=True, alpha=0.5)
sns.kdeplot(X_test_drifted['transaction_amount'], ax=axes[1], label='Distribución con Drift (+40%)', color='#e74c3c', fill=True, alpha=0.5)

axes[1].set_xlabel('Monto de la Transacción', fontsize=12, fontweight='bold')
axes[1].set_ylabel('Densidad', fontsize=12, fontweight='bold')
axes[1].set_title('Detección Estadística de Drift (Kolmogorov-Smirnov)', fontsize=13, fontweight='bold')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f"{REPORTS_DIR}/10_concept_drift_impact.png", dpi=300, bbox_inches='tight')
logger.info(f"✅ Gráfica guardada: {REPORTS_DIR}/10_concept_drift_impact.png")
plt.close()

# ============================================================================
# RESUMEN FINAL
# ============================================================================
logger.info("\n" + "="*80)
logger.info("🎉 ¡SIMULACIÓN DE CONCEPT DRIFT COMPLETADA EXITOSAMENTE!")
logger.info("="*80)
logger.info(f"Degradación del F1-Score: {f1_base:.4f} -> {f1_drift:.4f} (Δ {f1_drift - f1_base:.4f})")
logger.info("Esta simulación demuestra la necesidad de implementar un módulo de monitoreo continuo")
logger.info("y reentrenamiento periódico en un entorno de producción real.")