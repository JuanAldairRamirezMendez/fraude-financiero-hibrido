import { Badge } from "@/components/ui/Badge";

import type { ModelHealth } from "../types";

interface DriftStatsProps {
  health: ModelHealth;
}

export function DriftStats({ health }: DriftStatsProps) {
  const withinThreshold = health.psi <= health.psiThreshold;
  const shift = `${health.driftShiftPct >= 0 ? "+" : ""}${health.driftShiftPct.toFixed(1)}%`;

  return (
    <div className="drift-stats">
      <div>
        <span>Population Stability Index</span>
        <strong>{health.psi.toFixed(2)}</strong>
        <Badge variant={withinThreshold ? "success" : "warning"}>
          {withinThreshold ? "Within threshold" : "Above threshold"}
        </Badge>
      </div>
      <div>
        <span>Distribution shift</span>
        <strong>{shift}</strong>
        <small>vs. training baseline</small>
      </div>
      <div>
        <span>Threshold</span>
        <strong>{health.psiThreshold.toFixed(2)}</strong>
        <small>PSI warning level</small>
      </div>
    </div>
  );
}
