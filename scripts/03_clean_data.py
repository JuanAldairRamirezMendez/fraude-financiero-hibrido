#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 03_clean_data.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
METODOLOGÍA: CRISP-DM - Fase 3 (Preparación de los Datos)
AUTOR: Ramirez Mendez, Juan Aldair
FECHA: 2026
=============================================================================
DESCRIPCIÓN:
    Ejecuta el pipeline de preprocesamiento descrito en las secciones 
    5.4.1 a 5.4.4 del documento. Incluye limpieza, codificación, división 
    estratificada, balanceo con SMOTE (solo en train) y almacenamiento 
    en base de datos PostgreSQL.
=============================================================================
"""

import sys
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from dotenv import load_dotenv
import os

# =========================================================================
# CONFIGURACIÓN INICIAL
# =========================================================================
load_dotenv()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "clean_data.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

DATA_FILE = Path("data/raw/financial_fraud_risk_raw.parquet")

# Configuración de Base de Datos
DB_USER = os.getenv("DB_USER", "fraud_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "tu_password_seguro")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "fraud_detection")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# =========================================================================
# FUNCIONES PRINCIPALES
# =========================================================================

def load_data() -> pd.DataFrame:
    """Carga el dataset crudo."""
    if not DATA_FILE.exists():
        logger.error(f"No se encontró el archivo: {DATA_FILE}")
        sys.exit(1)
    logger.info(f"Cargando dataset desde: {DATA_FILE}")
    return pd.read_parquet(DATA_FILE)


def preprocess_and_balance(df: pd.DataFrame):
    """
    Aplica el pipeline de preprocesamiento CRISP-DM (Secciones 5.4.1 - 5.4.4).
    """
    logger.info("=" * 80)
    logger.info("INICIANDO PREPARACIÓN DE DATOS (CRISP-DM FASE 3)")
    logger.info("=" * 80)

    # 5.4.1 Limpieza y selección de variables
    logger.info("\n[1/5] Limpieza y selección de variables (Sección 5.4.1)...")
    cols_to_drop = ['transaction_id', 'customer_id']
    existing_cols_to_drop = [col for col in cols_to_drop if col in df.columns]
    
    df_clean = df.drop(columns=existing_cols_to_drop)
    logger.info(f"    Columnas identificadoras eliminadas: {existing_cols_to_drop}")
    logger.info(f"    Variables predictoras restantes: {len(df_clean.columns) - 1} (excluyendo target)")

    # Separar X e y
    X = df_clean.drop(columns=['risk_label'])
    y = df_clean['risk_label']

    # Identificar tipos de columnas
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = X.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
    
    logger.info(f"    Variables numéricas: {len(numeric_features)}")
    logger.info(f"    Variables categóricas: {len(categorical_features)}")

    # 5.4.3 División de entrenamiento y prueba (80/20 estratificado)
    logger.info("\n[2/5] División de datos 80/20 estratificada (Sección 5.4.3)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"    Train set: {len(X_train):,} registros ({len(y_train[y_train==1]):,} fraudes)")
    logger.info(f"    Test set:  {len(X_test):,} registros ({len(y_test[y_test==1]):,} fraudes)")

    # 5.4.2 Codificación y estandarización + 5.4.4 SMOTE (Pipeline seguro)
    logger.info("\n[3/5] Construyendo pipeline de preprocesamiento y SMOTE (Secciones 5.4.2 y 5.4.4)...")
    
    # Preprocesador: One-Hot Encoding para categóricas, StandardScaler para numéricas
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', StandardScaler(), numeric_features),
            ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), categorical_features)
        ]
    )

    # Pipeline que aplica preprocesamiento y luego SMOTE *solo* a los datos de entrenamiento
    smote_pipeline = ImbPipeline(steps=[
        ('preprocessor', preprocessor),
        ('smote', SMOTE(random_state=42, k_neighbors=5))
    ])

    logger.info("    Aplicando transformación y SMOTE al conjunto de ENTRENAMIENTO...")
    X_train_balanced_array, y_train_balanced = smote_pipeline.fit_resample(X_train, y_train)
    
    # Obtener nombres de columnas después del One-Hot Encoding
    cat_encoder = smote_pipeline.named_steps['preprocessor'].named_transformers_['cat']
    cat_feature_names = cat_encoder.get_feature_names_out(categorical_features)
    final_feature_names = numeric_features + cat_feature_names.tolist()
    
    logger.info(f"    Total de características finales: {len(final_feature_names)}")

    # Para el conjunto de prueba, SOLO se aplica el preprocesador (NUNCA SMOTE)
    logger.info("    Aplicando SOLO preprocesamiento al conjunto de PRUEBA (sin SMOTE)...")
    X_test_clean_array = smote_pipeline.named_steps['preprocessor'].transform(X_test)

    # Reconstruir DataFrames para guardar en PostgreSQL
    df_train_final = pd.DataFrame(X_train_balanced_array, columns=final_feature_names)
    df_train_final['risk_label'] = y_train_balanced
    
    df_test_final = pd.DataFrame(X_test_clean_array, columns=final_feature_names)
    df_test_final['risk_label'] = y_test.values

    logger.info("\n[4/5] Resumen de conjuntos finales:")
    logger.info(f"    Train balanceado: {len(df_train_final):,} filas (Legítimas: {(df_train_final['risk_label']==0).sum():,}, Fraudulentas: {(df_train_final['risk_label']==1).sum():,})")
    logger.info(f"    Test original:    {len(df_test_final):,} filas (Legítimas: {(df_test_final['risk_label']==0).sum():,}, Fraudulentas: {(df_test_final['risk_label']==1).sum():,})")

    return df_train_final, df_test_final, final_feature_names


def save_to_postgres(df_train: pd.DataFrame, df_test: pd.DataFrame, feature_names: list):
    """
    Guarda las versiones limpias en PostgreSQL (Requisito del profesor).
    CORRECCIÓN: chunksize=1000 para evitar el límite de 65,535 parámetros de PostgreSQL.
    """
    logger.info("\n[5/5] Conectando y guardando en base de datos PostgreSQL...")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        # Probar conexión
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("    ✅ Conexión a PostgreSQL establecida exitosamente.")

        # Guardar datos con chunksize=1000 (47 cols * 1000 = 47,000 params < 65,535 límite)
        logger.info("    Guardando 'train_cleaned_balanced' (~157,600 filas)...")
        df_train.to_sql('train_cleaned_balanced', engine, if_exists='replace', index=False, method='multi', chunksize=1000)
        
        logger.info("    Guardando 'test_cleaned_original' (20,000 filas)...")
        df_test.to_sql('test_cleaned_original', engine, if_exists='replace', index=False, method='multi', chunksize=1000)
        
        # Guardar metadata del proceso
        metadata = {
            'step': 'Fase 3: Preparación de Datos',
            'train_rows': len(df_train),
            'test_rows': len(df_test),
            'total_features': len(feature_names),
            'smote_applied': True,
            'timestamp': pd.Timestamp.now().isoformat()
        }
        df_meta = pd.DataFrame([metadata])
        df_meta.to_sql('crisp_dm_metadata', engine, if_exists='append', index=False)
        
        logger.info("    ✅ Datos guardados exitosamente en PostgreSQL.")
        
    except Exception as e:
        logger.error(f"    ❌ Error al conectar o guardar en PostgreSQL: {str(e)}")
        raise

def main():
    logger.info("=" * 80)
    logger.info("SCRIPT DE PREPARACIÓN DE DATOS - FRAUDE FINANCIERO")
    logger.info("=" * 80)
    
    # 1. Cargar
    df = load_data()
    
    # 2. Preprocesar y balancear
    df_train, df_test, feature_names = preprocess_and_balance(df)
    
    # 3. Guardar en BD
    save_to_postgres(df_train, df_test, feature_names)
    
    logger.info("\n" + "=" * 80)
    logger.info("PREPARACIÓN DE DATOS COMPLETADA EXITOSAMENTE")
    logger.info("=" * 80)
    logger.info("Próximos pasos:")
    logger.info("    1. Verificar tablas en PostgreSQL (pgAdmin, DBeaver o psql)")
    logger.info("    2. Ejecutar: python scripts/04_train_models.py (Fase 4: Modelado)")


if __name__ == "__main__":
    main()