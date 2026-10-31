#!/usr/bin/env python3
"""
=============================================================================
SCRIPT: 00_validate_pipeline.py
PROYECTO: Sistema Híbrido de Detección de Fraude Financiero
OBJETIVO: Procedimiento de validación post-ejecución para verificar el estado 
          de la base de datos, modelos (artifacts) y reportes en la terminal.
=============================================================================
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd

# Configuración inicial
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models_saved"
REPORTS_DIR = BASE_DIR / "reports"

def print_header(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def check_database():
    """Valida la integridad y estado de los DataFrames en PostgreSQL."""
    print_header("1. VALIDACIÓN DE BASE DE DATOS (DATAFRAMES)")
    
    db_url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Query para obtener conteos y distribución de clases
            query = text("""
                SELECT 'train_cleaned_balanced' as tabla, COUNT(*) as total, 
                       SUM(CASE WHEN risk_label = 1 THEN 1 ELSE 0 END) as fraude
                FROM train_cleaned_balanced
                UNION ALL
                SELECT 'test_cleaned_original', COUNT(*), SUM(CASE WHEN risk_label = 1 THEN 1 ELSE 0 END)
                FROM test_cleaned_original;
            """)
            df_status = pd.read_sql(query, conn)
            
            print(f"{'Tabla':<25} | {'Total Filas':<12} | {'Fraudes (1)':<12} | {'Legítimas (0)':<12}")
            print("-" * 70)
            for _, row in df_status.iterrows():
                legit = row['total'] - row['fraude']
                print(f"{row['tabla']:<25} | {row['total']:<12,} | {row['fraude']:<12,} | {legit:<12,}")
                
            # Validar metadata
            try:
                meta_query = text("SELECT COUNT(*) as count FROM crisp_dm_metadata;")
                meta_count = pd.read_sql(meta_query, conn)['count'][0]
                print(f"\n[OK] Tabla crisp_dm_metadata: {meta_count} registros de trazabilidad.")
            except Exception:
                print("\n[WARN] Tabla crisp_dm_metadata no encontrada o vacía.")
                
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a PostgreSQL: {e}")
        print("Verifica que el servicio esté activo y el archivo .env sea correcto.")

def check_artifacts():
    """Valida la existencia de los modelos guardados (artifacts)."""
    print_header("2. VALIDACIÓN DE MODELOS (ARTIFACTS)")
    
    if not MODELS_DIR.exists():
        print(f"[ERROR] El directorio {MODELS_DIR} no existe.")
        return

    # Buscar archivos .pkl, .keras, .json
    pkl_files = list(MODELS_DIR.glob("*.pkl"))
    keras_files = list(MODELS_DIR.glob("*.keras"))
    json_files = list(MODELS_DIR.glob("*.json"))
    
    print(f"📁 Directorio: {MODELS_DIR}")
    print(f"   - Modelos Scikit-Learn/XGBoost (.pkl): {len(pkl_files)}")
    for f in pkl_files: print(f"      -> {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    
    print(f"   - Modelos Keras/TensorFlow (.keras): {len(keras_files)}")
    for f in keras_files: print(f"      -> {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    
    print(f"   - Configuraciones (.json): {len(json_files)}")
    for f in json_files: print(f"      -> {f.name}")

def check_reports():
    """Valida la generación de visualizaciones y CSVs de reporte."""
    print_header("3. VALIDACIÓN DE REPORTES Y VISUALIZACIONES")
    
    if not REPORTS_DIR.exists():
        print(f"[ERROR] El directorio {REPORTS_DIR} no existe.")
        return

    png_files = list(REPORTS_DIR.glob("*.png"))
    csv_files = list(REPORTS_DIR.glob("*.csv"))
    
    print(f"📁 Directorio: {REPORTS_DIR}")
    print(f"   - Gráficas generadas (.png): {len(png_files)}")
    print(f"   - Tablas de resultados (.csv): {len(csv_files)}")

def main():
    print("\n" + "*"*80)
    print(" 🚀 PROCEDIMIENTO DE VALIDACIÓN POST-EJECUCIÓN - PIPELINE CRISP-DM")
    print("*"*80)
    
    check_database()
    check_artifacts()
    check_reports()
    
    print("\n" + "="*80)
    print(" ✅ VALIDACIÓN COMPLETADA. Revisa los estados anteriores antes de continuar.")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()