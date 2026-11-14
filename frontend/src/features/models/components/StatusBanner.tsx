import { Badge } from "@/components/ui/Badge";
import { Icon } from "@/components/ui/Icon";
import { formatPercent } from "@/lib/format";

import type { ModelHealth } from "../types";

interface StatusBannerProps {
  health: ModelHealth;
}

export function StatusBanner({ health }: StatusBannerProps) {
  const stable = health.status === "stable";

  return (
    <section className="status-banner" aria-label="Estado de los modelos">
      <span className="status-icon" aria-hidden="true">
        <Icon name={stable ? "bell" : "alert"} size={24} />
      </span>
      <div>
        <h2 className="status-title">Estado del modelo: {stable ? "Estable" : "Degradado"}</h2>
        <p>
          {stable
            ? "Todos los modelos principales funcionan dentro de sus umbrales configurados."
            : "Uno o más modelos requieren atención."}
        </p>
      </div>
      <div className="status-metrics">
        <span>
          <strong>{formatPercent(health.uptimePct)}</strong>Disponibilidad
        </span>
        <span>
          <strong>{health.avgLatencyMs} ms</strong>Latencia media
        </span>
        <span>
          <strong>{health.criticalIssues}</strong>Incidencias críticas
        </span>
      </div>
      <Badge variant={stable ? "success" : "warning"}>
        {stable ? (
          <>
            <Icon name="check" size={13} /> Saludable
          </>
        ) : (
          "Atención"
        )}
      </Badge>
    </section>
  );
}
