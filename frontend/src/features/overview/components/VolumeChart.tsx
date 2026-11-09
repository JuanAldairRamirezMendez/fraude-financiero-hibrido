export function VolumeChart() {
  return (
    <svg
      className="volume-chart"
      viewBox="0 0 900 260"
      role="img"
      aria-labelledby="volume-chart-title"
    >
      <title id="volume-chart-title">
        Gráfico ilustrativo de volumen de transacciones frente a eventos de fraude en las últimas 24
        horas
      </title>
      <defs>
        <linearGradient id="blueFill" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#2563EB" stopOpacity=".22" />
          <stop offset="1" stopColor="#2563EB" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[30, 80, 130, 180, 230].map((y) => (
        <line key={y} x1="58" x2="850" y1={y} y2={y} stroke="#E5E7EB" strokeDasharray="3 5" />
      ))}
      <path
        d="M58 204 C100 186 118 195 154 167 S220 144 251 157 S309 132 348 117 S409 126 447 96 S510 115 552 83 S615 76 655 91 S720 54 758 66 S815 40 850 48 L850 230 L58 230Z"
        fill="url(#blueFill)"
      />
      <path
        d="M58 204 C100 186 118 195 154 167 S220 144 251 157 S309 132 348 117 S409 126 447 96 S510 115 552 83 S615 76 655 91 S720 54 758 66 S815 40 850 48"
        fill="none"
        stroke="#2563EB"
        strokeWidth="3"
      />
      <path
        d="M58 220 C111 217 134 208 175 211 S245 194 284 204 S356 187 401 191 S471 172 510 184 S577 159 621 168 S689 139 732 150 S797 119 850 127"
        fill="none"
        stroke="#EF4444"
        strokeWidth="2.5"
      />
      {[
        [58, 204],
        [154, 167],
        [251, 157],
        [348, 117],
        [447, 96],
        [552, 83],
        [655, 91],
        [758, 66],
        [850, 48],
      ].map(([x, y]) => (
        <circle
          key={`${x}-${y}`}
          cx={x}
          cy={y}
          r="3.5"
          fill="#fff"
          stroke="#2563EB"
          strokeWidth="2"
        />
      ))}
      {[
        [58, 220],
        [175, 211],
        [284, 204],
        [401, 191],
        [510, 184],
        [621, 168],
        [732, 150],
        [850, 127],
      ].map(([x, y]) => (
        <circle
          key={`${x}-${y}`}
          cx={x}
          cy={y}
          r="3"
          fill="#fff"
          stroke="#EF4444"
          strokeWidth="2"
        />
      ))}
      <text x="58" y="17" fill="#6B7280" fontSize="9">
        TRANSACTIONS
      </text>
      <text x="850" y="17" textAnchor="end" fill="#6B7280" fontSize="9">
        FRAUD EVENTS: 0–150
      </text>
      <g className="chart-point pinned-tooltip">
        <line x1="655" x2="655" y1="24" y2="230" stroke="#9CA3AF" strokeDasharray="4 4" />
        <circle cx="655" cy="91" r="5" fill="#fff" stroke="#2563EB" strokeWidth="3" />
        <circle cx="655" cy="164" r="4" fill="#fff" stroke="#EF4444" strokeWidth="3" />
        <g transform="translate(570 12)">
          <rect width="170" height="62" rx="7" fill="#111827" />
          <text x="12" y="21" fill="#9CA3AF" fontSize="10">
            14:00:00 UTC • Jun 12
          </text>
          <circle cx="14" cy="38" r="3" fill="#2563EB" />
          <text x="23" y="42" fill="white" fontSize="11">
            Volume
          </text>
          <text x="153" y="42" fill="white" textAnchor="end" fontSize="11" fontWeight="600">
            82,417
          </text>
          <circle cx="14" cy="53" r="3" fill="#EF4444" />
          <text x="23" y="57" fill="white" fontSize="11">
            Fraud
          </text>
          <text x="153" y="57" fill="white" textAnchor="end" fontSize="11" fontWeight="600">
            91 alerts
          </text>
        </g>
      </g>
      {["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"].map((time, index) => (
        <text
          key={time}
          x={58 + index * 132}
          y="252"
          textAnchor={index === 0 ? "start" : index === 6 ? "end" : "middle"}
          fill="#6B7280"
          fontSize="10"
        >
          {time}
        </text>
      ))}
      {["100k", "75k", "50k", "25k", "0"].map((label, index) => (
        <text key={label} x="48" y={34 + index * 50} textAnchor="end" fill="#6B7280" fontSize="10">
          {label}
        </text>
      ))}
    </svg>
  );
}
