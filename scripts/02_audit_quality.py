#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 02_audit_quality.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
METODOLOGÍA: CRISP-DM - Fase 2.3 (Análisis Exploratorio de los Datos)
AUTOR: Ramirez Mendez, Juan Aldair
FECHA: 2026
=============================================================================
DESCRIPCIÓN:
    Realiza el Análisis Exploratorio de Datos (EDA) requerido en la 
    Sección 5.3.2 del documento. Genera estadísticas descriptivas y 
    visualizaciones clave, incluyendo un análisis preliminar de importancia 
    de características con Random Forest para validar las hipótesis del documento.
=============================================================================
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# =========================================================================
# CONFIGURACIÓN DEL LOGGING Y RUTAS
# =========================================================================
LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

REPORTS_DIR = Path("reports")
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "audit_quality.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATA_FILE = Path("data/raw/financial_fraud_risk_raw.parquet")


def load_data() -> pd.DataFrame:
    """Carga el dataset desde el archivo Parquet."""
    if not DATA_FILE.exists():
        logger.error(f"No se encontró el archivo: {DATA_FILE}")
        logger.error("Ejecuta primero: python scripts/01_download_dataset.py")
        sys.exit(1)
    
    logger.info(f"Cargando dataset desde: {DATA_FILE}")
    df = pd.read_parquet(DATA_FILE)
    logger.info(f"Dataset cargado. Shape: {df.shape}")
    return df


def generate_eda_plots(df: pd.DataFrame):
    """
    Genera las visualizaciones clave mencionadas en la Sección 5.3.2 del documento.
    """
    logger.info("Generando visualizaciones de Análisis Exploratorio (EDA)...")
    
    # Configurar estilo de seaborn
    sns.set_theme(style="whitegrid")
    
    # 1. Distribución de Clases (Sección 5.3.3)
    logger.info("  - Generando gráfico de distribución de clases...")
    plt.figure(figsize=(8, 5))
    class_counts = df['risk_label'].value_counts()
    sns.barplot(x=class_counts.index.map({0: 'Legítima (0)', 1: 'Fraudulenta (1)'}), 
                y=class_counts.values, palette=['#2ecc71', '#e74c3c'])
    plt.title('Distribución de Clases (Desbalance 98.5% vs 1.5%)', fontsize=14)
    plt.ylabel('Número de Transacciones')
    plt.xticks(rotation=0)
    for i, v in enumerate(class_counts.values):
        plt.text(i, v + 1000, f"{v:,}\n({v/len(df)*100:.1f}%)", ha='center', va='bottom', fontweight='bold')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "01_class_distribution.png", dpi=300)
    plt.close()

    # 2. Relación Monto vs Riesgo (Sección 5.3.2)
    logger.info("  - Generando boxplot de Monto de Transacción vs Riesgo...")
    plt.figure(figsize=(10, 6))
    # Usamos log1p para visualizar mejor la distribución debido a outliers en montos
    df['log_transaction_amount'] = pd.to_numeric(df['transaction_amount'], errors='coerce').apply(lambda x: np.log1p(x) if pd.notnull(x) else 0)
    
    sns.boxplot(data=df, x='risk_label', y='log_transaction_amount', palette=['#2ecc71', '#e74c3c'])
    plt.title('Distribución del Monto de Transacción (Log) por Tipo de Operación', fontsize=14)
    plt.xlabel('Risk Label (0: Legítima, 1: Fraudulenta)')
    plt.ylabel('Log(Monto de Transacción + 1)')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "02_amount_vs_risk.png", dpi=300)
    plt.close()

    # 3. Importancia de Características con Random Forest (Sección 5.3.2)
    logger.info("  - Ejecutando Random Forest rápido para importancia de características...")
    # Preparar datos para RF (codificar categóricas rápidamente)
    df_ml = df.copy()
    le = LabelEncoder()
    for col in df_ml.select_dtypes(include=['object', 'category']).columns:
        df_ml[col] = le.fit_transform(df_ml[col].astype(str))
    
    X = df_ml.drop(columns=['risk_label', 'transaction_id', 'customer_id', 'log_transaction_amount'])
    y = df_ml['risk_label']
    
    # Usamos una muestra para que sea rápido en 16GB RAM (20,000 registros son suficientes para estimar importancia)
    sample_size = 20000
    X_sample = X.sample(n=sample_size, random_state=42)
    y_sample = y.loc[X_sample.index]
    
    rf = RandomForestClassifier(n_estimators=50, max_depth=10, random_state=42, n_jobs=-1)
    rf.fit(X_sample, y_sample)
    
    # Obtener importancias
    importances = rf.feature_importances_
    feature_names = X.columns
    feature_importance_df = pd.DataFrame({'Feature': feature_names, 'Importance': importances})
    feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False).head(10)
    
    logger.info("  - Top 5 características más importantes:")
    for _, row in feature_importance_df.head(5).iterrows():
        logger.info(f"      {row['Feature']}: {row['Importance']:.4f}")
    
    # Graficar
    plt.figure(figsize=(10, 6))
    sns.barplot(data=feature_importance_df, x='Importance', y='Feature', palette='Blues_r')
    plt.title('Importancia de Características (Random Forest - Muestra)', fontsize=14)
    plt.xlabel('Importancia (Gini Impurity Decrease)')
    plt.ylabel('Característica')
    plt.tight_layout()
    plt.savefig(REPORTS_DIR / "03_feature_importance_rf.png", dpi=300)
    plt.close()
    
    logger.info(f"✅ Visualizaciones guardadas en el directorio: {REPORTS_DIR.resolve()}")


def main():
    logger.info("=" * 80)
    logger.info("INICIANDO ANÁLISIS EXPLORATORIO DE DATOS (CRISP-DM FASE 2.3)")
    logger.info("=" * 80)
    
    # 1. Cargar datos
    df = load_data()
    
    # 2. Resumen estadístico rápido
    logger.info("\nResumen de tipos de datos:")
    logger.info(f"Variables numéricas: {len(df.select_dtypes(include=['number']).columns)}")
    logger.info(f"Variables categóricas: {len(df.select_dtypes(include=['object', 'category']).columns)}")
    
    logger.info("\nEstadísticas descriptivas de variables numéricas clave:")
    numeric_cols = ['transaction_amount', 'customer_risk_score', 'account_age_days', 'previous_chargebacks']
    logger.info(f"\n{df[numeric_cols].describe().round(2).to_string()}")
    
    # 3. Generar gráficas
    generate_eda_plots(df)
    
    logger.info("\n" + "=" * 80)
    logger.info("ANÁLISIS EXPLORATORIO COMPLETADO EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info("Próximos pasos:")
    logger.info("    1. Revisar las gráficas generadas en la carpeta 'reports/'")
    logger.info("    2. Ejecutar: python scripts/03_clean_data.py (Fase 3: Preparación de datos)")


if __name__ == "__main__":
    import numpy as np  # Importado aquí para asegurar compatibilidad
    main()
