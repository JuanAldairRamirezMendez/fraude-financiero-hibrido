import { useEffect, useRef } from "react";

import { formatCurrency } from "@/lib/format";
import { GENDER_LABELS, categoryLabel } from "@/lib/labels";

import raw from "../anatomy.json";

/**
 * Compras reales de una tarjeta del periodo de prueba de Sparkov alrededor de un episodio de
 * fraude, con el puntaje que el modelo dio a cada una. Generado por
 * `backend/scripts/build_sparkov_artifacts.py` (la tarjeta del escenario "Fraude probable").
 */
interface Purchase {
  time: string;
  amount: number;
  category: string;
  score: number;
  isFraud: boolean;
}

interface Anatomy {
  cardId: string;
  gender: string;
  age: number;
  city: string;
  state: string;
  threshold: number;
  start: string;
  end: string;
  before: { purchases: number; averageAmount: number; maxAmount: number };
  burst: { purchases: number; totalAmount: number; hours: number; firstAt: string };
  model: { fraudsBlocked: number; frauds: number; falseAlarms: number; legitimate: number };
  purchases: Purchase[];
}

const DATA = raw as Anatomy;
const MONTHS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];

const time = (iso: string) => new Date(iso).getTime();
const two = (value: number) => String(value).padStart(2, "0");
function when(iso: string) {
  const date = new Date(iso);
  return `${date.getDate()} ${MONTHS[date.getMonth()]} ${two(date.getHours())}:${two(date.getMinutes())}`;
}
const blocked = (purchase: Purchase) => purchase.score >= DATA.threshold * 100;

const WIDTH = 760;
const HEIGHT = 250;
const PAD = { top: 22, right: 12, bottom: 30, left: 52 };

function Timeline() {
  const t0 = time(DATA.start);
  const t1 = time(DATA.end);
  const maxAmount = Math.max(...DATA.purchases.map((purchase) => purchase.amount));
  const plotHeight = HEIGHT - PAD.top - PAD.bottom;
  const x = (iso: string) =>
    PAD.left + ((time(iso) - t0) / (t1 - t0)) * (WIDTH - PAD.left - PAD.right);
  // Escala de raíz cuadrada: las compras pequeñas siguen siendo visibles junto a las grandes.
  const y = (amount: number) =>
    PAD.top + (1 - Math.sqrt(amount) / Math.sqrt(maxAmount)) * plotHeight;
  const baseline = PAD.top + plotHeight;
  const ticks = [10, 100, 500, 1_000].filter((value) => value <= maxAmount);
  const frauds = DATA.purchases.filter((purchase) => purchase.isFraud);
  const burstStart = x(frauds[0].time);
  const burstEnd = x(frauds[frauds.length - 1].time);

  const days: string[] = [];
  const firstDay = new Date(DATA.start);
  firstDay.setHours(24, 0, 0, 0);
  for (let day = firstDay.getTime(); day < t1; day += 86_400_000)
    days.push(new Date(day).toISOString());

  return (
    <svg
      className="anatomy-chart"
      viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
      role="img"
      aria-label={`Compras de la tarjeta ${DATA.cardId}: ${DATA.purchases.length} compras, ${DATA.burst.purchases} de ellas fraudulentas en una ráfaga de ${DATA.burst.hours} horas.`}
    >
      <rect
        x={burstStart - 6}
        y={PAD.top - 16}
        width={burstEnd - burstStart + 12}
        height={plotHeight + 16}
        className="anatomy-burst"
        rx="6"
      />
      <text x={burstStart} y={PAD.top - 5} className="anatomy-burst-label">
        Ráfaga de fraude
      </text>
      {ticks.map((value) => (
        <g key={value}>
          <line
            x1={PAD.left}
            x2={WIDTH - PAD.right}
            y1={y(value)}
            y2={y(value)}
            className="anatomy-grid"
          />
          <text x={PAD.left - 6} y={y(value) + 3} textAnchor="end" className="curve-tick">
            {value >= 1_000 ? "1 mil" : value}
          </text>
        </g>
      ))}
      <line
        x1={PAD.left}
        x2={WIDTH - PAD.right}
        y1={baseline}
        y2={baseline}
        className="anatomy-axis"
      />
      {days.map((day) => (
        <text key={day} x={x(day)} y={HEIGHT - 10} textAnchor="middle" className="curve-tick">
          {new Date(day).getDate()} {MONTHS[new Date(day).getMonth()]}
        </text>
      ))}
      {DATA.purchases.map((purchase) => {
        const cx = x(purchase.time);
        const cy = y(purchase.amount);
        const tone = blocked(purchase) ? "is-blocked" : "is-approved";
        return (
          <g key={purchase.time} className={`anatomy-mark ${tone}`}>
            <title>
              {`${when(purchase.time)} · ${categoryLabel(purchase.category)} · ${formatCurrency(purchase.amount)} · puntaje ${purchase.score}% · ${blocked(purchase) ? "bloqueada" : "aprobada"} · era ${purchase.isFraud ? "fraude" : "legítima"}`}
            </title>
            <line x1={cx} x2={cx} y1={baseline} y2={cy} className="anatomy-stem" />
            {purchase.isFraud && <circle cx={cx} cy={cy} r="8.5" className="anatomy-ring" />}
            <circle cx={cx} cy={cy} r="5" className="anatomy-dot" />
            {/* Área de hover más grande que la marca. */}
            <circle cx={cx} cy={cy} r="12" className="anatomy-hit" />
          </g>
        );
      })}
      <text
        x={12}
        y={PAD.top + plotHeight / 2}
        className="curve-tick"
        transform={`rotate(-90 12 ${PAD.top + plotHeight / 2})`}
        textAnchor="middle"
      >
        Monto (USD)
      </text>
    </svg>
  );
}

