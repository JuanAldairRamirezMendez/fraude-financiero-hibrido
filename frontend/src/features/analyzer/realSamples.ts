import raw from "./real-samples.json";

import type { TransactionFormValues } from "./validation";

/**
 * Transacciones reales del periodo de prueba de Sparkov (jun–dic 2020), que el modelo
 * nunca vio al entrenar. Las genera `backend/scripts/build_sparkov_artifacts.py`. La
 * muestra está equilibrada (mitad fraudes) para que en una demo aparezcan fraudes con
 * frecuencia; en la realidad son el 0.39 %.
 */
type ThresholdField = "decisionThreshold";

export interface RealSample {
  id: string;
  isFraud: boolean;
  values: {
    cardId: string;
    transactionTime: string;
    amount: number;
    category: string;
    merchantDistanceKm: number;
  };
}

const data = raw as unknown as { note: string; samples: RealSample[] };

export const REAL_SAMPLES: readonly RealSample[] = data.samples;
export const REAL_SAMPLES_NOTE = data.note;

export function pickRealSample(excludeId?: string, random: () => number = Math.random): RealSample {
  const pool = REAL_SAMPLES.filter((sample) => sample.id !== excludeId);
  return pool[Math.floor(random() * pool.length)] ?? REAL_SAMPLES[0];
}

/** Carga los valores de la transacción real conservando el umbral que el usuario eligió. */
export function sampleToFormValues(
  sample: RealSample,
  thresholds: Pick<TransactionFormValues, ThresholdField>,
): TransactionFormValues {
  return {
    cardId: sample.values.cardId,
    transactionTime: sample.values.transactionTime,
    amount: String(sample.values.amount),
    category: sample.values.category,
    merchantDistanceKm: String(sample.values.merchantDistanceKm),
    decisionThreshold: thresholds.decisionThreshold,
  };
}
