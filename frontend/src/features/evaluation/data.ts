import raw from "./evaluation-data.json";

/**
 * Datos generados por `backend/scripts/build_evaluation.py` sobre el conjunto de prueba
 * (20 % estratificado, random_state=42) que el modelo nunca vio al entrenar.
 */

export interface ConfusionCounts {
  threshold: number;
  tp: number;
  fp: number;
  fn: number;
  tn: number;
  caughtAmount: number;
  missedAmount: number;
}

export interface FeatureImportance {
  feature: string;
  meanAbsShap: number;
  share: number;
}

export interface ProfileBucket {
  key: string;
  transactions: number;
  frauds: number;
  fraudRate: number;
}

export type ProfileDimension =
  "merchantCategory" | "transactionHour" | "transactionCountry" | "transactionType";

export interface EvaluationData {
  generatedAt: string;
  modelVersion: string;
  dataset: {
    source: string;
    rows: number;
    fraudRate: number;
    split: string;
    testRows: number;
    testFrauds: number;
    avgFraudAmount: number;
  };
  calibratedThreshold: number;
  calibrated: ConfusionCounts;
  aucRoc: number;
  averagePrecision: number;
  thresholds: ConfusionCounts[];
  roc: [number, number][];
  precisionRecall: [number, number][];
  globalImportance: FeatureImportance[];
  shapSampleSize: number;
  profile: Record<ProfileDimension, ProfileBucket[]>;
}

export const EVALUATION = raw as unknown as EvaluationData;

export function metricsOf(counts: Pick<ConfusionCounts, "tp" | "fp" | "fn" | "tn">) {
  const { tp, fp, fn } = counts;
  const precision = tp + fp === 0 ? 0 : tp / (tp + fp);
  const recall = tp + fn === 0 ? 0 : tp / (tp + fn);
  const f1 = precision + recall === 0 ? 0 : (2 * precision * recall) / (precision + recall);
  return { precision, recall, f1, alerts: tp + fp };
}

/** Fila de la tabla de umbrales más cercana al valor pedido (pasos de 0.01). */
export function countsAt(threshold: number): ConfusionCounts {
  const index = Math.min(
    EVALUATION.thresholds.length - 1,
    Math.max(0, Math.round(threshold * 100)),
  );
  return EVALUATION.thresholds[index];
}

/** Costo total = fraude no detectado + revisiones manuales de las alertas emitidas. */
export function costAt(counts: ConfusionCounts, reviewCost: number) {
  const reviews = (counts.tp + counts.fp) * reviewCost;
  return { reviews, missed: counts.missedAmount, total: counts.missedAmount + reviews };
}

export function cheapestThreshold(reviewCost: number): ConfusionCounts {
  return EVALUATION.thresholds
    .filter((row) => row.threshold > 0 && row.threshold < 1)
    .reduce((best, row) =>
      costAt(row, reviewCost).total < costAt(best, reviewCost).total ? row : best,
    );
}
