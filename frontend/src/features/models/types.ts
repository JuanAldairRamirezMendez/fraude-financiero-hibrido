export type AlertStatus = "UNACKNOWLEDGED" | "ACKNOWLEDGED" | "RESOLVED";

export interface ModelAlert {
  id: string;
  occurredAt: string;
  modelId: string;
  alertType: "Feature drift" | "Data quality" | "Prediction drift" | "Performance";
  detail: string;
  status: AlertStatus;
}

export interface ModelHealth {
  status: "stable" | "degraded";
  uptimePct: number;
  avgLatencyMs: number;
  criticalIssues: number;
  psi: number;
  driftShiftPct: number;
  psiThreshold: number;
  windowLabel: string;
}

export interface ModelsData {
  health: ModelHealth;
  alerts: ModelAlert[];
  updatedAt: string;
}
