# =============================================================================
# MAKEFILE - Sistema Híbrido de Detección de Fraude Financiero
# =============================================================================

.PHONY: setup install download audit clean train evaluate ensemble report pipeline clean-files test notebook help

# Variables
PYTHON := python3
VENV := venv
PIP := $(VENV)/bin/pip
PYTHON_VENV := $(VENV)/bin/python

# =============================================================================
# COMANDOS PRINCIPALES
# =============================================================================

## Configurar entorno virtual
setup:
	@echo "🔧 Configurando entorno virtual..."
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	@echo "✅ Entorno virtual configurado"
	@echo "💡 Activar con: source $(VENV)/bin/activate"

## Instalar dependencias
install:
	@echo "📦 Instalando dependencias..."
	$(PIP) install -r requirements.txt
	@echo "✅ Dependencias instaladas"

## Descargar dataset de Hugging Face
download:
	@echo "📥 Descargando dataset..."
	$(PYTHON_VENV) scripts/01_download_dataset.py
	@echo "✅ Dataset descargado"

## Auditoría de calidad de datos
audit:
	@echo "🔍 Ejecutando auditoría de calidad..."
	$(PYTHON_VENV) scripts/02_audit_quality.py
	@echo "✅ Auditoría completada"

## Limpieza y guardado en PostgreSQL
clean:
	@echo "🧹 Limpiando datos..."
	$(PYTHON_VENV) scripts/03_clean_data.py
	@echo "✅ Datos limpios y guardados en PostgreSQL"

## Entrenar todos los modelos
train:
	@echo "🤖 Entrenando modelos..."
	$(PYTHON_VENV) scripts/04_train_models.py
	@echo "✅ Modelos entrenados"

## Evaluar modelos
evaluate:
	@echo "📊 Evaluando modelos..."
	$(PYTHON_VENV) scripts/05_evaluate_models.py
	@echo "✅ Evaluación completada"

## Generar ensamble
ensemble:
	@echo "🎭 Generando ensamble..."
	$(PYTHON_VENV) scripts/06_generate_ensemble.py
	@echo "✅ Ensamble generado"

## Generar reporte final
report:
	@echo "📄 Generando reporte..."
	$(PYTHON_VENV) scripts/07_generate_report.py
	@echo "✅ Reporte generado"

## Pipeline completo
pipeline: download audit clean train evaluate ensemble report
	@echo "✅ Pipeline completado exitosamente"

# =============================================================================
# COMANDOS AUXILIARES
# =============================================================================

## Limpiar archivos temporales
clean-files:
	@echo "🧹 Limpiando archivos temporales..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	@echo "✅ Archivos temporales eliminados"

## Ejecutar tests
test:
	@echo "🧪 Ejecutando tests..."
	$(PYTHON_VENV) -m pytest tests/ -v --cov=src --cov-report=html
	@echo "✅ Tests completados"

## Iniciar Jupyter Notebook
notebook:
	@echo "📓 Iniciando Jupyter Notebook..."
	$(PYTHON_VENV) -m jupyter notebook notebooks/

## Mostrar ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  make setup       - Configurar entorno virtual"
	@echo "  make install     - Instalar dependencias"
	@echo "  make download    - Descargar dataset"
	@echo "  make audit       - Auditoría de calidad"
	@echo "  make clean       - Limpieza de datos"
	@echo "  make train       - Entrenar modelos"
	@echo "  make evaluate    - Evaluar modelos"
	@echo "  make ensemble    - Generar ensamble"
	@echo "  make report      - Generar reporte"
	@echo "  make pipeline    - Ejecutar pipeline completo"
	@echo "  make clean-files - Limpiar archivos temporales"
	@echo "  make test        - Ejecutar tests"
	@echo "  make notebook    - Iniciar Jupyter Notebook"
	@echo "  make help        - Mostrar esta ayuda"
