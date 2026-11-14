import raw from "./real-samples.json";

import type { TransactionFormValues } from "./validation";

/**
 * Transacciones reales del conjunto de prueba (nunca vistas por el modelo), generadas por
 * `backend/scripts/build_evaluation.py`. La muestra está equilibrada (mitad fraudes) para
 * que en una demo aparezcan fraudes con frecuencia; en la realidad son el 1.5 %.
 */
type ThresholdField = "decisionThreshold";

export interface RealSample {
  id: string;
  isFraud: boolean;
  values: Record<Exclude<keyof TransactionFormValues, ThresholdField>, string | number>;
}

const data = raw as unknown as { note: string; samples: RealSample[] };

export const REAL_SAMPLES: readonly RealSample[] = data.samples;
export const REAL_SAMPLES_NOTE = data.note;

export function pickRealSample(excludeId?: string, random: () => number = Math.random): RealSample {
  const pool = REAL_SAMPLES.filter((sample) => sample.id !== excludeId);
  return pool[Math.floor(random() * pool.length)] ?? REAL_SAMPLES[0];
}

/** Carga los valores de la transacción real conservando los umbrales que el usuario eligió. */
export function sampleToFormValues(
  sample: RealSample,
  thresholds: Pick<TransactionFormValues, ThresholdField>,
): TransactionFormValues {
  const entries = Object.entries(sample.values).map(([key, value]) => [key, String(value)]);
  return {
    ...(Object.fromEntries(entries) as Omit<TransactionFormValues, ThresholdField>),
    decisionThreshold: thresholds.decisionThreshold,
  };
}
