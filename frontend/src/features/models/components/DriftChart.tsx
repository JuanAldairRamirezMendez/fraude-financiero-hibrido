export function DriftChart() {
  return (
    <svg
      className="drift-chart"
      viewBox="0 0 1000 300"
      role="img"
      aria-labelledby="drift-chart-title"
    >
      <title id="drift-chart-title">
        Distribución ilustrativa del monto de transacción actual frente a los datos de entrenamiento
      </title>
      <defs>
        <linearGradient id="currentFill" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#2563EB" stopOpacity=".3" />
          <stop offset="1" stopColor="#2563EB" stopOpacity=".02" />
        </linearGradient>
        <linearGradient id="trainingFill" x1="0" y1="0" x2="0" y2="1">
          <stop stopColor="#06B6D4" stopOpacity=".26" />
          <stop offset="1" stopColor="#06B6D4" stopOpacity=".01" />
        </linearGradient>
      </defs>
      {[30, 75, 120, 165, 210, 255].map((y) => (
        <line key={y} x1="62" x2="954" y1={y} y2={y} stroke="#E5E7EB" strokeDasharray="3 5" />
      ))}
      <path
        d="M62 255 C99 250 126 230 164 190 S218 91 269 56 S343 50 397 83 S469 143 520 178 S606 218 659 229 S756 242 807 248 S900 252 954 254 L954 255Z"
        fill="url(#trainingFill)"
        stroke="#06B6D4"
        strokeWidth="2.5"
      />
      <path
        d="M62 255 C105 248 128 235 168 216 S234 162 278 128 S352 92 397 111 S466 149 512 179 S580 190 626 199 S699 211 749 225 S858 244 954 251 L954 255Z"
        fill="url(#currentFill)"
        stroke="#2563EB"
        strokeWidth="2.5"
      />
      {[
        [62, 255],
        [168, 216],
        [278, 128],
        [397, 111],
        [512, 179],
        [626, 199],
        [749, 225],
        [954, 251],
      ].map(([x, y]) => (
        <circle
          key={`current-${x}-${y}`}
          cx={x}
          cy={y}
          r="3.5"
          fill="#fff"
          stroke="#2563EB"
          strokeWidth="2"
        />
      ))}
      {[
        [62, 255],
        [164, 190],
        [269, 56],
        [397, 83],
        [520, 178],
        [659, 229],
        [807, 248],
        [954, 254],
      ].map(([x, y]) => (
        <circle
          key={`training-${x}-${y}`}
          cx={x}
          cy={y}
          r="3"
          fill="#fff"
          stroke="#06B6D4"
          strokeWidth="2"
        />
      ))}
      <line
        x1="397"
        x2="397"
        y1="24"
        y2="255"
        stroke="#F59E0B"
        strokeWidth="2"
        strokeDasharray="6 5"
      />
      <g transform="translate(407 34)">
        <rect width="101" height="25" rx="4" fill="#FFFBEB" />
        <text x="50" y="16" textAnchor="middle" fill="#B45309" fontSize="10" fontWeight="600">
          Drift threshold • $150
        </text>
      </g>
      <g transform="translate(515 72)">
        <rect width="176" height="76" rx="7" fill="#111827" />
        <text x="13" y="22" fill="#9CA3AF" fontSize="10">
          Amount range • $200–$220
        </text>
        <circle cx="15" cy="40" r="3" fill="#2563EB" />
        <text x="25" y="44" fill="white" fontSize="11">
          Current
        </text>
        <text x="160" y="44" textAnchor="end" fill="white" fontSize="11" fontWeight="600">
          244 transactions
        </text>
        <circle cx="15" cy="59" r="3" fill="#06B6D4" />
        <text x="25" y="63" fill="white" fontSize="11">
          Training
        </text>
        <text x="160" y="63" textAnchor="end" fill="white" fontSize="11" fontWeight="600">
          183 transactions
        </text>
      </g>
      {["$0", "$50", "$100", "$150", "$200", "$250", "$300", "$350", "$400"].map((tick, index) => (
        <text
          key={tick}
          x={62 + index * 111.5}
          y="281"
          textAnchor={index === 0 ? "start" : index === 8 ? "end" : "middle"}
          fill="#6B7280"
          fontSize="10"
        >
          {tick}
        </text>
      ))}
      {["700", "560", "420", "280", "140", "0"].map((tick, index) => (
        <text key={tick} x="50" y={34 + index * 45} textAnchor="end" fill="#6B7280" fontSize="10">
          {tick}
        </text>
      ))}
    </svg>
  );
}