export function FraudAnatomy() {
  const wrapRef = useRef<HTMLDivElement>(null);
  // En celulares el gráfico se desplaza: se abre mostrando la ráfaga, que está al final.
  useEffect(() => {
    const wrap = wrapRef.current;
    if (wrap) wrap.scrollLeft = wrap.scrollWidth;
  }, []);
  const missed = DATA.purchases.filter((purchase) => purchase.isFraud && !blocked(purchase));
  const bigLegit = DATA.purchases
    .filter((purchase) => !purchase.isFraud && !blocked(purchase))
    .sort((a, b) => b.amount - a.amount)[0];

  return (
    <div className="anatomy">
      <p className="anatomy-card">
        Tarjeta <strong>{DATA.cardId}</strong> · {GENDER_LABELS[DATA.gender] ?? DATA.gender},{" "}
        {DATA.age} años · {DATA.city}, {DATA.state}
      </p>

      <dl className="anatomy-stats">
        <div>
          <dt>Antes del fraude</dt>
          <dd>{DATA.before.purchases} compras normales</dd>
          <small>Promedio de {formatCurrency(DATA.before.averageAmount)} por compra</small>
        </div>
        <div className="is-burst">
          <dt>La ráfaga</dt>
          <dd>
            {DATA.burst.purchases} compras en {Math.round(DATA.burst.hours)} h
          </dd>
          <small>
            {formatCurrency(DATA.burst.totalAmount)} desde el {when(DATA.burst.firstAt)}
          </small>
        </div>
        <div className="is-model">
          <dt>El modelo</dt>
          <dd>
            Bloqueó {DATA.model.fraudsBlocked} de {DATA.model.frauds} fraudes
          </dd>
          <small>
            {DATA.model.falseAlarms === 0
              ? `Ninguna falsa alarma en ${DATA.model.legitimate} compras legítimas`
              : `${DATA.model.falseAlarms} falsas alarmas en ${DATA.model.legitimate} compras legítimas`}
          </small>
        </div>
      </dl>

      {/* En pantallas angostas el gráfico conserva un ancho legible y se desplaza en su tarjeta. */}
      <div className="anatomy-chart-wrap" ref={wrapRef}>
        <Timeline />
      </div>

      <div className="anatomy-legend" aria-hidden="true">
        <span>
          <i className="legend-dot is-approved" /> Aprobada por el modelo
        </span>
        <span>
          <i className="legend-dot is-blocked" /> Bloqueada por el modelo
        </span>
        <span>
          <i className="legend-ring" /> Era fraude (etiqueta real)
        </span>
      </div>

      <p className="benchmark-note eval-note">
        {bigLegit && (
          <>
            Una compra grande aislada ({formatCurrency(bigLegit.amount)}, el {when(bigLegit.time)})
            se aprobó: para esta tarjeta no es rara.{" "}
          </>
        )}
        Lo que delató el fraude fue el <strong>comportamiento</strong>: {DATA.burst.purchases}{" "}
        compras y {formatCurrency(DATA.burst.totalAmount)} en menos de{" "}
        {Math.ceil(DATA.burst.hours / 24)} días, cuando la tarjeta gastaba{" "}
        {formatCurrency(DATA.before.averageAmount)} por compra.
        {missed.length > 0 &&
          ` Solo se le escapó ${missed
            .map(
              (purchase) =>
                `una compra de ${formatCurrency(purchase.amount)} (${categoryLabel(purchase.category).toLowerCase()}, puntaje ${purchase.score}%)`,
            )
            .join(" y ")}${
            missed.every((purchase) => purchase.amount < DATA.before.averageAmount)
              ? ": un monto menor al promedio de la tarjeta, que por sí solo parece normal."
              : "."
          }`}
      </p>

      <details className="anatomy-table">
        <summary>Ver las {DATA.purchases.length} compras como tabla</summary>
        <table>
          <caption className="sr-only">Compras de la tarjeta {DATA.cardId}</caption>
          <thead>
            <tr>
              <th scope="col">Fecha y hora</th>
              <th scope="col">Comercio</th>
              <th scope="col">Monto</th>
              <th scope="col">Puntaje</th>
              <th scope="col">Decisión</th>
              <th scope="col">Etiqueta real</th>
            </tr>
          </thead>
          <tbody>
            {DATA.purchases.map((purchase) => (
              <tr key={purchase.time}>
                <td>{when(purchase.time)}</td>
                <td>{categoryLabel(purchase.category)}</td>
                <td>{formatCurrency(purchase.amount)}</td>
                <td>{purchase.score}%</td>
                <td>{blocked(purchase) ? "Bloqueada" : "Aprobada"}</td>
                <td>{purchase.isFraud ? "Fraude" : "Legítima"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </div>
  );
}
