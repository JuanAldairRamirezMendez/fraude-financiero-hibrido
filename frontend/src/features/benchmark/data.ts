export type ModelFamily = "neural" | "classic" | "ensemble";

export interface ModelResult {
  id: string;
  name: string;
  family: ModelFamily;
  detail: string;
  precision: number;
  recall: number;
  f1: number;
  aucRoc: number;
  selected?: boolean;
}

/**
 * Resultados del conjunto de prueba generados por `pipeline_completo.py`
 * (fases 4 y 5). Fuente: `models_saved/final_model_comparison.csv`.
 * Si se reentrena el pipeline, actualizar estos valores desde ese CSV.
 */
export const MODEL_RESULTS: readonly ModelResult[] = [
  {
    id: "xgboost",
    name: "XGBoost",
    family: "classic",
    detail: "Gradient boosting de árboles",
    precision: 0.5664,
    recall: 0.81,
    f1: 0.6667,
    aucRoc: 0.9946,
    selected: true,
  },
  {
    id: "voting",
    name: "Ensamble Soft Voting",
    family: "ensemble",
    detail: "RF + XGBoost + LightGBM + CatBoost, votación ponderada",
    precision: 0.5184,
    recall: 0.7967,
    f1: 0.6281,
    aucRoc: 0.9937,
  },
  {
    id: "stacking",
    name: "Ensamble Stacking",
    family: "ensemble",
    detail: "XGBoost + LightGBM + CatBoost → Regresión Logística",
    precision: 0.6706,
    recall: 0.57,
    f1: 0.6162,
    aucRoc: 0.9899,
  },
  {
    id: "dnn",
    name: "Red Neuronal Profunda",
    family: "neural",
    detail: "TensorFlow/Keras · Dense 128-64-32 + BatchNorm + Dropout",
    precision: 0.5198,
    recall: 0.7,
    f1: 0.5966,
    aucRoc: 0.9793,
  },
  {
    id: "random-forest",
    name: "Random Forest",
    family: "classic",
    detail: "Bosque aleatorio · umbral 0.3",
    precision: 0.4681,
    recall: 0.7833,
    f1: 0.586,
    aucRoc: 0.9915,
  },
  {
    id: "svm",
    name: "SVM lineal",
    family: "classic",
    detail: "Máquina de vectores de soporte optimizada",
    precision: 0.2717,
    recall: 0.97,
    f1: 0.4245,
    aucRoc: 0.9915,
  },
];

/**
 * Métricas del modelo desplegado tras la optimización con Optuna (Tier 2).
 * Fuente: `backend/artifacts/model_metadata.json` → `metrics`.
 */
export const PRODUCTION_MODEL = {
  version: "xgboost-tier2-isotonic-f88d84b82069",
  tier2F1: 0.7343,
  calibratedF1: 0.726,
} as const;

export const FAMILY_LABELS: Record<ModelFamily, string> = {
  neural: "Red neuronal",
  classic: "Machine Learning",
  ensemble: "Ensamble",
};

export interface FamilySummary {
  family: ModelFamily;
  title: string;
  description: string;
  techniques: readonly string[];
}

export const FAMILIES: readonly FamilySummary[] = [
  {
    family: "neural",
    title: "Redes neuronales",
    description:
      "Red densa profunda que aprende interacciones no lineales entre las variables de la transacción.",
    techniques: ["TensorFlow / Keras", "3 capas ocultas", "BatchNorm + Dropout", "Early stopping"],
  },
  {
    family: "classic",
    title: "Machine Learning",
    description:
      "Modelos de árboles y márgenes, robustos con datos tabulares y clases desbalanceadas.",
    techniques: ["XGBoost", "LightGBM", "CatBoost", "Random Forest", "SVM"],
  },
  {
    family: "ensemble",
    title: "Técnicas de ensamble",
    description:
      "Combinan varios modelos base para reducir la varianza y aprovechar sus fortalezas.",
    techniques: ["Soft Voting ponderado", "Stacking", "Meta-learner logístico"],
  },
];

export const CRISP_DM_STEPS: readonly { title: string; detail: string }[] = [
  { title: "Negocio", detail: "Priorizar transacciones sospechosas para el analista" },
  { title: "Datos", detail: "Auditoría de calidad del dataset transaccional" },
  { title: "Preparación", detail: "Limpieza, codificación y escalado de variables" },
  { title: "Modelado", detail: "6 modelos: red neuronal, ML clásico y ensambles" },
  { title: "Evaluación", detail: "F1, AUC-ROC y optimización de umbrales" },
  { title: "Despliegue", detail: "XGBoost calibrado + SHAP vía API REST" },
];
