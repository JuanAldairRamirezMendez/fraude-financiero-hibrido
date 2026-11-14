import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Icon } from "@/components/ui/Icon";
import { formatCurrency, formatDateTime, formatRelative } from "@/lib/format";
import {
  COUNTRY_LABELS,
  DEVICE_LABELS,
  MERCHANT_CATEGORY_LABELS,
  REGION_LABELS,
  TRANSACTION_TYPE_LABELS,
  featureLabel,
} from "@/lib/labels";

import {
  STATUS_LABELS,
  VERDICT_LABELS,
  isPending,
  useUpdateCase,
  type CaseVerdict,
  type FraudCase,
} from "../api";

const DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];

type Row = { label: string; value: string; highlight?: boolean };

function transactionRows(transaction: Record<string, string | number>): Row[] {
  const num = (key: string) => Number(transaction[key] ?? 0);
  const str = (key: string) => String(transaction[key] ?? "");
  const amount = num("transactionAmount");
  const average = num("avgTransactionAmount30dCustomer");
  const ratio = average > 0 ? amount / average : 0;

  return [
    {
      label: "Monto",
      value: `${formatCurrency(amount)}${ratio >= 1.5 ? ` · ${ratio.toFixed(1)}× su promedio` : ""}`,
      highlight: ratio >= 3,
    },
    { label: "Promedio del cliente (30 d)", value: formatCurrency(average) },
    {
      label: "Comercio",
      value: MERCHANT_CATEGORY_LABELS[str("merchantCategory")] ?? str("merchantCategory"),
      highlight: num("isHighRiskMerchantCategory") === 1,
    },
    {
      label: "País / región",
      value: `${COUNTRY_LABELS[str("transactionCountry")] ?? str("transactionCountry")} · ${REGION_LABELS[str("geoLocationRegion")] ?? str("geoLocationRegion")}`,
      highlight: num("isInternational") === 1,
    },
    {
      label: "Canal",
      value: `${TRANSACTION_TYPE_LABELS[str("transactionType")] ?? str("transactionType")} · ${DEVICE_LABELS[str("deviceType")] ?? str("deviceType")}`,
    },
    {
      label: "Momento",
      value: `${DAYS[num("transactionDayOfWeek")] ?? "—"}, ${String(num("transactionHour")).padStart(2, "0")}:00`,
    },
    {
      label: "Antigüedad de la cuenta",
      value: `${num("accountAgeDays")} días`,
      highlight: num("accountAgeDays") < 60,
    },
    {
      label: "Contracargos previos",
      value: String(num("previousChargebacks")),
      highlight: num("previousChargebacks") >= 2,
    },
    { label: "Score de riesgo del cliente", value: num("customerRiskScore").toFixed(2) },
    {
      label: "Velocidad",
      value: `${num("transactionVelocity1h")} en 1 h · ${num("transactionVelocity24h")} en 24 h`,
      highlight: num("transactionVelocity1h") >= 3,
    },
  ];
}

interface CaseDetailProps {
  item: FraudCase;
  currentUser: string;
}

