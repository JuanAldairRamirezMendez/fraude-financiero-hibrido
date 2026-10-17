#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 08_save_and_visualize.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: Guardar modelos optimizados + Generar reporte visual comparativo
TIEMPO ESTIMADO: 5-10 minutos
=============================================================================
"""
import os
import json
import logging
import pandas as pd
import numpy as np
import joblib
from sqlalchemy import create_engine
from sklearn.metrics import precision_recall_curve, f1_score, precision_score, recall_score, roc_auc_score
from dotenv import load_dotenv
import tensorflow as tf
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = "models_saved"
REPORTS_DIR = "reports"

# Cargar datos
DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

logger.info("Cargando datos de prueba...")
df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)
X_test = df_test.drop(columns=['risk_label'])
y_test = df_test['risk_label']

# Cargar modelos
logger.info("Cargando modelos...")
rf = joblib.load(f"{MODELS_DIR}/random_forest_model.pkl")
xgb_model = joblib.load(f"{MODELS_DIR}/xgboost_model.pkl")
svm_model = joblib.load(f"{MODELS_DIR}/svm_model.pkl")
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
dnn_model = tf.keras.models.load_model(f"{MODELS_DIR}/dnn_model.keras")

# ============================================================================
# PARTE A: GUARDAR MODELOS OPTIMIZADOS
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PARTE A: GUARDANDO MODELOS OPTIMIZADOS")
logger.info("="*80)

def find_optimal_threshold(y_true, y_proba):
    precision, recall, thresholds = precision_recall_curve(y_true, y_proba)
    scores = 2 * (precision * recall) / (precision + recall + 1e-8)
    optimal_idx = np.argmax(scores)
    return thresholds[optimal_idx], scores[optimal_idx]

# Generar predicciones
logger.info("Generando predicciones...")
proba_rf = rf.predict_proba(X_test)[:, 1]
proba_xgb = xgb_model.predict_proba(X_test)[:, 1]
proba_svm = svm_model.predict_proba(X_test)[:, 1]
proba_dnn = dnn_model.predict(X_test, verbose=0).flatten()

# Optimizar umbrales
logger.info("Calculando umbrales óptimos...")
threshold_rf, f1_rf_opt = find_optimal_threshold(y_test, proba_rf)
threshold_xgb, f1_xgb_opt = find_optimal_threshold(y_test, proba_xgb)
threshold_svm, f1_svm_opt = find_optimal_threshold(y_test, proba_svm)
threshold_dnn, f1_dnn_opt = find_optimal_threshold(y_test, proba_dnn)

# Calcular pesos para weighted voting
f1_scores = {'rf': f1_rf_opt, 'xgb': f1_xgb_opt, 'svm': f1_svm_opt, 'dnn': f1_dnn_opt}
total_f1 = sum(f1_scores.values())
weights = {k: v/total_f1 for k, v in f1_scores.items()}

weighted_proba = (weights['rf'] * proba_rf + weights['xgb'] * proba_xgb + 
                  weights['svm'] * proba_svm + weights['dnn'] * proba_dnn)
threshold_weighted, f1_weighted_opt = find_optimal_threshold(y_test, weighted_proba)

# Guardar configuración optimizada
optimized_config = {
    'modelos_optimizados': {
        'random_forest': {
            'umbral_optimo': float(threshold_rf),
            'f1_score': float(f1_rf_opt),
            'peso_ensamble': float(weights['rf'])
        },
        'xgboost': {
            'umbral_optimo': float(threshold_xgb),
            'f1_score': float(f1_xgb_opt),
            'peso_ensamble': float(weights['xgb'])
        },
        'svm': {
            'umbral_optimo': float(threshold_svm),
            'f1_score': float(f1_svm_opt),
            'peso_ensamble': float(weights['svm'])
        },
        'dnn': {
            'umbral_optimo': float(threshold_dnn),
            'f1_score': float(f1_dnn_opt),
            'peso_ensamble': float(weights['dnn'])
        },
        'weighted_voting': {
            'umbral_optimo': float(threshold_weighted),
            'f1_score': float(f1_weighted_opt)
        }
    },
    'metadata': {
        'fecha_optimizacion': pd.Timestamp.now().isoformat(),
        'dataset_prueba': len(X_test),
        'metodo': 'Precision-Recall Curve Optimization'
    }
}

with open(f"{MODELS_DIR}/optimized_thresholds.json", 'w') as f:
    json.dump(optimized_config, f, indent=2)

logger.info("✅ Configuración optimizada guardada en models_saved/optimized_thresholds.json")
logger.info(f"   Umbrales: RF={threshold_rf:.4f}, XGB={threshold_xgb:.4f}, SVM={threshold_svm:.4f}, DNN={threshold_dnn:.4f}")
logger.info(f"   Weighted Voting: umbral={threshold_weighted:.4f}, F1={f1_weighted_opt:.4f}")

# ============================================================================
# PARTE B: GENERAR REPORTE VISUAL COMPARATIVO
# ============================================================================
logger.info("\n" + "="*80)
logger.info("PARTE B: GENERANDO REPORTE VISUAL COMPARATIVO")
logger.info("="*80)

# Cargar resultados originales
df_original = pd.read_csv(f"{MODELS_DIR}/final_model_comparison.csv")

# Configurar estilo de gráficas
sns.set_style("whitegrid")
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 10

# ============================================================================
# GRÁFICA 1: Comparación de F1-Score (Antes vs Después)
# ============================================================================
logger.info("Generando gráfica 1: Comparación de F1-Score...")

fig, ax = plt.subplots(figsize=(12, 6))

# Preparar datos
modelos = ['Random Forest', 'XGBoost', 'SVM', 'DNN', 'Soft Voting']
f1_original = [
    df_original[df_original['model'] == 'Random Forest (Threshold 0.3)']['f1_score'].values[0],
    df_original[df_original['model'] == 'XGBoost']['f1_score'].values[0],
    df_original[df_original['model'] == 'SVM (Linear Optimizado)']['f1_score'].values[0],
    df_original[df_original['model'] == 'DNN (TensorFlow/Keras)']['f1_score'].values[0],
    df_original[df_original['model'] == 'Ensamble Soft Voting']['f1_score'].values[0]
]

f1_optimizado = [f1_rf_opt, f1_xgb_opt, f1_svm_opt, f1_dnn_opt, f1_weighted_opt]

x = np.arange(len(modelos))
width = 0.35

bars1 = ax.bar(x - width/2, f1_original, width, label='Original', color='#3498db', alpha=0.7)
bars2 = ax.bar(x + width/2, f1_optimizado, width, label='Optimizado (TIER 1)', color='#e74c3c', alpha=0.7)

ax.set_xlabel('Modelo', fontsize=12, fontweight='bold')
ax.set_ylabel('F1-Score', fontsize=12, fontweight='bold')
ax.set_title('Comparación de F1-Score: Modelos Originales vs Optimizados', fontsize=14, fontweight='bold', pad=20)
ax.set_xticks(x)
ax.set_xticklabels(modelos, rotation=15, ha='right')
ax.legend(loc='upper left', fontsize=11)
ax.set_ylim(0, 0.8)
ax.grid(axis='y', alpha=0.3)

# Agregar valores en las barras
for bars in [bars1, bars2]:
    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

plt.tight_layout()
plt.savefig(f"{REPORTS_DIR}/01_f1_score_comparison.png", dpi=300, bbox_inches='tight')
logger.info(f"✅ Gráfica 1 guardada: {REPORTS_DIR}/01_f1_score_comparison.png")
plt.close()

# ============================================================================
# GRÁFICA 2: Curvas Precision-Recall
# ============================================================================
logger.info("Generando gráfica 2: Curvas Precision-Recall...")

fig, ax = plt.subplots(figsize=(10, 8))

# Calcular curvas Precision-Recall
precision_rf, recall_rf, _ = precision_recall_curve(y_test, proba_rf)
precision_xgb, recall_xgb, _ = precision_recall_curve(y_test, proba_xgb)
precision_svm, recall_svm, _ = precision_recall_curve(y_test, proba_svm)
precision_dnn, recall_dnn, _ = precision_recall_curve(y_test, proba_dnn)

# Plot
ax.plot(recall_rf, precision_rf, label=f'Random Forest (F1={f1_rf_opt:.3f})', linewidth=2, color='#3498db')
ax.plot(recall_xgb, precision_xgb, label=f'XGBoost (F1={f1_xgb_opt:.3f})', linewidth=2, color='#e74c3c')
ax.plot(recall_svm, precision_svm, label=f'SVM (F1={f1_svm_opt:.3f})', linewidth=2, color='#2ecc71')
ax.plot(recall_dnn, precision_dnn, label=f'DNN (F1={f1_dnn_opt:.3f})', linewidth=2, color='#f39c12')

ax.set_xlabel('Recall', fontsize=12, fontweight='bold')
ax.set_ylabel('Precision', fontsize=12, fontweight='bold')
ax.set_title('Curvas Precision-Recall (Modelos Optimizados)', fontsize=14, fontweight='bold', pad=20)
ax.legend(loc='lower left', fontsize=10)
ax.grid(alpha=0.3)
ax.set_xlim(0, 1)
ax.set_ylim(0, 1)

plt.tight_layout()
plt.savefig(f"{REPORTS_DIR}/02_precision_recall_curves.png", dpi=300, bbox_inches='tight')
logger.info(f"✅ Gráfica 2 guardada: {REPORTS_DIR}/02_precision_recall_curves.png")
plt.close()

# ============================================================================
# GRÁFICA 3: Mejora Porcentual por Modelo
# ============================================================================
logger.info("Generando gráfica 3: Mejora porcentual...")

fig, ax = plt.subplots(figsize=(10, 6))

mejoras = [
    ((f1_rf_opt - f1_original[0]) / f1_original[0]) * 100,
    ((f1_xgb_opt - f1_original[1]) / f1_original[1]) * 100,
    ((f1_svm_opt - f1_original[2]) / f1_original[2]) * 100,
    ((f1_dnn_opt - f1_original[3]) / f1_original[3]) * 100,
    ((f1_weighted_opt - f1_original[4]) / f1_original[4]) * 100
]

colors = ['#3498db' if m > 0 else '#e74c3c' for m in mejoras]
bars = ax.bar(modelos, mejoras, color=colors, alpha=0.7, edgecolor='black', linewidth=1.5)

ax.set_xlabel('Modelo', fontsize=12, fontweight='bold')
ax.set_ylabel('Mejora en F1-Score (%)', fontsize=12, fontweight='bold')
ax.set_title('Mejora Porcentual en F1-Score (Optimización TIER 1)', fontsize=14, fontweight='bold', pad=20)
ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
ax.grid(axis='y', alpha=0.3)

# Agregar valores
for bar, mejora in zip(bars, mejoras):
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height,
            f'{mejora:.1f}%',
            ha='center', va='bottom' if mejora > 0 else 'top', 
            fontsize=10, fontweight='bold')

plt.tight_layout()
plt.savefig(f"{REPORTS_DIR}/03_improvement_percentage.png", dpi=300, bbox_inches='tight')
logger.info(f"✅ Gráfica 3 guardada: {REPORTS_DIR}/03_improvement_percentage.png")
plt.close()

# ============================================================================
# TABLA COMPARATIVA FINAL
# ============================================================================
logger.info("\nGenerando tabla comparativa final...")

tabla_comparativa = pd.DataFrame({
    'Modelo': modelos,
    'F1 Original': [f"{f:.4f}" for f in f1_original],
    'F1 Optimizado': [f"{f:.4f}" for f in f1_optimizado],
    'Mejora (%)': [f"{m:.2f}%" for m in mejoras],
    'Umbral Óptimo': [
        f"{threshold_rf:.4f}",
        f"{threshold_xgb:.4f}",
        f"{threshold_svm:.4f}",
        f"{threshold_dnn:.4f}",
        f"{threshold_weighted:.4f}"
    ]
})

tabla_comparativa.to_csv(f"{REPORTS_DIR}/04_tabla_comparativa_final.csv", index=False)
logger.info(f"✅ Tabla guardada: {REPORTS_DIR}/04_tabla_comparativa_final.csv")

logger.info("\n" + tabla_comparativa.to_string(index=False))

# ============================================================================
# RESUMEN FINAL
# ============================================================================
logger.info("\n" + "="*80)
logger.info("✅ OPTIMIZACIÓN TIER 1 COMPLETADA EXITOSAMENTE")
logger.info("="*80)
logger.info("\nArchivos generados:")
logger.info(f"  📁 {MODELS_DIR}/optimized_thresholds.json - Configuración optimizada")
logger.info(f"  📊 {REPORTS_DIR}/01_f1_score_comparison.png - Comparación F1-Score")
logger.info(f"  📊 {REPORTS_DIR}/02_precision_recall_curves.png - Curvas Precision-Recall")
logger.info(f"  📊 {REPORTS_DIR}/03_improvement_percentage.png - Mejora porcentual")
logger.info(f"  📋 {REPORTS_DIR}/04_tabla_comparativa_final.csv - Tabla comparativa")

logger.info("\n" + "="*80)
logger.info("🎉 ¡LISTO PARA TU TESIS!")
logger.info("="*80)
logger.info("\nPróximos pasos:")
logger.info("1. Revisa las gráficas en reports/")
logger.info("2. Incluye las gráficas en tu documento (Sección 6)")
logger.info("3. Cita los umbrales óptimos en la metodología")
logger.info("4. Menciona las mejoras TIER 2-4 como trabajo futuro")