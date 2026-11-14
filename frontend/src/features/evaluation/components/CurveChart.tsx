interface CurveChartProps {
  title: string;
  points: ReadonlyArray<readonly [number, number]>;
  xLabel: string;
  yLabel: string;
  marker?: { x: number; y: number; label: string };
  /** Línea de referencia de un clasificador aleatorio. */
  baseline?: "diagonal" | { y: number };
}

const W = 320;
const H = 240;
const PAD = { top: 12, right: 14, bottom: 36, left: 42 };
const PLOT_W = W - PAD.left - PAD.right;
const PLOT_H = H - PAD.top - PAD.bottom;

const sx = (x: number) => PAD.left + x * PLOT_W;
const sy = (y: number) => PAD.top + (1 - y) * PLOT_H;

export function CurveChart({ title, points, xLabel, yLabel, marker, baseline }: CurveChartProps) {
  const path = points
    .map(([x, y], index) => `${index === 0 ? "M" : "L"}${sx(x).toFixed(1)} ${sy(y).toFixed(1)}`)
    .join(" ");
  const ticks = [0, 0.25, 0.5, 0.75, 1];

  return (
    <svg className="curve-chart" viewBox={`0 0 ${W} ${H}`} role="img" aria-label={title}>
      <title>{title}</title>
      {ticks.map((tick) => (
        <g key={tick}>
          <line x1={sx(0)} x2={sx(1)} y1={sy(tick)} y2={sy(tick)} className="curve-grid" />
          <text x={PAD.left - 6} y={sy(tick) + 3} textAnchor="end" className="curve-tick">
            {tick}
          </text>
          <text x={sx(tick)} y={H - PAD.bottom + 14} textAnchor="middle" className="curve-tick">
            {tick}
          </text>
        </g>
      ))}
      {baseline === "diagonal" && (
        <line x1={sx(0)} y1={sy(0)} x2={sx(1)} y2={sy(1)} className="curve-baseline" />
      )}
      {baseline && baseline !== "diagonal" && (
        <line
          x1={sx(0)}
          x2={sx(1)}
          y1={sy(baseline.y)}
          y2={sy(baseline.y)}
          className="curve-baseline"
        />
      )}
      <path d={path} className="curve-line" />
      {marker && (
        <g>
          <circle cx={sx(marker.x)} cy={sy(marker.y)} r="5" className="curve-marker" />
          <text
            x={sx(marker.x) + (marker.x > 0.7 ? -8 : 8)}
            y={sy(marker.y) + (marker.y > 0.85 ? 16 : -8)}
            textAnchor={marker.x > 0.7 ? "end" : "start"}
            className="curve-marker-label"
          >
            {marker.label}
          </text>
        </g>
      )}
      <text x={PAD.left + PLOT_W / 2} y={H - 4} textAnchor="middle" className="curve-axis">
        {xLabel}
      </text>
      <text
        x={12}
        y={PAD.top + PLOT_H / 2}
        textAnchor="middle"
        transform={`rotate(-90 12 ${PAD.top + PLOT_H / 2})`}
        className="curve-axis"
      >
        {yLabel}
      </text>
    </svg>
  );
}
