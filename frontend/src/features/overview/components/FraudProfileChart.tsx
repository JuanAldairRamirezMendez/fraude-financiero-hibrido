import { useState } from "react";

import { EVALUATION, type ProfileBucket, type ProfileDimension } from "@/features/evaluation/data";
import { formatNumber } from "@/lib/format";
import { COUNTRY_LABELS, MERCHANT_CATEGORY_LABELS, TRANSACTION_TYPE_LABELS } from "@/lib/labels";

const DIMENSIONS: ReadonlyArray<{ key: ProfileDimension; label: string }> = [
  { key: "merchantCategory", label: "Categoría" },
  { key: "transactionHour", label: "Hora" },
  { key: "transactionCountry", label: "País" },
  { key: "transactionType", label: "Tipo" },
];

const LABELS: Partial<Record<ProfileDimension, Record<string, string>>> = {
  merchantCategory: MERCHANT_CATEGORY_LABELS,
  transactionCountry: COUNTRY_LABELS,
  transactionType: TRANSACTION_TYPE_LABELS,
};

const percent = (value: number) => `${(value * 100).toFixed(2)}%`;

function bucketLabel(dimension: ProfileDimension, key: string) {
  if (dimension === "transactionHour") return `${key.padStart(2, "0")}:00`;
  return LABELS[dimension]?.[key] ?? key;
}

function HourColumns({ buckets, average }: { buckets: ProfileBucket[]; average: number }) {
  const width = 720;
  const height = 200;
  const pad = { top: 14, bottom: 24, left: 40 };
  const max = Math.max(...buckets.map((bucket) => bucket.fraudRate), average) * 1.1;
  const slot = (width - pad.left) / buckets.length;
  const y = (value: number) => pad.top + (1 - value / max) * (height - pad.top - pad.bottom);

  return (
    <svg
      className="profile-hours"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Tasa de fraude por hora del día"
    >
      <title>Tasa de fraude por hora del día</title>
      {buckets.map((bucket, index) => {
        const x = pad.left + index * slot + slot * 0.15;
        const top = y(bucket.fraudRate);
        const highlight = bucket.fraudRate > average;
        return (
          <g key={bucket.key}>
            <rect
              x={x}
              y={top}
              width={slot * 0.7}
              height={height - pad.bottom - top}
              rx="2"
              className={highlight ? "profile-col is-high" : "profile-col"}
            >
              <title>
                {`${bucketLabel("transactionHour", bucket.key)} · ${percent(bucket.fraudRate)} (${bucket.frauds} de ${formatNumber(bucket.transactions)})`}
              </title>
            </rect>
            {index % 3 === 0 && (
              <text x={x + slot * 0.35} y={height - 8} textAnchor="middle" className="curve-tick">
                {bucket.key.padStart(2, "0")}h
              </text>
            )}
          </g>
        );
      })}
      <line x1={pad.left} x2={width} y1={y(average)} y2={y(average)} className="curve-baseline" />
      <text x={pad.left - 6} y={y(average) + 3} textAnchor="end" className="curve-tick">
        {percent(average)}
      </text>
    </svg>
  );
}

export function FraudProfileChart() {
  const [dimension, setDimension] = useState<ProfileDimension>("merchantCategory");
  const average = EVALUATION.dataset.fraudRate;
  const buckets = EVALUATION.profile[dimension];
  const sorted =
    dimension === "transactionHour"
      ? buckets
      : [...buckets].sort((a, b) => b.fraudRate - a.fraudRate);
  const max = Math.max(...sorted.map((bucket) => bucket.fraudRate));

  return (
    <>
      <div className="profile-toolbar">
        <div className="metric-toggle" role="group" aria-label="Agrupar tasa de fraude por">
          {DIMENSIONS.map((item) => (
            <button
              key={item.key}
              type="button"
              aria-pressed={dimension === item.key}
              onClick={() => setDimension(item.key)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <span className="profile-average">
          <i aria-hidden="true" /> Promedio general: {percent(average)}
        </span>
      </div>

      {dimension === "transactionHour" ? (
        <HourColumns buckets={sorted} average={average} />
      ) : (
        <ol className="benchmark-bars profile-bars" aria-label="Tasa de fraude por grupo">
          {sorted.map((bucket) => (
            <li key={bucket.key}>
              <span className="benchmark-label">{bucketLabel(dimension, bucket.key)}</span>
              <span className="bar-track benchmark-track profile-track">
                <span
                  className={`benchmark-bar ${bucket.fraudRate > average ? "profile-bar-high" : "profile-bar"}`}
                  style={{ width: `${(bucket.fraudRate / max) * 100}%` }}
                />
                <span
                  className="profile-average-mark"
                  style={{ left: `${(average / max) * 100}%` }}
                  aria-hidden="true"
                />
              </span>
              <span className="benchmark-value">{percent(bucket.fraudRate)}</span>
            </li>
          ))}
        </ol>
      )}
    </>
  );
}
