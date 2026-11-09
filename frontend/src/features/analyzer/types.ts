import type { components } from "@/lib/api/schema";

export type TransactionInput = components["schemas"]["AnalyzeRequest"];
export type ApiRiskAssessment = components["schemas"]["AnalyzeResponse"];
export type ShapTone =
  | "blue"
  | "cyan"
  | "violet"
  | "orange"
  | "indigo"
  | "teal"
  | "rose"
  | "slate";

export interface RiskAssessment extends ApiRiskAssessment {
  summary: string;
  shap: Array<ApiRiskAssessment["shap"][number] & { tone: ShapTone }>;
}
