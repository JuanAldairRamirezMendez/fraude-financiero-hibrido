# =============================================================================
# MAKEFILE - Sistema Híbrido de Detección de Fraude Financiero
# =============================================================================

.PHONY: setup install pipeline clean-files test notebook help

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

## Ejecutar pipeline completo unificado (CRISP-DM, fases 1-12)
pipeline:
	@echo "🚀 Ejecutando pipeline completo CRISP-DM..."
	$(PYTHON_VENV) pipeline_completo.py
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
	@echo "  make pipeline    - Ejecutar pipeline completo (pipeline_completo.py)"
	@echo "  make clean-files - Limpiar archivos temporales"
	@echo "  make test        - Ejecutar tests"
	@echo "  make notebook    - Iniciar Jupyter Notebook"
	@echo "  make help        - Mostrar esta ayuda"
