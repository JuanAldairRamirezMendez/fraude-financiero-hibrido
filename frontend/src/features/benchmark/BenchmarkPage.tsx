import { useState } from "react";
import { Link } from "react-router-dom";

import { Badge, type BadgeVariant } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ChartHeader } from "@/components/ui/ChartHeader";
import { DataTable, type Column } from "@/components/ui/DataTable";
import { Icon } from "@/components/ui/Icon";

import {
  CRISP_DM_STEPS,
  FAMILIES,
  FAMILY_LABELS,
  MODEL_RESULTS,
  PRODUCTION_MODEL,
  type ModelFamily,
  type ModelResult,
} from "./data";

type Metric = "f1" | "precision" | "recall";

const METRICS: ReadonlyArray<{ key: Metric; label: string; hint: string }> = [
  {
    key: "f1",
    label: "F1-Score",
    hint: "Equilibrio entre precisión y recall: la métrica principal.",
  },
  {
    key: "precision",
    label: "Precisión",
    hint: "De las alertas emitidas, cuántas eran fraude real.",
  },
  {
    key: "recall",
    label: "Recall",
    hint: "Del fraude real, cuánto logró detectar el modelo.",
  },
];

const FAMILY_BADGE: Record<ModelFamily, BadgeVariant> = {
  neural: "info",
  classic: "success",
  ensemble: "warning",
};

const percent = (value: number) => `${(value * 100).toFixed(1)}%`;

type MetricKey = "precision" | "recall" | "f1" | "aucRoc";

function bestOf(metric: MetricKey) {
  return Math.max(...MODEL_RESULTS.map((model) => model[metric]));
}

function MetricCell({ value, metric }: { value: number; metric: MetricKey }) {
  const isBest = value === bestOf(metric);
  return <span className={isBest ? "metric-best" : undefined}>{value.toFixed(4)}</span>;
}

const COLUMNS: ReadonlyArray<Column<ModelResult>> = [
  {
    key: "name",
    header: "Modelo",
    render: (model) => (
      <div className="model-name-cell">
        <strong>
          {model.name}
          {model.selected && (
            <span className="model-selected-tag">
              <Icon name="check" size={11} />
              Producción
            </span>
          )}
        </strong>
        <span>{model.detail}</span>
      </div>
    ),
  },
  {
    key: "family",
    header: "Familia",
    render: (model) => (
      <Badge variant={FAMILY_BADGE[model.family]}>{FAMILY_LABELS[model.family]}</Badge>
    ),
  },
  {
    key: "precision",
    header: "Precisión",
    render: (m) => <MetricCell value={m.precision} metric="precision" />,
  },
  {
    key: "recall",
    header: "Recall",
    render: (m) => <MetricCell value={m.recall} metric="recall" />,
  },
  { key: "f1", header: "F1-Score", render: (m) => <MetricCell value={m.f1} metric="f1" /> },
  { key: "auc", header: "AUC-ROC", render: (m) => <MetricCell value={m.aucRoc} metric="aucRoc" /> },
];

