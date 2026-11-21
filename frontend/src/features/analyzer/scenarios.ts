import raw from "./scenarios.json";
import { BLOCK_THRESHOLD, type TransactionFormValues } from "./validation";

export type ScenarioRisk = "low" | "medium" | "high";

export interface DemoScenario {
  id: string;
  label: string;
  description: string;
  expectedRisk: ScenarioRisk;
  /** Puntaje que el modelo dio al generar el escenario (sirve para verificarlo). */
  expectedScore: number;
  values: TransactionFormValues;
}

/**
 * Escenarios de demostración: transacciones REALES del periodo de prueba de Sparkov
 * (jun–dic 2020), elegidas por `backend/scripts/build_sparkov_artifacts.py`. El
 * historial de cada tarjeta lo aporta el backend, así que el resultado depende de la
 * tarjeta y de la fecha, no solo del monto.
 */
export const DEMO_SCENARIOS: readonly DemoScenario[] = raw.map((scenario) => ({
  id: scenario.id,
  label: scenario.label,
  description: scenario.description,
  expectedRisk: scenario.expectedRisk as ScenarioRisk,
  expectedScore: scenario.expectedScore,
  values: {
    cardId: scenario.values.cardId,
    transactionTime: scenario.values.transactionTime,
    amount: String(scenario.values.amount),
    category: scenario.values.category,
    merchantDistanceKm: String(scenario.values.merchantDistanceKm),
    decisionThreshold: BLOCK_THRESHOLD,
  },
}));
