import { env } from "@/config/env";
import { apiRequest } from "@/lib/api/client";
import { mockDelay } from "@/lib/api/mock";

import { mockAnalyzeTransaction } from "./mocks";
import type { ApiRiskAssessment, RiskAssessment, TransactionInput } from "./types";

const MOCK_LATENCY_MS = 650;

export async function analyzeTransaction(
  input: TransactionInput,
  signal?: AbortSignal,
): Promise<RiskAssessment> {
  if (!env.useMocks) {
    const response = await apiRequest<ApiRiskAssessment>("/analyze", {
      method: "POST",
      body: input,
      signal,
    });
    return {
      ...response,
      summary: response.blocked
        ? "Multiple risk signals exceed the configured threshold."
        : "The transaction is below the configured risk threshold.",
      shap: response.shap.map((item, index) => ({
        ...item,
        tone: ["blue", "orange", "violet", "indigo", "cyan", "teal", "rose", "slate"][index] as RiskAssessment["shap"][number]["tone"],
      })),
    };
  }

  await mockDelay(MOCK_LATENCY_MS, signal);
  return mockAnalyzeTransaction(input);
}
