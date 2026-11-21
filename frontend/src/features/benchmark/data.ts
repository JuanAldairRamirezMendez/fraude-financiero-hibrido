import raw from "./benchmark-data.json";

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
  averagePrecision: number;
  threshold: number;
  selected?: boolean;
}

/**
 * Resultados en la prueba de Sparkov (jun–dic 2020) generados por
 * `experiments/comparativa_sparkov.py`: mismas 36 variables, misma división temporal y
 * umbral de cada modelo elegido en la validación.
 */
const data = raw as unknown as { dataset: string; note: string; results: ModelResult[] };

export const MODEL_RESULTS: readonly ModelResult[] = data.results;
export const BENCHMARK_DATASET = data.dataset;

/** Aporte del historial de la tarjeta (experiments/viabilidad_sparkov.py, misma prueba). */
export const HISTORY_GAIN = { withoutHistoryF1: 0.828, withHistoryF1: 0.926 } as const;

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
      "Perceptrón multicapa que aprende interacciones no lineales entre la compra y el historial de la tarjeta.",
    techniques: ["Perceptrón multicapa", "3 capas ocultas (128-64-32)", "Early stopping"],
  },
  {
    family: "classic",
    title: "Machine Learning",
    description:
      "Modelos de árboles y márgenes, robustos con datos tabulares y clases desbalanceadas.",
    techniques: ["XGBoost", "LightGBM", "Random Forest", "Regresión logística"],
  },
  {
    family: "ensemble",
    title: "Técnicas de ensamble",
    description:
      "Combinan varios modelos base para reducir la varianza y aprovechar sus fortalezas.",
    techniques: ["Soft voting", "Stacking", "Meta-modelo logístico"],
  },
];

export const CRISP_DM_STEPS: readonly { title: string; detail: string }[] = [
  { title: "Negocio", detail: "Priorizar transacciones sospechosas para el analista" },
  { title: "Datos", detail: "1.85 M compras con tarjeta (Sparkov, 2019–2020)" },
  { title: "Preparación", detail: "36 variables: compra + historial de cada tarjeta" },
  { title: "Modelado", detail: "7 modelos: red neuronal, ML clásico y ensambles" },
  { title: "Evaluación", detail: "División temporal: umbral en validación, F1 en prueba" },
  { title: "Despliegue", detail: "XGBoost + SHAP vía API REST con historial en vivo" },
];
