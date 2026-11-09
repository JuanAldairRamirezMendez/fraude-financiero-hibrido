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
        <h2 className="status-title">Model Status: {stable ? "Stable" : "Degraded"}</h2>
        <p>
          {stable
            ? "All core models are performing within their configured thresholds."
            : "One or more models require attention."}
        </p>
      </div>
      <div className="status-metrics">
        <span>
          <strong>{formatPercent(health.uptimePct)}</strong>Uptime
        </span>
        <span>
          <strong>{health.avgLatencyMs}ms</strong>Avg. latency
        </span>
        <span>
          <strong>{health.criticalIssues}</strong>Critical issues
        </span>
      </div>
      <Badge variant={stable ? "success" : "warning"}>
        {stable ? (
          <>
            <Icon name="check" size={13} /> Healthy
          </>
        ) : (
          "Attention"
        )}
      </Badge>
    </section>
  );
}
