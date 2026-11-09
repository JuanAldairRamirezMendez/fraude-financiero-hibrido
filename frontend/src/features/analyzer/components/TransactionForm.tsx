import { useState, type FormEvent } from "react";

import { Button } from "@/components/ui/Button";
import { Field } from "@/components/ui/Field";
import { Icon } from "@/components/ui/Icon";

import type { TransactionInput } from "../types";
import {
  INITIAL_FORM_VALUES,
  validateTransactionForm,
  type FieldErrors,
  type TransactionFormValues,
} from "../validation";

interface TransactionFormProps {
  isPending: boolean;
  onSubmit: (input: TransactionInput) => void;
}

type FieldConfig = {
  key: keyof TransactionFormValues;
  label: string;
  type?: "text" | "number";
  min?: number;
  max?: number;
  step?: number;
  options?: readonly string[];
};

const FIELDS: readonly FieldConfig[] = [
  { key: "transactionHour", label: "Transaction hour", type: "number", min: 0, max: 23, step: 1 },
  { key: "transactionDayOfWeek", label: "Day of week", type: "number", min: 0, max: 6, step: 1 },
  { key: "accountAgeDays", label: "Account age (days)", type: "number", min: 0, max: 3650, step: 1 },
  { key: "previousChargebacks", label: "Previous chargebacks", type: "number", min: 0, max: 50, step: 1 },
  { key: "merchantCategory", label: "Merchant category", options: ["digital_subscriptions", "electronics", "fashion", "fuel", "gambling", "grocery", "luxury_goods", "online_services", "restaurant", "travel"] },
  { key: "transactionCountry", label: "Transaction country", options: ["AU", "BR", "CA", "DE", "FR", "IN", "MX", "NG", "UK", "US"] },
  { key: "deviceType", label: "Device type", options: ["desktop", "mobile", "tablet", "wearable"] },
  { key: "transactionType", label: "Transaction type", options: ["atm_withdrawal", "card_present_moto", "online", "pos"] },
  { key: "geoLocationRegion", label: "Geographic region", options: ["Africa", "Asia", "Europe", "North America", "South America"] },
  { key: "isInternational", label: "International", options: ["0", "1"] },
  { key: "isHighRiskMerchantCategory", label: "High-risk merchant category", options: ["0", "1"] },
  { key: "isWeekend", label: "Weekend", options: ["0", "1"] },
  { key: "customerTotalTransactions30d", label: "Customer transactions (30d)", type: "number", min: 0, max: 500, step: 1 },
  { key: "customerRiskScore", label: "Customer risk score", type: "number", min: 0, max: 1, step: 0.01 },
  { key: "transactionAmount", label: "Transaction amount", type: "number", min: 0.01, max: 1_000_000, step: 0.01 },
  { key: "avgTransactionAmount30dCustomer", label: "Average amount (30d)", type: "number", min: 0, max: 1_000_000, step: 0.01 },
  { key: "transactionVelocity1h", label: "Transaction velocity (1h)", type: "number", min: 0, max: 100, step: 1 },
  { key: "transactionVelocity24h", label: "Transaction velocity (24h)", type: "number", min: 0, max: 500, step: 1 },
  { key: "decisionThreshold", label: "Decision threshold", type: "number", min: 0, max: 1, step: 0.01 },
];

export function TransactionForm({ isPending, onSubmit }: TransactionFormProps) {
  const [values, setValues] = useState<TransactionFormValues>(INITIAL_FORM_VALUES);
  const [errors, setErrors] = useState<FieldErrors>({});

  function update(field: keyof TransactionFormValues, value: string) {
    setValues((previous) => ({ ...previous, [field]: value }));
    setErrors({});
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = validateTransactionForm(values);
    setErrors(result.errors);
    if (result.input) onSubmit(result.input);
  }

  return (
    <form onSubmit={handleSubmit} noValidate>
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
            min={field.min}
            max={field.max}
            step={field.step}
            error={errors[field.key]}
          />
        ))}
      </div>
      <Button type="submit" className="analyze-button" disabled={isPending} aria-busy={isPending}>
        {isPending ? (
          <><span className="spinner spinner-inline" aria-hidden="true" />Analyzing…</>
        ) : (
          <><Icon name="activity" size={18} />Analyze Transaction<Icon name="arrow" size={17} /></>
        )}
      </Button>
    </form>
  );
}
