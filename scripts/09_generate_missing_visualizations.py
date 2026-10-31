#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 09_generate_missing_visualizations.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: Generar visualizaciones faltantes para el documento de tesis
=============================================================================
"""
import os
import logging
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = "models_saved"
REPORTS_DIR = "reports"
DATA_DIR = "data/raw"

# Configuración de estilo
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10

# ============================================================================
# VISUALIZACIÓN 1: DISTRIBUCIÓN DE CLASES
# ============================================================================
logger.info("\n" + "="*80)
logger.info("GENERANDO VISUALIZACIÓN 1: DISTRIBUCIÓN DE CLASES")
logger.info("="*80)

# Cargar dataset original
logger.info("Cargando dataset original...")
df_raw = pd.read_parquet(f"{DATA_DIR}/financial_fraud_risk_raw.parquet")

# Contar clases
class_counts = df_raw['risk_label'].value_counts()
legit_count = class_counts[0]
fraud_count = class_counts[1]
total = len(df_raw)

logger.info(f"Transacciones legítimas: {legit_count:,} ({legit_count/total*100:.2f}%)")
logger.info(f"Transacciones fraudulentas: {fraud_count:,} ({fraud_count/total*100:.2f}%)")

# Crear gráfico de barras
fig, ax = plt.subplots(figsize=(10, 6))

classes = ['Legítimas (0)', 'Fraudulentas (1)']
counts = [legit_count, fraud_count]
percentages = [legit_count/total*100, fraud_count/total*100]
colors = ['#2ecc71', '#e74c3c']

bars = ax.bar(classes, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

# Agregar etiquetas con conteo y porcentaje
for i, (bar, count, pct) in enumerate(zip(bars, counts, percentages)):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{count:,}\n({pct:.2f}%)',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax.set_xlabel('Clase', fontsize=12, fontweight='bold')
ax.set_ylabel('Número de Transacciones', fontsize=12, fontweight='bold')
ax.set_title('Distribución de Clases en el Dataset Original\nFuerte Desbalance: 98.5% Legítimas vs 1.5% Fraudulentas', 
             fontsize=14, fontweight='bold', pad=20)
ax.set_ylim(0, max(counts) * 1.15)
ax.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig(f"{REPORTS_DIR}/04_class_distribution.png", dpi=300, bbox_inches='tight')
logger.info(f"✅ Visualización 1 guardada: {REPORTS_DIR}/04_class_distribution.png")
plt.close()

# ============================================================================
# CARGAR MODELOS Y DATOS DE PRUEBA
# ============================================================================
logger.info("\nCargando modelos y datos de prueba...")

# Cargar datos de prueba
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)
X_test = df_test.drop(columns=['risk_label'])
y_test = df_test['risk_label']

# Cargar modelos
rf = joblib.load(f"{MODELS_DIR}/random_forest_model.pkl")
xgb_model = joblib.load(f"{MODELS_DIR}/xgboost_model.pkl")
svm_model = joblib.load(f"{MODELS_DIR}/svm_model.pkl")

logger.info("✅ Modelos y datos cargados")

# ============================================================================
# VISUALIZACIÓN 2: MATRIZ DE CONFUSIÓN DE XGBOOST
# ============================================================================
logger.info("\n" + "="*80)
logger.info("GENERANDO VISUALIZACIÓN 2: MATRIZ DE CONFUSIÓN DE XGBOOST")
logger.info("="*80)

# Obtener predicciones de XGBoost con umbral óptimo
logger.info("Generando predicciones de XGBoost...")
proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
threshold_xgb = 0.6358  # Umbral óptimo encontrado
y_pred_xgb = (proba_xgb >= threshold_xgb).astype(int)

# Calcular matriz de confusión
cm = confusion_matrix(y_test, y_pred_xgb)

logger.info("Matriz de confusión:")
logger.info(f"  TN: {cm[0,0]:,} | FP: {cm[0,1]:,}")
logger.info(f"  FN: {cm[1,0]:,} | TP: {cm[1,1]:,}")

# Crear visualización
fig, ax = plt.subplots(figsize=(10, 8))

disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Legítima (0)', 'Fraudulenta (1)'])
disp.plot(cmap='Blues', ax=ax, colorbar=False)

# Personalizar
ax.set_xlabel('Predicción', fontsize=12, fontweight='bold')
ax.set_ylabel('Valor Real', fontsize=12, fontweight='bold')
ax.set_title(f'Matriz de Confusión - XGBoost Optimizado\n(Umbral: {threshold_xgb:.4f})', 
             fontsize=14, fontweight='bold', pad=20)

# Agregar valores en las celdas
for i in range(2):
    for j in range(2):
        text = ax.text(j, i, f'{cm[i, j]:,}',
                      ha="center", va="center", 
                      color="white" if cm[i, j] > 5000 else "black",
                      fontsize=16, fontweight='bold')

plt.tight_layout()
plt.savefig(f"{REPORTS_DIR}/05_confusion_matrix_xgboost.png", dpi=300, bbox_inches='tight')
logger.info(f"✅ Visualización 2 guardada: {REPORTS_DIR}/05_confusion_matrix_xgboost.png")
plt.close()

# ============================================================================
# VISUALIZACIÓN 3: CURVA ROC COMPARATIVA
# ============================================================================
logger.info("\n" + "="*80)
logger.info("GENERANDO VISUALIZACIÓN 3: CURVA ROC COMPARATIVA")
logger.info("="*80)

# Obtener probabilidades de todos los modelos
logger.info("Generando predicciones de todos los modelos...")
proba_rf = rf.predict_proba(X_test)[:, 1]
proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
proba_svm = svm_model.predict_proba(X_test)[:, 1]

# Calcular curvas ROC
fpr_rf, tpr_rf, _ = roc_curve(y_test, proba_rf)
auc_rf = auc(fpr_rf, tpr_rf)

fpr_xgb, tpr_xgb, _ = roc_curve(y_test, proba_xgb)
auc_xgb = auc(fpr_xgb, tpr_xgb)

fpr_svm, tpr_svm, _ = roc_curve(y_test, proba_svm)
auc_svm = auc(fpr_svm, tpr_svm)

# Crear visualización
fig, ax = plt.subplots(figsize=(10, 8))

ax.plot(fpr_rf, tpr_rf, label=f'Random Forest (AUC = {auc_rf:.4f})', linewidth=2, color='#3498db')
ax.plot(fpr_xgb, tpr_xgb, label=f'XGBoost (AUC = {auc_xgb:.4f})', linewidth=2, color='#e74c3c')
ax.plot(fpr_svm, tpr_svm, label=f'SVM (AUC = {auc_svm:.4f})', linewidth=2, color='#2ecc71')

# Línea diagonal (clasificador aleatorio)
ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Clasificador Aleatorio', alpha=0.5)

ax.set_xlabel('Tasa de Falsos Positivos (FPR)', fontsize=12, fontweight='bold')
ax.set_ylabel('Tasa de Verdaderos Positivos (TPR)', fontsize=12, fontweight='bold')
ax.set_title('Curvas ROC Comparativas - Capacidad Discriminativa de los Modelos', 
             fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='lower right', fontsize=10)
ax.grid(alpha=0.3)
ax.set_xlim([0.0, 1.0])
ax.set_ylim([0.0, 1.05])

plt.tight_layout()
plt.savefig(f"{REPORTS_DIR}/06_roc_curves_comparison.png", dpi=300, bbox_inches='tight')
logger.info(f"✅ Visualización 3 guardada: {REPORTS_DIR}/06_roc_curves_comparison.png")
plt.close()

# ============================================================================
# RESUMEN FINAL
# ============================================================================
logger.info("\n" + "="*80)
logger.info("✅ TODAS LAS VISUALIZACIONES FALTANTES GENERADAS EXITOSAMENTE")
logger.info("="*80)
logger.info("\nImágenes generadas:")
logger.info(f"  1. {REPORTS_DIR}/04_class_distribution.png - Distribución de clases")
logger.info(f"  2. {REPORTS_DIR}/05_confusion_matrix_xgboost.png - Matriz de confusión XGBoost")
logger.info(f"  3. {REPORTS_DIR}/06_roc_curves_comparison.png - Curvas ROC comparativas")