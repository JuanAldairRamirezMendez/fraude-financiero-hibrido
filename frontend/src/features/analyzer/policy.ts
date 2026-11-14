import type { RiskLevel } from "@/types/common";

import type { ApiRiskAssessment } from "./types";

export type DecisionAction = ApiRiskAssessment["decision"];

/** Misma política que `backend/app/domain/transaction.py::decide`. */
export function decide(
  probability: number,
  reviewThreshold: number,
  blockThreshold: number,
): DecisionAction {
  if (probability >= blockThreshold) return "block";
  if (probability >= reviewThreshold) return "review";
  return "approve";
}

export const LEVEL_BY_DECISION: Record<DecisionAction, RiskLevel> = {
  approve: "low",
  review: "medium",
  block: "high",
};

export const DECISION_SUMMARY: Record<DecisionAction, string> = {
  approve: "La probabilidad de fraude está por debajo del umbral de bloqueo.",
  review: "Probabilidad intermedia: queda retenida hasta que un analista la revise.",
  block: "Probabilidad de fraude sobre el umbral: se bloquea y un analista puede revisarla.",
};
