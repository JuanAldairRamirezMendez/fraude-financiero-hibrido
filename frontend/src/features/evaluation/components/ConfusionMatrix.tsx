import { formatNumber } from "@/lib/format";

import type { ConfusionCounts } from "../data";

interface ConfusionMatrixProps {
  counts: ConfusionCounts;
}

export function ConfusionMatrix({ counts }: ConfusionMatrixProps) {
  const cells = [
    {
      id: "tp",
      value: counts.tp,
      title: "Fraude detectado",
      hint: "Era fraude y se retuvo o bloqueó",
      tone: "good",
    },
    {
      id: "fn",
      value: counts.fn,
      title: "Fraude no detectado",
      hint: "Era fraude y se aprobó",
      tone: "bad",
    },
    {
      id: "fp",
      value: counts.fp,
      title: "Falsa alarma",
      hint: "Era legítima y se retuvo o bloqueó",
      tone: "warn",
    },
    {
      id: "tn",
      value: counts.tn,
      title: "Legítima aprobada",
      hint: "Era legítima y se aprobó",
      tone: "good",
    },
  ] as const;

  return (
    <div className="confusion" role="table" aria-label="Matriz de confusión">
      <div role="row" className="confusion-head">
        <span role="columnheader" />
        <span role="columnheader">Bloqueada</span>
        <span role="columnheader">Aprobada</span>
      </div>
      <div role="row" className="confusion-row">
        <span role="rowheader">Era fraude</span>
        {[cells[0], cells[1]].map((cell) => (
          <div role="cell" key={cell.id} className={`confusion-cell tone-${cell.tone}`}>
            <strong>{formatNumber(cell.value)}</strong>
            <span>{cell.title}</span>
            <small>{cell.hint}</small>
          </div>
        ))}
      </div>
      <div role="row" className="confusion-row">
        <span role="rowheader">Era legítima</span>
        {[cells[2], cells[3]].map((cell) => (
          <div role="cell" key={cell.id} className={`confusion-cell tone-${cell.tone}`}>
            <strong>{formatNumber(cell.value)}</strong>
            <span>{cell.title}</span>
            <small>{cell.hint}</small>
          </div>
        ))}
      </div>
    </div>
  );
}