export function CaseDetail({ item, currentUser }: CaseDetailProps) {
  const [comment, setComment] = useState("");
  const update = useUpdateCase();
  const pending = isPending(item);
  const decision = item.decision;
  const probability = decision ? Math.round(decision.probability * 100) : null;
  const factors = (decision?.shap ?? []).slice(0, 5);
  const maxImpact = Math.max(...factors.map((factor) => factor.impact), 0.01);
  const busy = update.isPending;

  function send(changes: Parameters<typeof update.mutate>[0]["changes"]) {
    const note = comment.trim();
    update.mutate(
      { id: item.id, changes: { ...changes, ...(note ? { note, feedbackComment: note } : {}) } },
      { onSuccess: () => setComment("") },
    );
  }

  const resolve = (verdict: CaseVerdict) =>
    send({ status: "resolved", verdict, assignedTo: item.assignedTo ?? currentUser });

  return (
    <article className="case-detail" aria-labelledby="case-detail-title">
      <header className="case-detail-header">
        <div>
          <span className="section-kicker">Transacción bloqueada</span>
          <h2 id="case-detail-title">{item.caseNumber}</h2>
          <p>
            Abierto {formatRelative(item.createdAt)} · decisión <code>{item.decisionId}</code>
          </p>
        </div>
        <Badge
          variant={
            item.verdict === "confirmed_fraud"
              ? "danger"
              : item.verdict === "false_positive"
                ? "success"
                : item.status === "escalated"
                  ? "info"
                  : "warning"
          }
        >
          {item.verdict ? VERDICT_LABELS[item.verdict] : STATUS_LABELS[item.status]}
        </Badge>
      </header>

      {decision && (
        <section className="case-section" aria-label="Por qué la IA bloqueó la transacción">
          <h3>Por qué la IA la bloqueó</h3>
          <div className="case-probability-row">
            <span className="bar-track case-probability-track">
              <span className="case-probability-fill" style={{ width: `${probability}%` }} />
            </span>
            <strong>{probability}%</strong>
          </div>
          <p className="case-hint">
            {decision.decision === "review"
              ? "Probabilidad de fraude intermedia: el modelo no está seguro, por eso pide una revisión humana."
              : "Probabilidad de fraude según el modelo para esta transacción."}{" "}
            Estos son los factores que más pesaron:
          </p>
          <ul className="case-factors">
            {factors.map((factor) => (
              <li key={factor.feature}>
                <span className={`shap-direction shap-${factor.direction}`} aria-hidden="true">
                  {factor.direction === "increases" ? "▲" : "▼"}
                </span>
                <span className="case-factor-label">{featureLabel(factor.feature)}</span>
                <span className="bar-track">
                  <span
                    className={`case-factor-bar ${factor.direction}`}
                    style={{ width: `${(factor.impact / maxImpact) * 100}%` }}
                  />
                </span>
                <span className="sr-only">
                  {factor.direction === "increases" ? "aumenta el riesgo" : "reduce el riesgo"}
                </span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {decision && (
        <section className="case-section" aria-label="Datos de la transacción">
          <h3>Datos de la transacción</h3>
          <dl className="case-facts">
            {transactionRows(decision.transaction).map((row) => (
              <div key={row.label} className={row.highlight ? "is-flagged" : undefined}>
                <dt>{row.label}</dt>
                <dd>{row.value}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      <section className="case-section" aria-label="Historial del caso">
        <h3>Historial</h3>
        <ol className="case-timeline">
          <li>
            <span className="timeline-dot is-ai" aria-hidden="true" />
            <div>
              <strong>SentinelAI bloqueó la transacción</strong>
              <small>{formatDateTime(item.createdAt)}</small>
            </div>
          </li>
          {item.notes.map((note, index) => (
            <li key={`${note.createdAt}-${index}`}>
              <span className="timeline-dot" aria-hidden="true" />
              <div>
                <strong>{note.author}</strong>
                <p>{note.content}</p>
                <small>{formatDateTime(note.createdAt)}</small>
              </div>
            </li>
          ))}
          {item.resolvedAt && (
            <li>
              <span
                className={`timeline-dot ${item.verdict === "confirmed_fraud" ? "is-fraud" : "is-ok"}`}
                aria-hidden="true"
              />
              <div>
                <strong>
                  {item.verdict === "confirmed_fraud"
                    ? "Fraude confirmado: bloqueo definitivo"
                    : "Transacción liberada"}
                  {item.assignedTo ? ` por ${item.assignedTo}` : ""}
                </strong>
                <small>{formatDateTime(item.resolvedAt)}</small>
              </div>
            </li>
          )}
        </ol>
      </section>

      {pending ? (
        <section className="case-actions" aria-label="Decisión del analista">
          {!item.assignedTo && (
            <button
              type="button"
              className="button button-outline case-take"
              disabled={busy}
              onClick={() => send({ status: "in_review", assignedTo: currentUser })}
            >
              <Icon name="check" size={15} /> Tomar caso
            </button>
          )}
          <label htmlFor="case-comment">Comentario del analista (opcional)</label>
          <textarea
            id="case-comment"
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            placeholder="Ej. El cliente confirmó la compra por teléfono."
            rows={2}
            disabled={busy}
          />
          <div className="case-action-buttons">
            <button
              type="button"
              className="button case-release"
              disabled={busy}
              onClick={() => resolve("false_positive")}
            >
              <Icon name="check" size={16} /> Liberar transacción
            </button>
            <button
              type="button"
              className="button button-danger"
              disabled={busy}
              onClick={() => resolve("confirmed_fraud")}
            >
              <Icon name="shield" size={16} /> Confirmar fraude
            </button>
          </div>
          {item.status !== "escalated" && (
            <button
              type="button"
              className="text-button case-escalate"
              disabled={busy}
              onClick={() =>
                send({ status: "escalated", assignedTo: item.assignedTo ?? currentUser })
              }
            >
              Escalar a un supervisor
            </button>
          )}
          {update.isError && (
            <p className="auth-error" role="alert">
              {update.error.message}
            </p>
          )}
        </section>
      ) : (
        <section
          className={`case-outcome ${item.verdict === "confirmed_fraud" ? "is-fraud" : "is-ok"}`}
          role="status"
        >
          <Icon name={item.verdict === "confirmed_fraud" ? "shield" : "check"} size={20} />
          <div>
            <strong>
              {item.verdict === "confirmed_fraud"
                ? "Bloqueo definitivo. El caso alimenta el reentrenamiento del modelo."
                : "La transacción fue liberada. Se registra como falsa alarma para mejorar el modelo."}
            </strong>
            {item.feedbackComment && <small>“{item.feedbackComment}”</small>}
          </div>
        </section>
      )}
    </article>
  );
}
