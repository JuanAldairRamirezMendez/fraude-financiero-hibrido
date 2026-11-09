import type { TransactionInput } from "./types";

export interface TransactionFormValues {
  transactionHour: string;
  transactionDayOfWeek: string;
  accountAgeDays: string;
  previousChargebacks: string;
  merchantCategory: string;
  transactionCountry: string;
  deviceType: string;
  transactionType: string;
  geoLocationRegion: string;
  isInternational: string;
  isHighRiskMerchantCategory: string;
  isWeekend: string;
  customerTotalTransactions30d: string;
  customerRiskScore: string;
  transactionAmount: string;
  avgTransactionAmount30dCustomer: string;
  transactionVelocity1h: string;
  transactionVelocity24h: string;
  decisionThreshold: string;
}

export type FieldErrors = Partial<Record<keyof TransactionFormValues, string>>;

export const INITIAL_FORM_VALUES: TransactionFormValues = {
  transactionHour: "11",
  transactionDayOfWeek: "3",
  accountAgeDays: "703",
  previousChargebacks: "0",
  merchantCategory: "travel",
  transactionCountry: "US",
  deviceType: "mobile",
  transactionType: "online",
  geoLocationRegion: "North America",
  isInternational: "0",
  isHighRiskMerchantCategory: "0",
  isWeekend: "0",
  customerTotalTransactions30d: "6",
  customerRiskScore: "0.15",
  transactionAmount: "484.15",
  avgTransactionAmount30dCustomer: "651.035",
  transactionVelocity1h: "0",
  transactionVelocity24h: "3",
  decisionThreshold: "0.5",
};

interface ValidationResult {
  errors: FieldErrors;
  input: TransactionInput | null;
}

const NUMERIC_FIELDS: Array<[keyof TransactionFormValues, number, number, boolean]> = [
  ["transactionHour", 0, 23, true],
  ["transactionDayOfWeek", 0, 6, true],
  ["accountAgeDays", 0, 3650, true],
  ["previousChargebacks", 0, 50, true],
  ["isInternational", 0, 1, true],
  ["isHighRiskMerchantCategory", 0, 1, true],
  ["isWeekend", 0, 1, true],
  ["customerTotalTransactions30d", 0, 500, true],
  ["customerRiskScore", 0, 1, false],
  ["transactionAmount", 0.01, 1_000_000, false],
  ["avgTransactionAmount30dCustomer", 0, 1_000_000, false],
  ["transactionVelocity1h", 0, 100, true],
  ["transactionVelocity24h", 0, 500, true],
  ["decisionThreshold", 0, 1, false],
];

const CATEGORY_FIELDS: Array<keyof TransactionFormValues> = [
  "merchantCategory",
  "transactionCountry",
  "deviceType",
  "transactionType",
  "geoLocationRegion",
];

export function validateTransactionForm(values: TransactionFormValues): ValidationResult {
  const errors: FieldErrors = {};
  const parsed = {} as Record<string, number>;

  for (const [field, minimum, maximum, integer] of NUMERIC_FIELDS) {
    const value = Number(values[field].replace(",", "."));
    parsed[field] = value;
    if (
      !Number.isFinite(value) ||
      value < minimum ||
      value > maximum ||
      (integer && !Number.isInteger(value))
    ) {
      errors[field] = `Ingresa un valor entre ${minimum} y ${maximum}${integer ? " sin decimales" : ""}.`;
    }
  }

  for (const field of CATEGORY_FIELDS) {
    if (!values[field].trim()) errors[field] = "Selecciona un valor válido.";
  }

  if (Object.keys(errors).length > 0) return { errors, input: null };

  return {
    errors,
    input: {
      transactionHour: parsed.transactionHour,
      transactionDayOfWeek: parsed.transactionDayOfWeek,
      accountAgeDays: parsed.accountAgeDays,
      previousChargebacks: parsed.previousChargebacks,
      merchantCategory: values.merchantCategory,
      transactionCountry: values.transactionCountry,
      deviceType: values.deviceType,
      transactionType: values.transactionType,
      geoLocationRegion: values.geoLocationRegion,
      isInternational: parsed.isInternational,
      isHighRiskMerchantCategory: parsed.isHighRiskMerchantCategory,
      isWeekend: parsed.isWeekend,
      customerTotalTransactions30d: parsed.customerTotalTransactions30d,
      customerRiskScore: parsed.customerRiskScore,
      transactionAmount: parsed.transactionAmount,
      avgTransactionAmount30dCustomer: parsed.avgTransactionAmount30dCustomer,
      transactionVelocity1h: parsed.transactionVelocity1h,
      transactionVelocity24h: parsed.transactionVelocity24h,
      decisionThreshold: parsed.decisionThreshold,
    },
  };
}
