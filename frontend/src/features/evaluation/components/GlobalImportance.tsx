import { featureLabel } from "@/lib/labels";

import { EVALUATION } from "../data";

const TOP = 10;

export function GlobalImportance() {
  const items = EVALUATION.globalImportance.slice(0, TOP);
  const max = Math.max(...items.map((item) => item.share));

  return (
    <ol className="importance-list" aria-label="Variables más influyentes del modelo">
      {items.map((item) => (
        <li key={item.feature}>
          <span className="benchmark-label">{featureLabel(item.feature)}</span>
          <span className="bar-track benchmark-track">
            <span
              className="benchmark-bar family-bar-classic"
              style={{ width: `${(item.share / max) * 100}%` }}
            />
          </span>
          <span className="benchmark-value">{(item.share * 100).toFixed(1)}%</span>
        </li>
      ))}
    </ol>
  );
}
