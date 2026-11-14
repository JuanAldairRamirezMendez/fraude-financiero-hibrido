import { Icon } from "@/components/ui/Icon";

import type { DecisionAction } from "../policy";
import type { RealSample } from "../realSamples";

interface GroundTruthRevealProps {
  sample: RealSample;
  decision: DecisionAction;
}

type Outcome = { tone: "correct" | "partial" | "wrong"; verdict: string; detail: string };

function outcomeOf(isFraud: boolean, decision: DecisionAction): Outcome {
  if (isFraud) {
    if (decision === "block")
      return {
        tone: "correct",
        verdict: "el modelo acertó",
        detail: "Fraude bloqueado antes de completarse.",
      };
    if (decision === "review")
      return {
        tone: "correct",
        verdict: "el modelo acertó",
        detail: "Fraude detectado: quedó retenido hasta la revisión del analista.",
      };
    return {
      tone: "wrong",
      verdict: "el modelo se equivocó",
      detail: "Fraude no detectado: se habría aprobado.",
    };
  }
  if (decision === "approve")
    return {
      tone: "correct",
      verdict: "el modelo acertó",
      detail: "Transacción legítima aprobada.",
    };
  if (decision === "review")
    return {
      tone: "partial",
      verdict: "falsa alarma leve",
      detail: "Era legítima: queda retenida y el analista la liberaría tras revisarla.",
    };
  return {
    tone: "wrong",
    verdict: "el modelo se equivocó",
    detail: "Falsa alarma: era legítima; el analista la liberaría al revisar el caso.",
  };
}

/** Revela la etiqueta verdadera de una transacción real después de que el modelo decidió. */
export function GroundTruthReveal({ sample, decision }: GroundTruthRevealProps) {
  const outcome = outcomeOf(sample.isFraud, decision);

  return (
    <div className={`truth-reveal is-${outcome.tone}`} role="status">
      <span className="truth-icon" aria-hidden="true">
        <Icon name={outcome.tone === "wrong" ? "alert" : "check"} size={18} />
      </span>
      <div>
        <span className="truth-kicker">Etiqueta real · {sample.id}</span>
        <strong>
          Era {sample.isFraud ? "FRAUDE" : "LEGÍTIMA"} · {outcome.verdict}
        </strong>
        <small>{outcome.detail}</small>
      </div>
    </div>
  );
}
