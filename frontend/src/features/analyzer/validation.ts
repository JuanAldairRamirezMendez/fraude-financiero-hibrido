import { EVALUATION } from "@/features/evaluation/data";

import { CARD_IDS } from "./cards";
import scenarios from "./scenarios.json";
import type { TransactionInput } from "./types";

export interface TransactionFormValues {
  cardId: string;
  transactionTime: string;
  amount: string;
  category: string;
  merchantDistanceKm: string;
  decisionThreshold: string;
}

export const CATEGORIES = [
  "entertainment",
  "food_dining",
  "gas_transport",
  "grocery_net",
  "grocery_pos",
  "health_fitness",
  "home",
  "kids_pets",
  "misc_net",
  "misc_pos",
  "personal_care",
  "shopping_net",
  "shopping_pos",
  "travel",
] as const;

type Category = (typeof CATEGORIES)[number];

/** Umbral calibrado del modelo: desde aquí la transacción se bloquea y pasa al analista. */
export const BLOCK_THRESHOLD = EVALUATION.calibratedThreshold.toFixed(3);

/** El historial de las tarjetas cubre el periodo del dataset. */
export const FIRST_DAY = "2019-01-01T00:00:00";
export const LAST_DAY = "2020-12-31T23:59:59";

export type FieldErrors = Partial<Record<keyof TransactionFormValues, string>>;

const normal = scenarios[0].values;

/** El formulario arranca con la compra habitual de los escenarios de demostración. */
export const INITIAL_FORM_VALUES: TransactionFormValues = {
  cardId: normal.cardId,
  transactionTime: normal.transactionTime,
  amount: String(normal.amount),
  category: normal.category,
  merchantDistanceKm: String(normal.merchantDistanceKm),
  decisionThreshold: BLOCK_THRESHOLD,
};

interface ValidationResult {
  errors: FieldErrors;
  input: TransactionInput | null;
}

const NUMERIC_FIELDS: Array<[keyof TransactionFormValues, number, number]> = [
  ["amount", 0.01, 50_000],
  ["merchantDistanceKm", 0, 1_000],
  ["decisionThreshold", 0, 1],
];

/** Acepta "AAAA-MM-DDTHH:MM" (sin segundos) además de "AAAA-MM-DDTHH:MM:SS". */
export function normalizeDateTime(value: string): string {
  const trimmed = value.trim();
  return /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(trimmed) ? `${trimmed}:00` : trimmed;
}

export function validateTransactionForm(values: TransactionFormValues): ValidationResult {
  const errors: FieldErrors = {};
  const parsed = {} as Record<string, number>;

  for (const [field, minimum, maximum] of NUMERIC_FIELDS) {
    const value = Number(values[field].replace(",", "."));
    parsed[field] = value;
    if (!Number.isFinite(value) || value < minimum || value > maximum) {
      errors[field] = `Ingresa un valor entre ${minimum} y ${maximum}.`;
    }
  }

  if (!CARD_IDS.has(values.cardId)) errors.cardId = "Selecciona una tarjeta del catálogo.";
  if (!(CATEGORIES as readonly string[]).includes(values.category)) {
    errors.category = "Selecciona una categoría válida.";
  }

  const when = normalizeDateTime(values.transactionTime);
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$/.test(when) || Number.isNaN(Date.parse(when))) {
    errors.transactionTime = "Ingresa una fecha y hora válidas.";
  } else if (when < FIRST_DAY || when > LAST_DAY) {
    errors.transactionTime =
      "Usa una fecha entre enero de 2019 y diciembre de 2020 (periodo del dataset).";
  }

  if (Object.keys(errors).length > 0) return { errors, input: null };

  return {
    errors,
    input: {
      cardId: values.cardId,
      transactionTime: when,
      amount: parsed.amount,
      category: values.category as Category,
      merchantDistanceKm: parsed.merchantDistanceKm,
      // Un solo umbral: aprobar o bloquear (sin franja intermedia de revisión).
      decisionThreshold: parsed.decisionThreshold,
      blockThreshold: parsed.decisionThreshold,
    },
  };
}
