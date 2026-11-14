import { Link } from "react-router-dom";

import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { Icon, type IconName } from "@/components/ui/Icon";

import type { DecisionAction } from "../policy";
import type { RiskAssessment } from "../types";
import { RiskGauge } from "./RiskGauge";

const DECISION_VIEW: Record<
  DecisionAction,
  { badge: string; variant: BadgeVariant; title: string; icon: IconName; stamp?: string }
> = {
  approve: {
    badge: "Riesgo bajo",
    variant: "success",
    title: "Aprobada",
    icon: "check",
  },
  review: {
    badge: "Sospechosa",
    variant: "warning",
    title: "Bloqueada temporalmente · pendiente de revisión",
    icon: "clock",
    stamp: "RETENIDA",
  },
  block: {
    badge: "Fraude probable",
    variant: "danger",
    title: "Bloqueada por riesgo de fraude",
    icon: "shield",
    stamp: "BLOQUEADA",
  },
};

interface RiskAssessmentPanelProps {
  assessment: RiskAssessment;
}

export function RiskAssessmentPanel({ assessment }: RiskAssessmentPanelProps) {
  const view = DECISION_VIEW[assessment.decision];
  const signals = assessment.signalsTriggered;

  return (
    <>
      <ChartHeader
        title="Evaluación de riesgo"
        subtitle={`Decisión generada en ${assessment.latencyMs} ms`}
        actions={<Badge variant={view.variant}>{view.badge}</Badge>}
      />
      <RiskGauge
        score={assessment.score}
        level={assessment.level}
        reviewThreshold={assessment.reviewThreshold}
        blockThreshold={assessment.blockThreshold}
      />
      <div className={`decision-message decision-${assessment.decision}`}>
        <span aria-hidden="true">
          <Icon name={view.icon} size={22} />
        </span>
        <div>
          <strong>{view.title}</strong>
          <small>
            {assessment.summary} {signals} {signals === 1 ? "señal de riesgo" : "señales de riesgo"}
            .
          </small>
        </div>
      </div>
      {assessment.decision !== "approve" && assessment.caseId && (
        <Link className="case-link" to={`/cases?case=${assessment.caseId}`}>
          <Icon name="alert" size={16} />
          <span>
            Caso <strong>{assessment.caseNumber}</strong> enviado al analista para su revisión
          </span>
          <Icon name="arrow" size={15} />
        </Link>
      )}
      {view.stamp && (
        <div className={`stamp stamp-${assessment.decision}`} aria-hidden="true">
          {view.stamp}
        </div>
      )}
      <div className="decision-id">
        ID de decisión <strong>{assessment.decisionId}</strong>
      </div>
    </>
  );
}