export default function BenchmarkPage() {
  const [metric, setMetric] = useState<Metric>("f1");
  const sorted = [...MODEL_RESULTS].sort((a, b) => b[metric] - a[metric]);
  const activeMetric = METRICS.find((item) => item.key === metric) ?? METRICS[0];
  const winner = MODEL_RESULTS.find((model) => model.selected) ?? MODEL_RESULTS[0];
  const runnerUp = [...MODEL_RESULTS]
    .filter((model) => !model.selected)
    .sort((a, b) => b.f1 - a.f1)[0];

  return (
    <div className="benchmark-page">
      <div className="analyzer-intro">
        <div>
          <h2 className="section-title">Sistema híbrido de detección de fraude</h2>
          <p className="section-subtitle">
            Se entrenaron y compararon {MODEL_RESULTS.length} modelos de tres familias sobre el
            mismo conjunto de prueba. El mejor se despliega en producción.
          </p>
        </div>
        <Badge variant="success">
          <span className="badge-dot" aria-hidden="true" />
          Ganador: {winner.name} · F1 {winner.f1.toFixed(3)}
        </Badge>
      </div>

      <div className="family-grid">
        {FAMILIES.map((family) => (
          <Card key={family.family} className={`family-card family-${family.family}`}>
            <span className="family-count">
              {MODEL_RESULTS.filter((model) => model.family === family.family).length} evaluado(s)
            </span>
            <h3>{family.title}</h3>
            <p>{family.description}</p>
            <ul className="tag-list" aria-label={`Técnicas de ${family.title}`}>
              {family.techniques.map((technique) => (
                <li key={technique}>{technique}</li>
              ))}
            </ul>
          </Card>
        ))}
      </div>

      <div className="benchmark-grid">
        <Card className="chart-card benchmark-chart">
          <ChartHeader
            title="Comparativa de rendimiento"
            subtitle={activeMetric.hint}
            actions={
              <div className="metric-toggle" role="group" aria-label="Métrica a comparar">
                {METRICS.map((item) => (
                  <button
                    key={item.key}
                    type="button"
                    aria-pressed={metric === item.key}
                    onClick={() => setMetric(item.key)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            }
          />
          <ol className="benchmark-bars" aria-label={`Modelos ordenados por ${activeMetric.label}`}>
            {sorted.map((model) => (
              <li key={model.id} className={model.selected ? "is-selected" : undefined}>
                <span className="benchmark-label">{model.name}</span>
                <span className="bar-track benchmark-track">
                  <span
                    className={`benchmark-bar family-bar-${model.family}`}
                    style={{ width: `${model[metric] * 100}%` }}
                  />
                </span>
                <span className="benchmark-value">{percent(model[metric])}</span>
              </li>
            ))}
          </ol>
          <div className="chart-legend benchmark-legend">
            {(Object.keys(FAMILY_LABELS) as ModelFamily[]).map((family) => (
              <span key={family}>
                <i className={`family-bar-${family}`} />
                {FAMILY_LABELS[family]}
              </span>
            ))}
          </div>
        </Card>

        <Card className="winner-card">
          <span className="section-kicker">Decisión de despliegue</span>
          <h3>¿Por qué {winner.name} en producción?</h3>
          <ul className="reason-list">
            <li>
              <Icon name="target" size={16} />
              <span>
                <strong>Mejor F1 ({winner.f1.toFixed(3)})</strong> y mejor AUC-ROC (
                {winner.aucRoc.toFixed(4)}) de los {MODEL_RESULTS.length} modelos
                {runnerUp ? `, por delante de ${runnerUp.name} (${runnerUp.f1.toFixed(3)})` : ""}.
              </span>
            </li>
            <li>
              <Icon name="shield" size={16} />
              <span>
                <strong>Detecta el {percent(winner.recall)} del fraude</strong> manteniendo una
                precisión superior a la de la red neuronal y Random Forest.
              </span>
            </li>
            <li>
              <Icon name="activity" size={16} />
              <span>
                <strong>Explicable con SHAP</strong>: al ser un modelo de árboles, cada decisión se
                descompone en el aporte de cada variable.
              </span>
            </li>
            <li>
              <Icon name="clock" size={16} />
              <span>
                <strong>Optimizado y calibrado</strong>: con Optuna (Tier 2) su F1 sube de{" "}
                {winner.f1.toFixed(3)} a <strong>{PRODUCTION_MODEL.tier2F1.toFixed(3)}</strong>, y la
                calibración isotónica convierte el score en una probabilidad fiable.
              </span>
            </li>
          </ul>
          <Link className="button button-primary" to="/analyzer">
            Probar el modelo en vivo
            <Icon name="arrow" size={16} />
          </Link>
        </Card>
      </div>

      <Card className="table-card">
        <ChartHeader
          title="Resultados en el conjunto de prueba"
          subtitle="Los valores resaltados son el mejor resultado de cada métrica."
        />
        <DataTable
          caption="Métricas de los modelos evaluados"
          columns={COLUMNS}
          rows={MODEL_RESULTS}
          rowKey={(model) => model.id}
        />
        <p className="benchmark-note">
          La SVM alcanza el mayor recall ({percent(bestOf("recall"))}) pero con muy baja precisión:
          generaría demasiadas falsas alarmas. Por eso la selección se basa en el F1-Score.
        </p>
      </Card>

      <Card className="crisp-card">
        <ChartHeader
          title="Metodología CRISP-DM"
          subtitle="Ciclo completo implementado en pipeline_completo.py"
        />
        <ol className="crisp-steps">
          {CRISP_DM_STEPS.map((step, index) => (
            <li key={step.title}>
              <span className="crisp-index">{index + 1}</span>
              <strong>{step.title}</strong>
              <span>{step.detail}</span>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}
