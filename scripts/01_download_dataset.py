#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 01_download_dataset.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
METODOLOGÍA: CRISP-DM - Fase 2.1 (Recolección de Datos)
AUTOR: Ramirez Mendez, Juan Aldair
FECHA: 2026
=============================================================================
DESCRIPCIÓN:
    Este script descarga el dataset "Financial Fraud Risk Dataset" desde
    Hugging Face y lo almacena localmente en formato Parquet para ser
    procesado en las fases siguientes de la metodología CRISP-DM.

DATASET:
    arun-gharami/lead-ai-fraud-detection-dataset-v2
    - 100,000 transacciones
    - 21 variables (20 características + 1 variable objetivo)
    - Desbalance: 98.5% legítimas vs 1.5% fraudulentas
    - Variable objetivo: risk_label (0 = legítima, 1 = fraudulenta)

ENTORNO DE EJECUCIÓN:
    CachyOS Linux | Python 3.10+ | i5 12400f | 16 GB RAM | RX 6700 XT
=============================================================================
"""

import sys
from pathlib import Path
from datetime import datetime
import logging

import pandas as pd
from datasets import load_dataset

# =========================================================================
# CONFIGURACIÓN DEL LOGGING
# =========================================================================
# Se configura el sistema de registro de eventos (logging) para dejar
# trazabilidad del proceso, requisito académico de la metodología CRISP-DM.

LOG_DIR = Path("logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "download_dataset.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# =========================================================================
# CONFIGURACIÓN DE RUTAS
# =========================================================================

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = DATA_DIR / "financial_fraud_risk_raw.parquet"

# =========================================================================
# CONSTANTES DEL DATASET ESPERADO
# =========================================================================
# Estos valores corresponden a la Sección 4.4 del documento oficial.

DATASET_NAME = "arun-gharami/lead-ai-fraud-detection-dataset-v2"
EXPECTED_ROWS = 100_000
EXPECTED_COLS = 21
TARGET_COLUMN = "risk_label"


# =========================================================================
# FUNCIONES PRINCIPALES
# =========================================================================

def download_dataset() -> pd.DataFrame:
    """
    Descarga el dataset desde Hugging Face y lo persiste en formato Parquet.

    Returns:
        pd.DataFrame: El dataset completo cargado en memoria.

    Raises:
        Exception: Si ocurre un error durante la descarga o el guardado.
    """
    logger.info("=" * 80)
    logger.info("INICIANDO DESCARGA DE DATASET")
    logger.info("=" * 80)
    logger.info(f"Dataset: {DATASET_NAME}")
    logger.info(f"Directorio de destino: {DATA_DIR.resolve()}")

    try:
        # Paso 1: Cargar dataset desde Hugging Face
        logger.info("")
        logger.info("[1/3] Descargando dataset desde Hugging Face...")
        logger.info("Tiempo estimado: 1-2 minutos según conexión a internet.")

        dataset = load_dataset(DATASET_NAME, split="train")

        logger.info("Dataset cargado en memoria correctamente.")
        logger.info(f"    Total de registros: {len(dataset):,}")
        logger.info(f"    Total de columnas: {len(dataset.column_names)}")

        # Paso 2: Convertir a DataFrame de pandas
        logger.info("")
        logger.info("[2/3] Convirtiendo a DataFrame de pandas...")
        df = dataset.to_pandas()

        logger.info("DataFrame creado correctamente.")
        logger.info(f"    Shape: {df.shape}")
        logger.info(f"    Columnas: {list(df.columns)}")

        # Paso 3: Guardar en formato Parquet
        logger.info("")
        logger.info("[3/3] Guardando en formato Parquet...")
        logger.info(f"    Archivo: {OUTPUT_FILE}")

        df.to_parquet(OUTPUT_FILE, engine="pyarrow", compression="snappy")

        file_size_mb = OUTPUT_FILE.stat().st_size / (1024 * 1024)
        logger.info("Archivo guardado exitosamente.")
        logger.info(f"    Tamaño: {file_size_mb:.2f} MB")

        # Verificación rápida de calidad (CRISP-DM Fase 2.3 preliminar)
        logger.info("")
        logger.info("[VERIFICACIÓN] Análisis preliminar de calidad...")
        logger.info(f"    Valores nulos totales: {df.isnull().sum().sum():,}")
        logger.info(f"    Filas duplicadas: {df.duplicated().sum():,}")

        # Análisis del desbalance de clases
        if TARGET_COLUMN in df.columns:
            class_dist = df[TARGET_COLUMN].value_counts()
            logger.info("")
            logger.info(f"    Distribución de clases ({TARGET_COLUMN}):")
            for cls, count in class_dist.items():
                pct = (count / len(df)) * 100
                logger.info(f"        Clase {cls}: {count:,} ({pct:.2f}%)")

            if len(class_dist) == 2:
                majority = class_dist.max()
                minority = class_dist.min()
                imbalance_ratio = majority / minority
                logger.info("")
                logger.info(f"    Ratio de desbalance: {imbalance_ratio:.1f}:1")
                logger.info("    Se confirma la necesidad de aplicar SMOTE (Sección 5.4.4).")

        logger.info("")
        logger.info("=" * 80)
        logger.info("DESCARGA COMPLETADA EXITOSAMENTE")
        logger.info("=" * 80)
        logger.info(f"Archivo guardado en: {OUTPUT_FILE.resolve()}")
        logger.info("")
        logger.info("Próximos pasos:")
        logger.info("    1. Ejecutar: python scripts/02_audit_quality.py")
        logger.info("    2. Revisar el log: logs/download_dataset.log")

        return df

    except Exception as e:
        logger.error("")
        logger.error(f"ERROR durante la descarga: {str(e)}")
        logger.error("Posibles causas:")
        logger.error("    - Conexión a internet inestable")
        logger.error("    - Dataset no disponible o renombrado en Hugging Face")
        logger.error("    - Permisos de escritura insuficientes en el directorio")
        raise


def verify_download() -> bool:
    """
    Verifica que el archivo descargado coincida con las especificaciones
    documentadas en la Sección 4.4 del proyecto.

    Returns:
        bool: True si la verificación es exitosa, False en caso contrario.
    """
    if not OUTPUT_FILE.exists():
        logger.error(f"Archivo no encontrado: {OUTPUT_FILE}")
        return False

    try:
        df = pd.read_parquet(OUTPUT_FILE)

        logger.info("")
        logger.info("[VERIFICACIÓN FINAL] Lectura del archivo Parquet")
        logger.info(f"    Shape: {df.shape}")
        logger.info(f"    Columnas: {len(df.columns)}")
        logger.info(f"    Memoria en RAM: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

        # Verificación de filas
        if len(df) == EXPECTED_ROWS:
            logger.info(f"    Coincide con el documento: {EXPECTED_ROWS:,} filas")
        else:
            logger.warning(
                f"    Diferencia en filas: {len(df):,} (esperado: {EXPECTED_ROWS:,})"
            )

        # Verificación de columnas
        if len(df.columns) == EXPECTED_COLS:
            logger.info(f"    Coincide con el documento: {EXPECTED_COLS} columnas")
        else:
            logger.warning(
                f"    Diferencia en columnas: {len(df.columns)} "
                f"(esperado: {EXPECTED_COLS})"
            )

        # Verificación de variable objetivo
        if TARGET_COLUMN in df.columns:
            logger.info(f"    Variable objetivo '{TARGET_COLUMN}' presente.")
        else:
            logger.error(f"    Variable objetivo '{TARGET_COLUMN}' NO encontrada.")
            return False

        return True

    except Exception as e:
        logger.error(f"Error al leer el archivo: {str(e)}")
        return False


# =========================================================================
# PUNTO DE ENTRADA
# =========================================================================

if __name__ == "__main__":
    logger.info("")
    logger.info("=" * 80)
    logger.info("SCRIPT DE DESCARGA DE DATASET - FRAUDE FINANCIERO")
    logger.info("=" * 80)
    logger.info(f"Ejecutado por: aldair@cachyos-aldair")
    logger.info(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("")

    try:
        df = download_dataset()

        if df is not None and verify_download():
            logger.info("")
            logger.info("Proceso completado. Puedes continuar con la Fase 2.3.")
        else:
            logger.error("")
            logger.error("La verificación falló. Revisa el log para más detalles.")
            sys.exit(1)

    except Exception:
        logger.exception("Se produjo un error no controlado durante la ejecución.")
        sys.exit(1)