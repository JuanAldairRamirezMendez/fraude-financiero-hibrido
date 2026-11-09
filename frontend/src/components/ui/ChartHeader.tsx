import type { ReactNode } from "react";

interface ChartHeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function ChartHeader({ title, subtitle, actions }: ChartHeaderProps) {
  return (
    <div className="chart-header">
      <div>
        <h2 className="section-title">{title}</h2>
        {subtitle && <p className="section-subtitle">{subtitle}</p>}
      </div>
      {actions}
    </div>
  );
}
