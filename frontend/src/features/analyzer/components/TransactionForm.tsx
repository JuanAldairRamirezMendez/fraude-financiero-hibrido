import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Icon } from "@/components/ui/Icon";
import { MERCHANT_CATEGORY_LABELS } from "@/lib/labels";

import { CARD_LABELS, CARDS } from "../cards";
import { pickRealSample, sampleToFormValues, type RealSample } from "../realSamples";
import { DEMO_SCENARIOS, type DemoScenario } from "../scenarios";
import { useAnalyzerSession } from "../session";
import type { TransactionInput } from "../types";
import {
  validateTransactionForm,
  type FieldErrors,
  type TransactionFormValues,
} from "../validation";

interface TransactionFormProps {
  isPending: boolean;
  /** `realSample` llega solo cuando se envía una transacción real sin modificar. */
  onSubmit: (input: TransactionInput, realSample: RealSample | null) => void;
}

type FieldConfig = {
  key: keyof TransactionFormValues;
  label: string;
  type?: "text" | "number" | "datetime-local";
  min?: number;
  max?: number;
  step?: number;
  options?: readonly string[];
  optionLabels?: Readonly<Record<string, string>>;
};

const FIELDS: readonly FieldConfig[] = [
  {
    key: "cardId",
    label: "Tarjeta del cliente",
    options: CARDS.map((card) => card.id),
    optionLabels: CARD_LABELS,
  },
  { key: "transactionTime", label: "Fecha y hora", type: "datetime-local", step: 1 },
  {
    key: "amount",
    label: "Monto (US$)",
    type: "number",
    min: 0.01,
    max: 50_000,
    step: 0.01,
  },
  {
    key: "category",
    label: "Categoría del comercio",
    options: Object.keys(MERCHANT_CATEGORY_LABELS),
    optionLabels: MERCHANT_CATEGORY_LABELS,
  },
  {
    key: "merchantDistanceKm",
    label: "Distancia al comercio (km)",
    type: "number",
    min: 0,
    max: 1_000,
    step: 0.1,
  },
  {
    key: "decisionThreshold",
    label: "Umbral de bloqueo (0-1)",
    type: "number",
    min: 0,
    max: 1,
    step: 0.001,
  },
];

const REAL_SAMPLE_ID = "real-sample";

export function TransactionForm({ isPending, onSubmit }: TransactionFormProps) {
  // El formulario se conserva al salir del Analizador y volver (ver session.ts).
  const [values, setValues] = useAnalyzerSession("values");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [activeScenario, setActiveScenario] = useAnalyzerSession("activeScenario");
  const [realSample, setRealSample] = useAnalyzerSession("realSample");
  const scenarioHint = realSample
    ? `Transacción real ${realSample.id} del conjunto de prueba. Su etiqueta verdadera se revela después del análisis.`
    : (DEMO_SCENARIOS.find((scenario) => scenario.id === activeScenario)?.description ??
      "Carga un caso de ejemplo con un clic o edita los campos manualmente.");

  function update(field: keyof TransactionFormValues, value: string) {
    setValues((previous) => ({ ...previous, [field]: value }));
    setErrors({});
    setActiveScenario(null);
    setRealSample(null);
  }

  function applyScenario(scenario: DemoScenario) {
    setValues(scenario.values);
    setErrors({});
    setActiveScenario(scenario.id);
    setRealSample(null);
  }

  function applyRealSample() {
    const sample = pickRealSample(realSample?.id);
    setValues((previous) => sampleToFormValues(sample, previous));
    setErrors({});
    setActiveScenario(REAL_SAMPLE_ID);
    setRealSample(sample);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = validateTransactionForm(values);
    setErrors(result.errors);
    if (result.input) onSubmit(result.input, realSample);
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
      <fieldset className="scenario-picker">
        <legend>Escenarios de demostración</legend>
        <div className="scenario-list">
          {DEMO_SCENARIOS.map((scenario) => (
            <button
              key={scenario.id}
              type="button"
              className={`scenario-chip scenario-${scenario.expectedRisk}`}
              aria-pressed={activeScenario === scenario.id}
              title={scenario.description}
              onClick={() => applyScenario(scenario)}
            >
              <span className="scenario-dot" aria-hidden="true" />
              {scenario.label}
            </button>
          ))}
          <button
            type="button"
            className="scenario-chip scenario-real"
            aria-pressed={activeScenario === REAL_SAMPLE_ID}
            title="Carga una transacción real del conjunto de prueba sin revelar si era fraude"
            onClick={applyRealSample}
          >
            <span className="scenario-dot" aria-hidden="true" />
            {realSample ? "Otra transacción real" : "Transacción real al azar"}
          </button>
        </div>
        <p className="scenario-hint" aria-live="polite">
          {scenarioHint}
        </p>
      </fieldset>
      <div className="form-grid">
        {FIELDS.map((field) => (
          <Field
            key={field.key}
            id={`transaction-${field.key}`}
            label={field.label}
            value={values[field.key]}
            onChange={(value) => update(field.key, value)}
            type={field.type}
            options={field.options}
            optionLabels={field.optionLabels}
            min={field.min}
            max={field.max}
            step={field.step}
            error={errors[field.key]}
          />
        ))}
      </div>
      <Button type="submit" className="analyze-button" disabled={isPending} aria-busy={isPending}>
        {isPending ? (
          <>
            <span className="spinner spinner-inline" aria-hidden="true" />
            Analizando…
          </>
        ) : (
          <>
            <Icon name="activity" size={18} />
            Analizar transacción
            <Icon name="arrow" size={17} />
          </>
        )}
      </Button>
    </form>
  );
}
