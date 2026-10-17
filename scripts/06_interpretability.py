#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 06_interpretability.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
METODOLOGÍA: CRISP-DM - Fase 5 (Evaluación - Interpretabilidad)
AUTOR: Ramirez Mendez, Juan Aldair
FECHA: 2026
=============================================================================
DESCRIPCIÓN:
    Implementa técnicas de interpretabilidad (SHAP y LIME) descritas en la
    Sección 3.7 del documento. Genera explicaciones globales y locales para
    validar la robustez y confiabilidad del sistema híbrido.
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
import matplotlib.pyplot as plt
import seaborn as sns

# SHAP para explicaciones globales y locales
import shap

# LIME para explicaciones locales alternativas
import lime
import lime.lime_tabular

# TensorFlow / Keras
import tensorflow as tf

# =========================================================================
# CONFIGURACIÓN INICIAL
# =========================================================================
load_dotenv()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

MODELS_DIR = Path("models_saved")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "interpretability.log", encoding="utf-8"),
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
    """Carga el conjunto de prueba desde PostgreSQL."""
    logger.info("Conectando a PostgreSQL para cargar datos de prueba...")
    engine = create_engine(DATABASE_URL)
    
    df_test = pd.read_sql("SELECT * FROM test_cleaned_original", engine)
    
    X_test = df_test.drop(columns=['risk_label'])
    y_test = df_test['risk_label']
    
    logger.info(f"Datos de prueba cargados. Shape: {X_test.shape}")
    return X_test, y_test


def load_base_models():
    """Carga los modelos previamente entrenados."""
    logger.info("Cargando modelos base desde disco...")
    
    rf = joblib.load(MODELS_DIR / "random_forest_model.pkl")
    xgb_model = joblib.load(MODELS_DIR / "xgboost_model.pkl")
    
    # Suprimir warnings de TensorFlow
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
    dnn_model = tf.keras.models.load_model(MODELS_DIR / "dnn_model.keras")
    
    logger.info("✅ Modelos cargados exitosamente.")
    return rf, xgb_model, dnn_model


# =========================================================================
# ANÁLISIS SHAP (Sección 3.7)
# =========================================================================

