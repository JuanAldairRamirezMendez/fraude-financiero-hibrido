#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 14_tier4_advanced.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: TIER 4 - Feature Engineering Avanzado + Isolation Forest (Anomalías)
TIEMPO ESTIMADO: 5-10 minutos (CPU intensivo pero rápido en i5-12400f)
=============================================================================
"""
import os
import logging
import warnings
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_recall_curve, f1_score, roc_auc_score
from sklearn.preprocessing import StandardScaler
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

logger.info("Cargando datos desde PostgreSQL...")
df_train = pd.read_sql("SELECT * FROM train_cleaned_balanced", engine)
df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)

# Separar variables
X_train = df_train.drop(columns=['risk_label'])
y_train = df_train['risk_label']
X_test = df_test.drop(columns=['risk_label'])
y_test = df_test['risk_label']

logger.info(f"Datos cargados: Train={X_train.shape}, Test={X_test.shape}")

# ============================================================================
# MEJORA 1: FEATURE ENGINEERING AVANZADO (Ingeniería de Características)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("MEJORA 1: FEATURE ENGINEERING AVANZADO (Variables Interactivas)")
logger.info("="*80)

def create_advanced_features(df):
    """Crea nuevas variables basadas en interacciones de dominio financiero."""
    df = df.copy()
    
    # 1. Monto relativo a la velocidad de transacción (Detecta ráfagas de alto monto)
    df['amount_per_velocity_1h'] = df['transaction_amount'] / (df['transaction_velocity_1h'] + 1)
    
    # 2. Interacción de riesgo histórico con el monto actual
    df['risk_amount_interaction'] = df['customer_risk_score'] * df['transaction_amount']
    
    # 3. Frecuencia de contracargos relativa a la antigüedad de la cuenta
    df['chargeback_frequency'] = df['previous_chargebacks'] / (df['account_age_days'] + 1)
    
    # 4. Desviación del monto promedio del cliente
    df['amount_deviation_from_avg'] = df['transaction_amount'] - df['avg_transaction_amount_30d_customer']
    
    return df

logger.info("Generando nuevas características interactivas...")
X_train_adv = create_advanced_features(X_train)
X_test_adv = create_advanced_features(X_test)

logger.info(f"✅ Nuevas dimensiones: Train={X_train_adv.shape}, Test={X_test_adv.shape}")

# Escalar las nuevas características para el Isolation Forest
scaler_adv = StandardScaler()
X_train_adv_scaled = scaler_adv.fit_transform(X_train_adv)
X_test_adv_scaled = scaler_adv.transform(X_test_adv)

# ============================================================================
# MEJORA 2: ISOLATION FOREST (Modelo de Anomalías No Supervisado)
# ============================================================================
logger.info("\n" + "="*80)
logger.info("MEJORA 2: ISOLATION FOREST (Detección de Anomalías)")
logger.info("="*80)

# El Isolation Forest se entrena idealmente solo con datos "normales" (legítimos)
# para que aprenda el comportamiento estándar y marque como anomalía lo que se desvíe.
logger.info("Entrenando Isolation Forest exclusivamente con transacciones legítimas...")
legit_train_mask = (y_train == 0)
X_train_legit = X_train_adv_scaled[legit_train_mask]

# contamination=0.015 porque sabemos que el fraude real es aprox 1.5% en el test set
iforest = IsolationForest(
    n_estimators=200, 
    contamination=0.015, 
    random_state=42, 
    n_jobs=6, # Usar 6 hilos de tu i5-12400f
    max_samples='auto'
)

iforest.fit(X_train_legit)
joblib.dump(iforest, f"{MODELS_DIR}/isolation_forest_tier4.pkl")
joblib.dump(scaler_adv, f"{MODELS_DIR}/scaler_tier4_features.pkl")
logger.info("✅ Modelo Isolation Forest y Scaler guardados")

# Predicción y Puntaje de Anomalía (Anomaly Score)
# score_samples devuelve valores negativos: más negativo = más anómalo (fraudulento)
logger.info("Calculando puntajes de anomalía en el conjunto de prueba...")
anomaly_scores = iforest.score_samples(X_test_adv_scaled)

# Convertir a probabilidad de fraude (invertir y normalizar)
# Multiplicamos por -1 para que valores altos signifiquen "más fraude"
fraud_proba_if = -anomaly_scores 

# ============================================================================
# EVALUACIÓN DEL MODELO DE ANOMALÍAS
# ============================================================================
logger.info("\n" + "="*80)
logger.info("EVALUACIÓN: Isolation Forest en Conjunto de Prueba")
logger.info("="*80)

# Calcular métricas
auc_pr_if = roc_auc_score(y_test, fraud_proba_if)
precision, recall, thresholds = precision_recall_curve(y_test, fraud_proba_if)
f1_scores = 2 * (precision * recall) / (precision + recall + 1e-8)
optimal_idx = np.argmax(f1_scores)
thr_if = thresholds[optimal_idx] if len(thresholds) > 0 else np.median(fraud_proba_if)
f1_if = f1_scores[optimal_idx]

logger.info(f"🏆 Isolation Forest (TIER 4):")
logger.info(f"   F1-Score: {f1_if:.4f}")
logger.info(f"   AUC-ROC:  {auc_pr_if:.4f}")
logger.info(f"   Umbral óptimo de anomalía: {thr_if:.4f}")

# ============================================================================
# VISUALIZACIÓN: Distribución de Puntajes de Anomalía
# ============================================================================
logger.info("\n" + "="*80)
logger.info("GENERANDO VISUALIZACIÓN: Distribución de Anomalías")
logger.info("="*80)

df_plot = pd.DataFrame({
    'Anomaly_Score': fraud_proba_if,
    'Actual_Fraud': y_test
})

plt.figure(figsize=(10, 6))
sns.kdeplot(data=df_plot[df_plot['Actual_Fraud'] == 0], x='Anomaly_Score', label='Legítimas (0)', fill=True, color='green', alpha=0.5)
sns.kdeplot(data=df_plot[df_plot['Actual_Fraud'] == 1], x='Anomaly_Score', label='Fraudulentas (1)', fill=True, color='red', alpha=0.5)

plt.title('Distribución de Puntajes de Anomalía (Isolation Forest)', fontsize=14, fontweight='bold')
plt.xlabel('Puntaje de Anomalía (Mayor valor = Más probable fraude)', fontsize=12, fontweight='bold')
plt.ylabel('Densidad', fontsize=12, fontweight='bold')
plt.legend(fontsize=11)
plt.grid(alpha=0.3)

plt.tight_layout()
plt.savefig(f"{REPORTS_DIR}/09_anomaly_score_distribution.png", dpi=300, bbox_inches='tight')
logger.info(f"✅ Gráfica guardada: {REPORTS_DIR}/09_anomaly_score_distribution.png")
plt.close()

# ============================================================================
# RESUMEN FINAL TIER 4
# ============================================================================
logger.info("\n" + "="*80)
logger.info("🎉 ¡TIER 4 COMPLETADO EXITOSAMENTE!")
logger.info("="*80)
logger.info("Se han generado 4 nuevas variables interactivas.")
logger.info("Se ha entrenado y evaluado el modelo Isolation Forest.")
logger.info("Se ha generado la visualización de la distribución de anomalías.")