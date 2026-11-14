import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { formatCurrency, formatNumber } from "@/lib/format";
import { featureLabel } from "@/lib/labels";

import { ConfusionMatrix } from "./components/ConfusionMatrix";
import { CurveChart } from "./components/CurveChart";
import { GlobalImportance } from "./components/GlobalImportance";
import { EVALUATION, cheapestThreshold, costAt, countsAt, metricsOf } from "./data";

const CALIBRATED = EVALUATION.calibratedThreshold;
const DEFAULT_REVIEW_COST = 25;
const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

export default function EvaluationPage() {
  const [threshold, setThreshold] = useState(CALIBRATED);
  const [reviewCost, setReviewCost] = useState(DEFAULT_REVIEW_COST);

  const isCalibrated = threshold === CALIBRATED;
  const counts = isCalibrated ? EVALUATION.calibrated : countsAt(threshold);
  const metrics = metricsOf(counts);
  const cost = costAt(counts, reviewCost);
  const cheapest = cheapestThreshold(reviewCost);
  const cheapestCost = costAt(cheapest, reviewCost);
  const { dataset } = EVALUATION;
  const topFeatures = EVALUATION.globalImportance.slice(0, 2);

  return (
    <div className="evaluation-page">
      <div className="analyzer-intro">
        <div>
          <h2 className="section-title">¿Funciona con datos que nunca vio?</h2>
          <p className="section-subtitle">
            {formatNumber(dataset.testRows)} transacciones reales de prueba ({dataset.split}), con{" "}
            {dataset.testFrauds} fraudes. El modelo no las usó para entrenar.
          </p>
        </div>
        <Badge variant="info">
          AUC-ROC {EVALUATION.aucRoc.toFixed(3)} · {formatNumber(dataset.testRows)} transacciones
        </Badge>
      </div>

      <div className="eval-kpis">
        <Card className="eval-kpi">
          <span>Fraudes detectados</span>
          <strong>
            {counts.tp} <small>/ {dataset.testFrauds}</small>
          </strong>
          <em>{percent(metrics.recall)} del fraude real (recall)</em>
        </Card>
        <Card className="eval-kpi">
          <span>Falsas alarmas</span>
          <strong>{formatNumber(counts.fp)}</strong>
          <em>
            {percent(counts.fp / (counts.fp + counts.tn))} de las{" "}
            {formatNumber(counts.fp + counts.tn)} legítimas
          </em>
        </Card>
        <Card className="eval-kpi">
          <span>Precisión de las alertas</span>
          <strong>{percent(metrics.precision)}</strong>
          <em>{(metrics.precision * 10).toFixed(1)} de cada 10 alertas son fraude real</em>
        </Card>
        <Card className="eval-kpi">
          <span>F1-Score</span>
          <strong>{metrics.f1.toFixed(3)}</strong>
          <em>Equilibrio entre precisión y recall</em>
        </Card>
      </div>

      <div className="eval-grid">
        <Card className="chart-card eval-threshold">
          <ChartHeader
            title="Umbral de bloqueo"
            subtitle="Desde este umbral la transacción se bloquea y pasa a la revisión de casos."
          />
          <div className="threshold-control">
            <label htmlFor="threshold-slider">
              Umbral: <strong>{threshold.toFixed(isCalibrated ? 3 : 2)}</strong>
              {isCalibrated && <span className="threshold-tag">calibrado</span>}
            </label>
            <input
              id="threshold-slider"
              type="range"
              min={0.01}
              max={0.99}
              step={0.01}
              value={threshold}
              onChange={(event) => setThreshold(Number(event.target.value))}
            />
            <div className="threshold-scale" aria-hidden="true">
              <span>Detecta más fraude · más falsas alarmas</span>
              <span>Menos falsas alarmas · se escapa más fraude</span>
            </div>
            {!isCalibrated && (
              <button
                type="button"
                className="text-button"
                onClick={() => setThreshold(CALIBRATED)}
              >
                Volver al umbral calibrado ({CALIBRATED.toFixed(3)})
              </button>
            )}
          </div>
          <ConfusionMatrix counts={counts} />
        </Card>

        <Card className="chart-card eval-cost">
          <ChartHeader
            title="Impacto económico"
            subtitle="El mejor umbral depende de lo que cuesta cada error al negocio."
          />
          <div className="cost-input">
            <label htmlFor="review-cost">Costo de revisar una alerta (US$)</label>
            <input
              id="review-cost"
              type="number"
              min={0}
              max={1000}
              step={5}
              value={reviewCost}
              onChange={(event) => setReviewCost(Math.max(0, Number(event.target.value) || 0))}
            />
            <small>
              Supuesto editable. El fraude no detectado se valora con el monto real de cada
              transacción.
            </small>
          </div>
          <dl className="cost-list">
            <div>
              <dt>Fraude evitado</dt>
              <dd className="cost-good">{formatCurrency(counts.caughtAmount)}</dd>
            </div>
            <div>
              <dt>Fraude no detectado</dt>
              <dd className="cost-bad">{formatCurrency(cost.missed)}</dd>
            </div>
            <div>
              <dt>
                Revisión de {formatNumber(metrics.alerts)} alertas × {formatCurrency(reviewCost)}
              </dt>
              <dd>{formatCurrency(cost.reviews)}</dd>
            </div>
            <div className="cost-total">
              <dt>Costo total</dt>
              <dd>{formatCurrency(cost.total)}</dd>
            </div>
          </dl>
          <div className="cost-suggestion">
            <p>
              Con estos costos, el umbral más económico es{" "}
              <strong>{cheapest.threshold.toFixed(2)}</strong> (costo total{" "}
              {formatCurrency(cheapestCost.total)}): detecta {cheapest.tp} fraudes con{" "}
              {formatNumber(cheapest.fp)} falsas alarmas.
            </p>
            {Math.abs(cheapest.threshold - threshold) >= 0.01 && (
              <button
                type="button"
                className="button button-outline"
                onClick={() => setThreshold(cheapest.threshold)}
              >
                Aplicar umbral {cheapest.threshold.toFixed(2)}
              </button>
            )}
          </div>
        </Card>
      </div>

      <div className="eval-curves">
        <Card className="chart-card">
          <ChartHeader
            title={`Curva ROC · AUC ${EVALUATION.aucRoc.toFixed(3)}`}
            subtitle="Cuanto más pegada a la esquina superior izquierda, mejor separa fraude de legítimas. La diagonal es el azar."
          />
          <CurveChart
            title="Curva ROC del modelo en el conjunto de prueba"
            points={EVALUATION.roc}
            xLabel="Tasa de falsas alarmas"
            yLabel="Fraude detectado (recall)"
            baseline="diagonal"
            marker={{
              x: counts.fp / (counts.fp + counts.tn),
              y: metrics.recall,
              label: `umbral ${threshold.toFixed(2)}`,
            }}
          />
        </Card>
        <Card className="chart-card">
          <ChartHeader
            title={`Precisión vs. recall · AP ${EVALUATION.averagePrecision.toFixed(3)}`}
            subtitle={`Más exigente con fraude escaso. Un modelo al azar quedaría en ${percent(dataset.fraudRate)} (línea punteada).`}
          />
          <CurveChart
            title="Curva de precisión y recall del modelo en el conjunto de prueba"
            points={EVALUATION.precisionRecall}
            xLabel="Recall"
            yLabel="Precisión"
            baseline={{ y: dataset.fraudRate }}
            marker={{
              x: metrics.recall,
              y: metrics.precision,
              label: `umbral ${threshold.toFixed(2)}`,
            }}
          />
        </Card>
      </div>

      <Card className="chart-card">
        <ChartHeader
          title="¿Qué aprendió el modelo?"
          subtitle={`Peso promedio de cada variable en las decisiones (SHAP global sobre ${formatNumber(EVALUATION.shapSampleSize)} transacciones de prueba).`}
        />
        <GlobalImportance />
        {topFeatures.length === 2 && (
          <p className="benchmark-note eval-note">
            Las dos variables más influyentes son{" "}
            <strong>{featureLabel(topFeatures[0].feature)}</strong> ({percent(topFeatures[0].share)}
            ) y <strong>{featureLabel(topFeatures[1].feature)}</strong> (
            {percent(topFeatures[1].share)}). Juntas suman el{" "}
            {percent(topFeatures[0].share + topFeatures[1].share)}; el resto del peso se reparte
            entre{" "}
            {EVALUATION.globalImportance
              .slice(2, 5)
              .map((item) => featureLabel(item.feature).toLowerCase())
              .join(", ")}{" "}
            y otras: el modelo combina varias señales, no depende de una sola.
          </p>
        )}
      </Card>
    </div>
  );
}
