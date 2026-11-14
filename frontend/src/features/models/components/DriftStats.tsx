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
        <span>Índice de estabilidad poblacional (PSI)</span>
        <strong>{health.psi.toFixed(2)}</strong>
        <Badge variant={withinThreshold ? "success" : "warning"}>
          {withinThreshold ? "Dentro del umbral" : "Sobre el umbral"}
        </Badge>
      </div>
      <div>
        <span>Cambio en la distribución</span>
        <strong>{shift}</strong>
        <small>vs. línea base de entrenamiento</small>
      </div>
      <div>
        <span>Umbral</span>
        <strong>{health.psiThreshold.toFixed(2)}</strong>
        <small>Nivel de alerta del PSI</small>
      </div>
    </div>
  );
}
