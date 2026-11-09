import { Card } from "@/components/ui/Card";
import { Icon } from "@/components/ui/Icon";
import { Sparkline } from "@/components/ui/Sparkline";

import type { Kpi } from "../types";

interface KpiGridProps {
  kpis: ReadonlyArray<Kpi>;
}

export function KpiGrid({ kpis }: KpiGridProps) {
  return (
    <div className="kpi-grid">
      {kpis.map((kpi) => (
        <Card className="kpi-card" key={kpi.id}>
          <div className={`kpi-icon icon-${kpi.tone}`} aria-hidden="true">
            <Icon name={kpi.icon} />
          </div>
          <div className="kpi-meta">
            <span>{kpi.label}</span>
            <strong>{kpi.value}</strong>
          </div>
          <div className={`kpi-trend trend-${kpi.tone}`}>{kpi.trend}</div>
          <Sparkline points={kpi.points} tone={kpi.tone} />
        </Card>
      ))}
    </div>
  );
}
