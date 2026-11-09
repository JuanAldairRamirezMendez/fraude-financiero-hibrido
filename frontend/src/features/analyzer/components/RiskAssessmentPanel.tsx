import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { Icon } from "@/components/ui/Icon";
import type { RiskLevel } from "@/types/common";

import type { RiskAssessment } from "../types";
import { RiskGauge } from "./RiskGauge";

const levelVariant: Record<RiskLevel, BadgeVariant> = {
  low: "success",
  medium: "warning",
  high: "danger",
};

const levelText: Record<RiskLevel, string> = {
  low: "Low risk",
  medium: "Medium risk",
  high: "High risk",
};

interface RiskAssessmentPanelProps {
  assessment: RiskAssessment;
}

export function RiskAssessmentPanel({ assessment }: RiskAssessmentPanelProps) {
  return (
    <>
      <ChartHeader
        title="Risk Assessment"
        subtitle={`Decision generated in ${assessment.latencyMs}ms`}
        actions={
          <Badge variant={levelVariant[assessment.level]}>{levelText[assessment.level]}</Badge>
        }
      />
      <RiskGauge score={assessment.score} level={assessment.level} />
      <div className="decision-message">
        <span aria-hidden="true">
          <Icon name="shield" size={22} />
        </span>
        <div>
          <strong>
            {assessment.blocked ? "Blocked due to fraud alert" : "Approved — below risk threshold"}
          </strong>
          <small>
            {assessment.signalsTriggered} risk signals · {assessment.summary}
          </small>
        </div>
      </div>
      {assessment.blocked && (
        <div className="stamp" aria-hidden="true">
          BLOCKED
        </div>
      )}
      <div className="decision-id">
        Decision ID <strong>{assessment.decisionId}</strong>
      </div>
    </>
  );
}
