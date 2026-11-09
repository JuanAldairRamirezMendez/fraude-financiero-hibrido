import { clamp } from "@/lib/format";
import type { RiskLevel } from "@/types/common";

import type { RiskAssessment, ShapTone, TransactionInput } from "./types";

const tones: ShapTone[] = ["blue", "orange", "violet", "indigo", "cyan", "teal"];

function resolveLevel(score: number): RiskLevel {
  if (score >= 75) return "high";
  if (score >= 40) return "medium";
  return "low";
}

export function mockAnalyzeTransaction(input: TransactionInput): RiskAssessment {
  const amountImpact = clamp(input.transactionAmount / 10_000, 0.05, 2);
  const chargebackImpact = clamp(input.previousChargebacks * 0.32, 0, 1.8);
  const velocityImpact = clamp(input.transactionVelocity24h / 100, 0.05, 1.4);
  const categoryImpact = input.isHighRiskMerchantCategory ? 0.9 : 0.12;
  const score = clamp(
    Math.round(12 + input.transactionAmount / 500 + input.previousChargebacks * 6 + velocityImpact * 18 + categoryImpact * 18),
    1,
    99,
  );
  const level = resolveLevel(score);
  const rawShap = [
    ["Transaction amount", amountImpact],
    ["Previous chargebacks", chargebackImpact],
    ["Transaction velocity", velocityImpact],
    ["Merchant risk", categoryImpact],
    ["Customer risk score", input.customerRiskScore],
  ] as const;
  const totalImpact = rawShap.reduce((sum, [, impact]) => sum + impact, 0);

  return {
    decisionId: `#DEC-${Math.random().toString(36).slice(2, 10).toUpperCase()}`,
    probability: score / 100,
    score,
    level,
    blocked: score / 100 >= input.decisionThreshold,
    signalsTriggered: [
      input.transactionAmount >= 5_000,
      input.previousChargebacks >= 2,
      input.isHighRiskMerchantCategory === 1,
      input.customerRiskScore >= 0.7,
      input.transactionVelocity24h >= 20,
    ].filter(Boolean).length,
    latencyMs: 120,
    shap: rawShap.map(([feature, impact], index) => ({
      feature,
      impact,
      direction: "increases" as const,
      tone: tones[index] ?? "slate",
    })),
    topDriver: { feature: rawShap[0][0], impactPct: clamp((rawShap[0][1] / totalImpact) * 100, 1, 99) },
    modelVersion: "mock-xgboost-tier2",
    calibratedThreshold: 0.5,
    idempotentReplay: false,
    summary:
      level === "high"
        ? "Multiple risk signals exceed the configured threshold."
        : level === "medium"
          ? "The transaction requires manual review."
          : "No material risk signals were detected.",
  };
}
