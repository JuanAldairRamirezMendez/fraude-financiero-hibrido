import { formatCurrency, formatRelative } from "@/lib/format";
import { categoryLabel } from "@/lib/labels";

import { STATUS_LABELS, VERDICT_LABELS, type FraudCase } from "../api";

interface CaseQueueProps {
  cases: readonly FraudCase[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function caseTone(item: FraudCase) {
  if (item.verdict === "confirmed_fraud") return "fraud";
  if (item.verdict === "false_positive") return "released";
  return item.status;
}

export function CaseQueue({ cases, selectedId, onSelect }: CaseQueueProps) {
  return (
    <ul className="case-queue" aria-label="Cola de casos">
      {cases.map((item) => {
        const transaction = item.decision?.transaction ?? {};
        // Casos nuevos (Sparkov) y antiguos (modelo anterior) guardan campos distintos.
        const amount = Number(transaction.amount ?? transaction.transactionAmount ?? 0);
        const category = String(transaction.category ?? transaction.merchantCategory ?? "");
        const where = String(transaction.cardId ?? transaction.transactionCountry ?? "");
        const probability = item.decision ? Math.round(item.decision.probability * 100) : null;
        const selected = item.id === selectedId;

        return (
          <li key={item.id}>
            <button
              type="button"
              className={`case-item tone-${caseTone(item)} ${selected ? "is-selected" : ""}`.trim()}
              aria-pressed={selected}
              onClick={() => onSelect(item.id)}
            >
              <span className="case-item-top">
                <strong>{item.caseNumber}</strong>
                <time dateTime={item.createdAt}>{formatRelative(item.createdAt)}</time>
              </span>
              <span className="case-item-main">
                <span className="case-amount">{formatCurrency(amount)}</span>
                {probability !== null && (
                  <span className="case-probability" title="Probabilidad de fraude según el modelo">
                    {probability}%
                  </span>
                )}
              </span>
              <span className="case-item-meta">
                {categoryLabel(category)}
                {where && ` · ${where}`}
              </span>
              <span className="case-item-bottom">
                <span className={`case-status status-${caseTone(item)}`}>
                  {item.verdict ? VERDICT_LABELS[item.verdict] : STATUS_LABELS[item.status]}
                </span>
                {item.assignedTo && <span className="case-assignee">{item.assignedTo}</span>}
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  );
}
