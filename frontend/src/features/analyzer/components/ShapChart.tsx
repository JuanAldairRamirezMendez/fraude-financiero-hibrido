import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { Icon } from "@/components/ui/Icon";

import type { RiskAssessment } from "../types";

interface ShapChartProps {
  assessment: RiskAssessment;
}

export function ShapChart({ assessment }: ShapChartProps) {
  const maxImpact = Math.max(...assessment.shap.map((feature) => feature.impact), 0.1);

  return (
    <Card className="shap-panel">
      <ChartHeader
        title="SHAP Feature Importance"
        subtitle="Impact on the final model prediction"
      />
      <div className="shap-axis" aria-hidden="true">
        <span>Feature</span>
        <span>Impact on prediction</span>
      </div>
      <div className="shap-list">
        {assessment.shap.map((feature) => (
          <div className="shap-row" key={feature.feature}>
            <div className="shap-label">{feature.feature}</div>
            <div className="bar-track">
              <div
                className={`shap-bar bar-${feature.tone}`}
                style={{ width: `${(feature.impact / maxImpact) * 100}%` }}
              />
            </div>
            <strong>{feature.impact.toFixed(2)}</strong>
          </div>
        ))}
      </div>
      <div className="impact-scale" aria-hidden="true">
        <span>0.0</span>
        <span>{(maxImpact / 4).toFixed(1)}</span>
        <span>{(maxImpact / 2).toFixed(1)}</span>
        <span>{((maxImpact * 3) / 4).toFixed(1)}</span>
        <span>{maxImpact.toFixed(1)}</span>
      </div>
      <div className="shap-note">
        <Icon name="activity" size={18} />
        <span>
          <strong>{assessment.topDriver.feature}</strong> is the strongest driver, increasing fraud
          probability by {assessment.topDriver.impactPct.toFixed(1)}%.
        </span>
      </div>
    </Card>
  );
}
