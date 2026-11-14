import type { RiskLevel } from "@/types/common";

interface RiskGaugeProps {
  score: number;
  level: RiskLevel;
  /** Umbrales de la política (0-1); las zonas de color se dibujan según ellos. */
  reviewThreshold: number;
  blockThreshold: number;
}

const levelLabel: Record<RiskLevel, string> = {
  low: "Riesgo bajo",
  medium: "Riesgo medio",
  high: "Riesgo alto",
};

const CX = 130;
const CY = 135;
const R = 95;
const GAP = 0.012;

function point(fraction: number) {
  const angle = Math.PI * (1 - fraction);
  return { x: CX + R * Math.cos(angle), y: CY - R * Math.sin(angle) };
}

function arc(from: number, to: number) {
  const start = point(from);
  const end = point(to);
  return `M${start.x.toFixed(1)} ${start.y.toFixed(1)} A${R} ${R} 0 0 1 ${end.x.toFixed(1)} ${end.y.toFixed(1)}`;
}

export function RiskGauge({ score, level, reviewThreshold, blockThreshold }: RiskGaugeProps) {
  const angle = (score / 100) * 180 - 90;
  const review = Math.min(Math.max(reviewThreshold, 0), 1);
  const block = Math.min(Math.max(blockThreshold, review), 1);

  return (
    <div className="gauge-wrap">
      <svg
        viewBox="0 0 260 160"
        className="gauge"
        role="img"
        aria-label={`${levelLabel[level]}: ${score} de 100`}
      >
        <title>{`${levelLabel[level]}: ${score} de 100`}</title>
        <path d={arc(0, 1)} fill="none" stroke="#E5E7EB" strokeWidth="20" />
        {review > GAP && (
          <path d={arc(0, review - GAP / 2)} fill="none" stroke="#10B981" strokeWidth="20" />
        )}
        {block - review > GAP && (
          <path
            d={arc(review + GAP / 2, block - GAP / 2)}
            fill="none"
            stroke="#F59E0B"
            strokeWidth="20"
          />
        )}
        {1 - block > GAP && (
          <path d={arc(block + GAP / 2, 1)} fill="none" stroke="#EF4444" strokeWidth="20" />
        )}
        <g transform={`rotate(${angle} ${CX} ${CY})`}>
          <path d="M130 135 126 60 130 50 134 60Z" fill="#1F2937" />
        </g>
        <circle cx={CX} cy={CY} r="13" fill="#1F2937" />
        <circle cx={CX} cy={CY} r="5" fill="white" />
        <text x="28" y="158" className="gauge-tick">
          0
        </text>
        <text x="222" y="158" className="gauge-tick">
          100
        </text>
      </svg>
      <div className="gauge-readout" aria-hidden="true">
        <strong>{score}%</strong>
        <span>Probabilidad de fraude</span>
      </div>
      <div className="gauge-zones">
        <span>
          <i className="green" />
          Aprobar &lt; {Math.round(review * 100)}%
        </span>
        {block - review > GAP && (
          <span>
            <i className="yellow" />
            Revisar
          </span>
        )}
        <span>
          <i className="red" />
          Bloquear ≥ {Math.round(block * 100)}%
        </span>
      </div>
    </div>
  );
}
