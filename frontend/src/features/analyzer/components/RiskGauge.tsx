import type { RiskLevel } from "@/types/common";

interface RiskGaugeProps {
  score: number;
  level: RiskLevel;
}

const levelLabel: Record<RiskLevel, string> = {
  low: "Riesgo bajo",
  medium: "Riesgo medio",
  high: "Riesgo alto",
};

export function RiskGauge({ score, level }: RiskGaugeProps) {
  const angle = (score / 100) * 180 - 90;

  return (
    <div className="gauge-wrap">
      <svg
        viewBox="0 0 260 160"
        className="gauge"
        role="img"
        aria-label={`${levelLabel[level]}: ${score} de 100`}
      >
        <title>{`${levelLabel[level]}: ${score} de 100`}</title>
        <path
          d="M35 135 A95 95 0 0 1 225 135"
          fill="none"
          stroke="#E5E7EB"
          strokeWidth="20"
          strokeLinecap="round"
        />
        <path
          d="M35 135 A95 95 0 0 1 92 48"
          fill="none"
          stroke="#10B981"
          strokeWidth="20"
          strokeLinecap="round"
        />
        <path d="M96 46 A95 95 0 0 1 166 46" fill="none" stroke="#F59E0B" strokeWidth="20" />
        <path
          d="M170 48 A95 95 0 0 1 225 135"
          fill="none"
          stroke="#EF4444"
          strokeWidth="20"
          strokeLinecap="round"
        />
        <g transform={`rotate(${angle} 130 135)`}>
          <path d="M130 135 126 60 130 50 134 60Z" fill="#1F2937" />
        </g>
        <circle cx="130" cy="135" r="13" fill="#1F2937" />
        <circle cx="130" cy="135" r="5" fill="white" />
        <text x="28" y="158" className="gauge-tick">
          0
        </text>
        <text x="222" y="158" className="gauge-tick">
          100
        </text>
      </svg>
      <div className="gauge-readout" aria-hidden="true">
        <strong>{score}%</strong>
        <span>Risk score</span>
      </div>
      <div className="gauge-zones">
        <span>
          <i className="green" />
          Low
        </span>
        <span>
          <i className="yellow" />
          Medium
        </span>
        <span>
          <i className="red" />
          High
        </span>
      </div>
    </div>
  );
}
