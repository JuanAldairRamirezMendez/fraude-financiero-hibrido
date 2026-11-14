import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { Icon } from "@/components/ui/Icon";
import { featureLabel } from "@/lib/labels";

import type { RiskAssessment } from "../types";

interface ShapChartProps {
  assessment: RiskAssessment;
}

const directionText = {
  increases: "aumenta el riesgo",
  decreases: "reduce el riesgo",
} as const;

export function ShapChart({ assessment }: ShapChartProps) {
  const maxImpact = Math.max(...assessment.shap.map((feature) => feature.impact), 0.1);
  const topDriver = assessment.topDriver;
  const topDirection = assessment.shap.find(
    (feature) => feature.feature === topDriver.feature,
  )?.direction;

  return (
    <Card className="shap-panel">
      <ChartHeader
        title="Importancia de variables (SHAP)"
        subtitle="Cuánto pesó cada variable en la decisión del modelo"
      />
      <div className="shap-axis" aria-hidden="true">
        <span>Variable</span>
        <span>Impacto en la predicción</span>
      </div>
      <div className="shap-list">
        {assessment.shap.map((feature) => {
          const label = featureLabel(feature.feature);
          const direction = directionText[feature.direction];
          return (
            <div className="shap-row" key={feature.feature}>
              <div className="shap-label" title={`${label}: ${direction}`}>
                <span className={`shap-direction shap-${feature.direction}`} aria-label={direction}>
                  {feature.direction === "increases" ? "▲" : "▼"}
                </span>
                {label}
              </div>
              <div className="bar-track">
                <div
                  className={`shap-bar bar-${feature.tone}`}
                  style={{ width: `${(feature.impact / maxImpact) * 100}%` }}
                />
              </div>
              <strong>{feature.impact.toFixed(2)}</strong>
            </div>
          );
        })}
      </div>
      <div className="impact-scale" aria-hidden="true">
        <span>0.0</span>
        <span>{(maxImpact / 4).toFixed(1)}</span>
        <span>{(maxImpact / 2).toFixed(1)}</span>
        <span>{((maxImpact * 3) / 4).toFixed(1)}</span>
        <span>{maxImpact.toFixed(1)}</span>
      </div>
      <div className="shap-legend" aria-hidden="true">
        <span>
          <span className="shap-direction shap-increases">▲</span> aumenta el riesgo
        </span>
        <span>
          <span className="shap-direction shap-decreases">▼</span> reduce el riesgo
        </span>
      </div>
      <div className="shap-note">
        <Icon name="activity" size={18} />
        <span>
          <strong>{featureLabel(topDriver.feature)}</strong> es la variable más influyente: explica
          el {topDriver.impactPct.toFixed(1)}% del impacto total
          {topDirection ? ` y ${directionText[topDirection]}` : ""}.
        </span>
      </div>
    </Card>
  );
}
