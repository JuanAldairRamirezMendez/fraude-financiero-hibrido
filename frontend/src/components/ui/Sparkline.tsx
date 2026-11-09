interface SparklineProps {
  points: string;
  tone: string;
}

export function Sparkline({ points, tone }: SparklineProps) {
  return (
    <svg
      className={`sparkline spark-${tone}`}
      viewBox="0 0 112 26"
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
    >
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="2" />
      <polyline points={`0,26 ${points} 112,26`} fill="currentColor" opacity=".08" />
    </svg>
  );
}
