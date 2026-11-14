import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Icon } from "@/components/ui/Icon";
import {
  COUNTRY_LABELS,
  DEVICE_LABELS,
  MERCHANT_CATEGORY_LABELS,
  REGION_LABELS,
  TRANSACTION_TYPE_LABELS,
  YES_NO_LABELS,
} from "@/lib/labels";

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
  type?: "text" | "number";
  min?: number;
  max?: number;
  step?: number;
  options?: readonly string[];
  optionLabels?: Readonly<Record<string, string>>;
};

const optionsOf = (labels: Readonly<Record<string, string>>) => Object.keys(labels);

// El modelo se entrenó con lunes = 0 … domingo = 6.
const DAY_LABELS: Record<string, string> = {
  "0": "Lunes",
  "1": "Martes",
  "2": "Miércoles",
  "3": "Jueves",
  "4": "Viernes",
  "5": "Sábado",
  "6": "Domingo",
};

const FIELDS: readonly FieldConfig[] = [
  {
    key: "transactionHour",
    label: "Hora de la transacción (0-23)",
    type: "number",
    min: 0,
    max: 23,
    step: 1,
  },
  {
    key: "transactionDayOfWeek",
    label: "Día de la semana",
    options: optionsOf(DAY_LABELS),
    optionLabels: DAY_LABELS,
  },
  {
    key: "accountAgeDays",
    label: "Antigüedad de la cuenta (días)",
    type: "number",
    min: 0,
    max: 20_000,
    step: 1,
  },
  {
    key: "previousChargebacks",
    label: "Contracargos previos",
    type: "number",
    min: 0,
    max: 50,
    step: 1,
  },
  {
    key: "merchantCategory",
    label: "Categoría del comercio",
    options: optionsOf(MERCHANT_CATEGORY_LABELS),
    optionLabels: MERCHANT_CATEGORY_LABELS,
  },
  {
    key: "transactionCountry",
    label: "País de la transacción",
    options: optionsOf(COUNTRY_LABELS),
    optionLabels: COUNTRY_LABELS,
  },
  {
    key: "deviceType",
    label: "Tipo de dispositivo",
    options: optionsOf(DEVICE_LABELS),
    optionLabels: DEVICE_LABELS,
  },
  {
    key: "transactionType",
    label: "Tipo de transacción",
    options: optionsOf(TRANSACTION_TYPE_LABELS),
    optionLabels: TRANSACTION_TYPE_LABELS,
  },
  {
    key: "geoLocationRegion",
    label: "Región geográfica",
    options: optionsOf(REGION_LABELS),
    optionLabels: REGION_LABELS,
  },
  {
    key: "isInternational",
    label: "Internacional",
    options: ["0", "1"],
    optionLabels: YES_NO_LABELS,
  },
  {
    key: "isHighRiskMerchantCategory",
    label: "Comercio de alto riesgo",
    options: ["0", "1"],
    optionLabels: YES_NO_LABELS,
  },
  { key: "isWeekend", label: "Fin de semana", options: ["0", "1"], optionLabels: YES_NO_LABELS },
  {
    key: "customerTotalTransactions30d",
    label: "Transacciones del cliente (30 días)",
    type: "number",
    min: 0,
    max: 500,
    step: 1,
  },
  {
    key: "customerRiskScore",
    label: "Score de riesgo del cliente (0-10)",
    type: "number",
    min: 0,
    max: 10,
    step: 0.01,
  },
  {
    key: "transactionAmount",
    label: "Monto de la transacción",
    type: "number",
    min: 0.01,
    max: 1_000_000,
    step: 0.01,
  },
  {
    key: "avgTransactionAmount30dCustomer",
    label: "Monto promedio (30 días)",
    type: "number",
    min: 0,
    max: 1_000_000,
    step: 0.01,
  },
  {
    key: "transactionVelocity1h",
    label: "Transacciones en la última hora",
    type: "number",
    min: 0,
    max: 100,
    step: 1,
  },
  {
    key: "transactionVelocity24h",
    label: "Transacciones en las últimas 24 h",
    type: "number",
    min: 0,
    max: 500,
    step: 1,
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
