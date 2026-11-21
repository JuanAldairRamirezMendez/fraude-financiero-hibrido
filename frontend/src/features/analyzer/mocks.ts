import { clamp } from "@/lib/format";

import { cardInfo } from "./cards";
import { DECISION_SUMMARY, LEVEL_BY_DECISION, decide } from "./policy";
import type { RiskAssessment, ShapTone, TransactionInput } from "./types";

const tones: ShapTone[] = ["blue", "orange", "violet", "indigo", "cyan", "teal"];

/**
 * Evaluación simulada para el modo sin backend (VITE_USE_MOCKS=true). No usa el modelo:
 * solo reacciona al monto, la hora y el canal para que la interfaz se pueda probar.
 */
export function mockAnalyzeTransaction(input: TransactionInput): RiskAssessment {
  const hour = new Date(input.transactionTime).getHours();
  const night = [22, 23, 0, 1, 2, 3].includes(hour) ? 1 : 0;
  const online = input.category.endsWith("_net") ? 1 : 0;
  const amountImpact = clamp(input.amount / 400, 0.05, 2);
  const score = clamp(Math.round(4 + input.amount / 25 + night * 30 + online * 12), 0, 100);
  const reviewThreshold = input.decisionThreshold ?? 0.466;
  const blockThreshold = input.blockThreshold ?? reviewThreshold;
  const decision = decide(score / 100, reviewThreshold, blockThreshold);
  const rawShap = [
    ["monto_24h", amountImpact * 1.2],
    ["monto", amountImpact],
    ["nocturna", night ? 1.4 : 0.2],
    ["categoria", online ? 0.9 : 0.15],
    ["seg_desde_anterior", 0.3],
  ] as const;
  const totalImpact = rawShap.reduce((sum, [, impact]) => sum + impact, 0);
  const card = cardInfo(input.cardId);

  return {
    decisionId: `#DEC-${Math.random().toString(36).slice(2, 10).toUpperCase()}`,
    probability: score / 100,
    score,
    level: LEVEL_BY_DECISION[decision],
    blocked: decision !== "approve",
    decision,
    reviewThreshold,
    blockThreshold,
    caseId: null,
    caseNumber: null,
    signalsTriggered: [night === 1, input.amount >= 500, online === 1].filter(Boolean).length,
    latencyMs: 120,
    shap: rawShap.map(([feature, impact], index) => ({
      feature,
      impact,
      direction: "increases" as const,
      tone: tones[index] ?? "slate",
    })),
    topDriver: {
      feature: rawShap[0][0],
      impactPct: clamp((rawShap[0][1] / totalImpact) * 100, 1, 99),
    },
    modelVersion: "mock-xgboost-sparkov",
    calibratedThreshold: 0.466,
    idempotentReplay: false,
    summary: DECISION_SUMMARY[decision],
    card: {
      previousPurchases: 120,
      secondsSincePrevious: 3_600,
      averageAmount: 64.5,
      purchases1h: 1,
      amount1h: input.amount,
      purchases24h: 3,
      amount24h: input.amount + 90,
      customerAge: card ? 2020 - card.birthYear : 40,
      customerGender: card?.gender ?? "F",
      city: card?.city ?? "—",
      state: card?.state ?? "—",
    },
  };
}