def shap_analysis_tree_models(X_test, rf, xgb_model):
    """
    Análisis SHAP para modelos basados en árboles (RF y XGBoost).
    SHAP es exacto y rápido para estos modelos.
    """
    logger.info("\n" + "="*80)
    logger.info("ANÁLISIS SHAP - MODELOS BASADOS EN ÁRBOLES")
    logger.info("="*80)
    
    # Usar una muestra representativa para SHAP (1000 instancias)
    sample_size = min(1000, len(X_test))
    X_sample = X_test.sample(n=sample_size, random_state=42)
    
    # =========================================================================
    # Random Forest - SHAP
    # =========================================================================
    logger.info("\n[1/2] Generando explicaciones SHAP para Random Forest...")
    
    explainer_rf = shap.TreeExplainer(rf)
    shap_values_rf = explainer_rf.shap_values(X_sample)
    
    # Para Random Forest con clasificación binaria, shap_values puede ser:
    # - Una lista de 2 arrays [clase_0, clase_1]
    # - Un array 3D (n_samples, n_features, n_classes)
    # Necesitamos extraer los valores para la clase 1 (fraude)
    
    if isinstance(shap_values_rf, list):
        # Formato: lista de arrays [clase_0, clase_1]
        shap_values_rf_class1 = shap_values_rf[1]
    elif isinstance(shap_values_rf, np.ndarray):
        if shap_values_rf.ndim == 3:
            # Formato: array 3D (n_samples, n_features, n_classes)
            shap_values_rf_class1 = shap_values_rf[:, :, 1]
        else:
            # Formato: array 2D (n_samples, n_features) - solo una clase
            shap_values_rf_class1 = shap_values_rf
    else:
        raise ValueError(f"Formato inesperado de shap_values: {type(shap_values_rf)}")
    
    # Verificar dimensiones
    logger.info(f"   Dimensiones de shap_values_rf_class1: {shap_values_rf_class1.shape}")
    logger.info(f"   Dimensiones de X_sample: {X_sample.shape}")
    
    # 1. Summary Plot (Importancia global)
    logger.info("   Generando Summary Plot (importancia global)...")
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values_rf_class1, X_sample, show=False, max_display=15)
    plt.title('SHAP Summary Plot - Random Forest\nImportancia Global de Características', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_summary_random_forest.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("   ✅ Summary Plot guardado: reports/shap_summary_random_forest.png")
    
    # 2. Bar Plot (Importancia promedio)
    logger.info("   Generando Bar Plot (importancia promedio)...")
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values_rf_class1, X_sample, plot_type="bar", show=False, max_display=15)
    plt.title('SHAP Feature Importance - Random Forest\nContribución Promedio al Valor de Predicción', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_importance_random_forest.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("   ✅ Bar Plot guardado: reports/shap_importance_random_forest.png")
    
    # 3. Dependence Plot (Interacción entre características)
    logger.info("   Generando Dependence Plot (interacción de características)...")
    # Identificar la característica más importante
    mean_abs_shap = np.abs(shap_values_rf_class1).mean(axis=0)
    top_feature_idx = np.argmax(mean_abs_shap)
    top_feature_name = X_sample.columns[top_feature_idx]
    
    # Para dependence_plot, necesitamos asegurar que las dimensiones sean correctas
    try:
        plt.figure(figsize=(10, 6))
        shap.dependence_plot(top_feature_idx, shap_values_rf_class1, X_sample, show=False)
        plt.title(f'SHAP Dependence Plot - Random Forest\nInteracción de {top_feature_name}', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(REPORTS_DIR / "shap_dependence_random_forest.png", dpi=300, bbox_inches='tight')
        plt.close()
        logger.info(f"   ✅ Dependence Plot guardado: reports/shap_dependence_random_forest.png")
    except Exception as e:
        logger.warning(f"   ⚠️  No se pudo generar Dependence Plot: {str(e)}")
        logger.info("   Continuando con los siguientes análisis...")
    
    # =========================================================================
    # XGBoost - SHAP
    # =========================================================================
    logger.info("\n[2/2] Generando explicaciones SHAP para XGBoost...")
    
    explainer_xgb = shap.TreeExplainer(xgb_model)
    shap_values_xgb = explainer_xgb.shap_values(X_sample)
    
    # XGBoost con XGBClassifier devuelve un array 2D directamente
    if isinstance(shap_values_xgb, list):
        shap_values_xgb = shap_values_xgb[1]
    elif isinstance(shap_values_xgb, np.ndarray) and shap_values_xgb.ndim == 3:
        shap_values_xgb = shap_values_xgb[:, :, 1]
    
    # 1. Summary Plot
    logger.info("   Generando Summary Plot (importancia global)...")
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values_xgb, X_sample, show=False, max_display=15)
    plt.title('SHAP Summary Plot - XGBoost\nImportancia Global de Características', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_summary_xgboost.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("   ✅ Summary Plot guardado: reports/shap_summary_xgboost.png")
    
    # 2. Bar Plot
    logger.info("   Generando Bar Plot (importancia promedio)...")
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values_xgb, X_sample, plot_type="bar", show=False, max_display=15)
    plt.title('SHAP Feature Importance - XGBoost\nContribución Promedio al Valor de Predicción', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_importance_xgboost.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("   ✅ Bar Plot guardado: reports/shap_importance_xgboost.png")
    
    # =========================================================================
    # Exportar valores SHAP a CSV para análisis adicional
    # =========================================================================
    logger.info("\n   Exportando valores SHAP a CSV...")
    shap_df_rf = pd.DataFrame(shap_values_rf_class1, columns=X_sample.columns)
    shap_df_rf.to_csv(REPORTS_DIR / "shap_values_random_forest.csv", index=False)
    
    shap_df_xgb = pd.DataFrame(shap_values_xgb, columns=X_sample.columns)
    shap_df_xgb.to_csv(REPORTS_DIR / "shap_values_xgboost.csv", index=False)
    
    logger.info("   ✅ Valores SHAP exportados a reports/shap_values_*.csv")
    
    # =========================================================================
    # Resumen de características más importantes
    # =========================================================================
    logger.info("\n" + "-"*80)
    logger.info("TOP 10 CARACTERÍSTICAS MÁS IMPORTANTES (SHAP)")
    logger.info("-"*80)
    
    # Random Forest
    rf_importance = pd.DataFrame({
        'Feature': X_sample.columns,
        'Mean_Abs_SHAP': np.abs(shap_values_rf_class1).mean(axis=0)
    }).sort_values('Mean_Abs_SHAP', ascending=False)
    
    logger.info("\nRandom Forest:")
    for idx, row in rf_importance.head(10).iterrows():
        logger.info(f"   {row['Feature']}: {row['Mean_Abs_SHAP']:.4f}")
    
    # XGBoost
    xgb_importance = pd.DataFrame({
        'Feature': X_sample.columns,
        'Mean_Abs_SHAP': np.abs(shap_values_xgb).mean(axis=0)
    }).sort_values('Mean_Abs_SHAP', ascending=False)
    
    logger.info("\nXGBoost:")
    for idx, row in xgb_importance.head(10).iterrows():
        logger.info(f"   {row['Feature']}: {row['Mean_Abs_SHAP']:.4f}")


def shap_analysis_dnn(X_test, dnn_model):
    """
    Análisis SHAP para Red Neuronal Profunda (DNN).
    Usa DeepExplainer para aproximación eficiente.
    """
    logger.info("\n" + "="*80)
    logger.info("ANÁLISIS SHAP - RED NEURONAL PROFUNDA (DNN)")
    logger.info("="*80)
    
    # Usar una muestra más pequeña para DNN (500 instancias)
    sample_size = min(500, len(X_test))
    X_sample = X_test.sample(n=sample_size, random_state=42)
    
    logger.info(f"\nGenerando explicaciones SHAP para DNN (muestra: {sample_size} instancias)...")
    logger.info("   Esto puede tomar 1-2 minutos...")
    
    # DeepExplainer para redes neuronales
    # Usamos datos de fondo (background data) para la aproximación
    background_data = X_test.sample(n=100, random_state=42).values
    
    explainer_dnn = shap.DeepExplainer(dnn_model, background_data)
    shap_values_dnn = explainer_dnn.shap_values(X_sample.values)
    
    # CORRECCIÓN: DeepExplainer para modelos con salida sigmoid devuelve array 3D (n_samples, n_features, 1)
    # Para clasificación binaria con una sola neurona de salida, solo existe el índice 0
    if isinstance(shap_values_dnn, list):
        # Formato: lista de arrays
        shap_values_dnn = shap_values_dnn[0]
    
    if isinstance(shap_values_dnn, np.ndarray):
        if shap_values_dnn.ndim == 3:
            # Formato: array 3D (n_samples, n_features, n_outputs)
            # Para sigmoid con 1 neurona, solo hay 1 output, extraer índice 0
            if shap_values_dnn.shape[2] == 1:
                shap_values_dnn = shap_values_dnn[:, :, 0]
            else:
                # Si hay múltiples outputs, extraer el último (clase positiva)
                shap_values_dnn = shap_values_dnn[:, :, -1]
        elif shap_values_dnn.ndim == 2:
            # Formato: array 2D (n_samples, n_features) - ya está correcto
            pass
    
    # Verificar dimensiones finales
    logger.info(f"   Dimensiones finales de shap_values_dnn: {shap_values_dnn.shape}")
    
    # 1. Summary Plot
    logger.info("   Generando Summary Plot (importancia global)...")
    plt.figure(figsize=(12, 8))
    shap.summary_plot(shap_values_dnn, X_sample, show=False, max_display=15)
    plt.title('SHAP Summary Plot - Red Neuronal Profunda (DNN)\nImportancia Global de Características', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_summary_dnn.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("   ✅ Summary Plot guardado: reports/shap_summary_dnn.png")
    
    # 2. Bar Plot
    logger.info("   Generando Bar Plot (importancia promedio)...")
    plt.figure(figsize=(10, 8))
    shap.summary_plot(shap_values_dnn, X_sample, plot_type="bar", show=False, max_display=15)
    plt.title('SHAP Feature Importance - DNN\nContribución Promedio al Valor de Predicción', fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "shap_importance_dnn.png", dpi=300, bbox_inches='tight')
    plt.close()
    logger.info("   ✅ Bar Plot guardado: reports/shap_importance_dnn.png")
    
    # Exportar valores SHAP
    logger.info("   Exportando valores SHAP a CSV...")
    shap_df_dnn = pd.DataFrame(shap_values_dnn, columns=X_sample.columns)
    shap_df_dnn.to_csv(REPORTS_DIR / "shap_values_dnn.csv", index=False)
    logger.info("   ✅ Valores SHAP exportados a reports/shap_values_dnn.csv")
    
    # Resumen de características más importantes para DNN
    logger.info("\n" + "-"*80)
    logger.info("TOP 10 CARACTERÍSTICAS MÁS IMPORTANTES (SHAP - DNN)")
    logger.info("-"*80)
    
    dnn_importance = pd.DataFrame({
        'Feature': X_sample.columns,
        'Mean_Abs_SHAP': np.abs(shap_values_dnn).mean(axis=0)
    }).sort_values('Mean_Abs_SHAP', ascending=False)
    
    for idx, row in dnn_importance.head(10).iterrows():
        logger.info(f"   {row['Feature']}: {row['Mean_Abs_SHAP']:.4f}")

# =========================================================================
# ANÁLISIS LIME (Sección 3.7)
# =========================================================================

def lime_analysis(X_test, y_test, rf, xgb_model):
    """
    Análisis LIME para explicaciones locales de instancias específicas.
    Se enfoca en instancias fraudulentas para entender por qué fueron clasificadas como tal.
    """
    logger.info("\n" + "="*80)
    logger.info("ANÁLISIS LIME - EXPLICACIONES LOCALES")
    logger.info("="*80)
    
    # Identificar instancias fraudulentas en el conjunto de prueba
    fraud_indices = y_test[y_test == 1].index
    
    if len(fraud_indices) == 0:
        logger.warning("No se encontraron instancias fraudulentas en el conjunto de prueba.")
        return
    
    # Seleccionar 3 instancias fraudulentas para análisis LIME
    num_instances = min(3, len(fraud_indices))
    selected_indices = fraud_indices[:num_instances]
    
    logger.info(f"\nAnalizando {num_instances} instancias fraudulentas con LIME...")
    
    # =========================================================================
    # LIME para Random Forest
    # =========================================================================
    logger.info("\n[1/2] Generando explicaciones LIME para Random Forest...")
    
    # Crear explicador LIME
    lime_explainer_rf = lime.lime_tabular.LimeTabularExplainer(
        X_test.values,
        feature_names=X_test.columns.tolist(),
        class_names=['Legítima (0)', 'Fraudulenta (1)'],
        mode='classification',
        random_state=42
    )
    
    for i, idx in enumerate(selected_indices):
        logger.info(f"   Analizando instancia fraudulenta #{i+1} (índice: {idx})...")
        
        try:
            # Generar explicación LIME - pasar como array numpy
            instance = X_test.loc[idx].values
            
            exp = lime_explainer_rf.explain_instance(
                instance,
                rf.predict_proba,
                top_labels=2,
                num_features=10
            )
            
            # Guardar explicación como figura
            plt.figure(figsize=(10, 6))
            fig = exp.as_pyplot_figure(label=1)  # label=1 para clase fraudulenta
            plt.title(f'LIME Explanation - Random Forest\nInstancia Fraudulenta #{i+1} (Índice: {idx})', 
                     fontsize=12, fontweight='bold')
            plt.tight_layout()
            plt.savefig(REPORTS_DIR / f"lime_rf_fraud_instance_{i+1}.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"   ✅ Explicación guardada: reports/lime_rf_fraud_instance_{i+1}.png")
            
        except Exception as e:
            logger.error(f"   ❌ Error al generar explicación LIME para instancia {i+1}: {str(e)}")
            continue
    
    # =========================================================================
    # LIME para XGBoost
    # =========================================================================
    logger.info("\n[2/2] Generando explicaciones LIME para XGBoost...")
    
    lime_explainer_xgb = lime.lime_tabular.LimeTabularExplainer(
        X_test.values,
        feature_names=X_test.columns.tolist(),
        class_names=['Legítima (0)', 'Fraudulenta (1)'],
        mode='classification',
        random_state=42
    )
    
    for i, idx in enumerate(selected_indices):
        logger.info(f"   Analizando instancia fraudulenta #{i+1} (índice: {idx})...")
        
        try:
            instance = X_test.loc[idx].values
            
            exp = lime_explainer_xgb.explain_instance(
                instance,
                xgb_model.predict_proba,
                top_labels=2,
                num_features=10
            )
            
            plt.figure(figsize=(10, 6))
            fig = exp.as_pyplot_figure(label=1)  # label=1 para clase fraudulenta
            plt.title(f'LIME Explanation - XGBoost\nInstancia Fraudulenta #{i+1} (Índice: {idx})', 
                     fontsize=12, fontweight='bold')
            plt.tight_layout()
            plt.savefig(REPORTS_DIR / f"lime_xgb_fraud_instance_{i+1}.png", dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"   ✅ Explicación guardada: reports/lime_xgb_fraud_instance_{i+1}.png")
            
        except Exception as e:
            logger.error(f"   ❌ Error al generar explicación LIME para instancia {i+1}: {str(e)}")
            continue

# =========================================================================
# FUNCIÓN PRINCIPAL
# =========================================================================

def main():
    logger.info("="*80)
    logger.info("INICIANDO FASE 5: EVALUACIÓN - INTERPRETABILIDAD (CRISP-DM)")
    logger.info("="*80)
    
    # 1. Cargar datos
    X_test, y_test = load_data_from_db()
    
    # 2. Cargar modelos
    rf, xgb_model, dnn_model = load_base_models()
    
    # 3. Análisis SHAP para modelos basados en árboles
    shap_analysis_tree_models(X_test, rf, xgb_model)
    
    # 4. Análisis SHAP para DNN
    shap_analysis_dnn(X_test, dnn_model)
    
    # 5. Análisis LIME para explicaciones locales
    lime_analysis(X_test, y_test, rf, xgb_model)
    
    # 6. Resumen final
    logger.info("\n" + "="*80)
    logger.info("ANÁLISIS DE INTERPRETABILIDAD COMPLETADO EXITOSAMENTE")
    logger.info("="*80)
    logger.info("\nArchivos generados en reports/:")
    logger.info("   - SHAP Summary Plots (importancia global)")
    logger.info("   - SHAP Bar Plots (contribución promedio)")
    logger.info("   - SHAP Dependence Plots (interacciones) - si fue posible generarlos")
    logger.info("   - SHAP Values CSV (valores numéricos)")
    logger.info("   - LIME Explanations (explicaciones locales)")
    logger.info("\nPróximos pasos:")
    logger.info("   1. Revisar las visualizaciones en reports/")
    logger.info("   2. Analizar las características más importantes")
    logger.info("   3. Redactar la Sección 6 (Resultados y Discusión) de tu tesis")
    logger.info("="*80)


if __name__ == "__main__":
    main()