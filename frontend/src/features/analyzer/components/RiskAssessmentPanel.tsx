import { Link } from "react-router-dom";

import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { Icon, type IconName } from "@/components/ui/Icon";

import { formatCurrency } from "@/lib/format";
import { GENDER_LABELS } from "@/lib/labels";

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

type Card = NonNullable<RiskAssessment["card"]>;

function elapsed(seconds: number): string {
  if (seconds < 3_600) return `hace ${Math.max(1, Math.round(seconds / 60))} min`;
  if (seconds < 86_400) return `hace ${Math.round(seconds / 3_600)} h`;
  return `hace ${Math.round(seconds / 86_400)} días`;
}

/** Lo que el modelo sabe de la tarjeta: su actividad reciente y el perfil del cliente. */
function CardHistory({ card }: { card: Card }) {
  return (
    <section className="card-history" aria-label="Historial de la tarjeta">
      <span className="card-history-title">
        Historial de la tarjeta · {GENDER_LABELS[card.customerGender] ?? card.customerGender},{" "}
        {card.customerAge} años · {card.city}, {card.state}
      </span>
      <dl>
        <div className={card.purchases1h >= 3 ? "is-risky" : undefined}>
          <dt>Última hora</dt>
          <dd>
            {card.purchases1h} {card.purchases1h === 1 ? "compra" : "compras"} ·{" "}
            {formatCurrency(card.amount1h)}
          </dd>
        </div>
        <div className={card.purchases24h >= 8 || card.amount24h >= 1_500 ? "is-risky" : undefined}>
          <dt>Últimas 24 h</dt>
          <dd>
            {card.purchases24h} compras · {formatCurrency(card.amount24h)}
          </dd>
        </div>
        <div
          className={
            card.secondsSincePrevious != null && card.secondsSincePrevious < 600
              ? "is-risky"
              : undefined
          }
        >
          <dt>Compra anterior</dt>
          <dd>
            {card.secondsSincePrevious == null
              ? "Primera compra"
              : elapsed(card.secondsSincePrevious)}
          </dd>
        </div>
        <div>
          <dt>Gasto promedio</dt>
          <dd>{card.averageAmount == null ? "—" : formatCurrency(card.averageAmount)}</dd>
        </div>
      </dl>
    </section>
  );
}

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
      {assessment.card && <CardHistory card={assessment.card} />}
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
