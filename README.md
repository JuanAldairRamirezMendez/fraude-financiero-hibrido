# Sistema Híbrido de Detección de Fraude Financiero

## Descripción

Sistema híbrido de detección de fraude financiero mediante Redes Neuronales, Machine Learning y Técnicas de Ensamble.

## Integrantes

- Bedon Silva, Yefli
- Ramirez Mendez, Juan Aldair
- Principe Carrasco, Augusto
- Ferrer Melgarejo, Jairo Lee

## Docente

Dr. Cesar Hernan Patricio Peralta

## Curso

Inteligencia Artificial - Facultad de Ingeniería de Software

## Metodología

Este proyecto sigue la metodología **CRISP-DM** (Cross-Industry Standard Process for Data Mining):

1. **Fase 1:** Comprensión del negocio
2. **Fase 2:** Comprensión de los datos
3. **Fase 3:** Preparación de los datos
4. **Fase 4:** Modelado
5. **Fase 5:** Evaluación
6. **Fase 6:** Despliegue

## Dataset

- **Fuente:** Hugging Face
- **Dataset:** Nigerian Financial Transactions and Fraud Detection Dataset
- **Registros:** 5,000,000 transacciones
- **Features:** 45 variables

## Tecnologías

- Python 3.10+
- PostgreSQL 16
- PyTorch (con soporte ROCm para AMD RX 6700 XT)
- Scikit-learn
- XGBoost
- SHAP/LIME para interpretabilidad

## Instalación

\`\`\`bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate

# Instalar dependencias
make install

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales

# Iniciar PostgreSQL (si usas Docker)
docker-compose up -d

# Ejecutar pipeline completo
make pipeline
\`\`\`

## Estructura del Proyecto

\`\`\`
fraude-financiero-hibrido/
├── config/              # Configuraciones
├── data/                # Datos (no subir a Git)
├── notebooks/           # Notebooks Jupyter
├── src/                 # Código fuente
│   ├── data/           # Manejo de datos
│   ├── models/         # Modelos de ML
│   ├── training/       # Entrenamiento
│   ├── interpretability/ # XAI
│   ├── visualization/  # Gráficos
│   └── utils/          # Utilidades
├── scripts/            # Scripts ejecutables
├── tests/              # Tests unitarios
├── logs/               # Logs de ejecución
├── models_saved/       # Modelos entrenados
├── reports/            # Reportes generados
└── docs/               # Documentación
\`\`\`

## Comandos Makefile

\`\`\`bash
make setup          # Configurar entorno virtual
make install        # Instalar dependencias
make download       # Descargar dataset
make audit          # Auditoría de calidad
make clean          # Limpieza de datos
make train          # Entrenar modelos
make evaluate       # Evaluar modelos
make ensemble       # Generar ensamble
make report         # Generar reporte
make pipeline       # Ejecutar pipeline completo
\`\`\`

## Licencia

Este proyecto es de uso académico.

## Año

2026
