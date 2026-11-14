import { INITIAL_FORM_VALUES, type TransactionFormValues } from "./validation";

export type ScenarioRisk = "low" | "medium" | "high";

export interface DemoScenario {
  id: string;
  label: string;
  description: string;
  expectedRisk: ScenarioRisk;
  values: TransactionFormValues;
}

/**
 * Escenarios precargados para demostrar el modelo en vivo.
 *
 * Los valores se calibraron contra el modelo de producción
 * (xgboost-tier2-isotonic-f88d84b82069) y heredan el umbral por defecto (bloqueo desde 0.247):
 * dan un score de 0 (aprobada), 71 y 99 (ambas bloqueadas y enviadas al analista). Si se
 * reentrena el modelo, conviene volver a verificarlos.
 */
export const DEMO_SCENARIOS: readonly DemoScenario[] = [
  {
    id: "normal",
    label: "Compra habitual",
    description: "Supermercado, cuenta de 4 años, importe en línea con su historial.",
    expectedRisk: "low",
    values: {
      ...INITIAL_FORM_VALUES,
      transactionHour: "14",
      transactionDayOfWeek: "2",
      accountAgeDays: "1460",
      previousChargebacks: "0",
      merchantCategory: "grocery",
      transactionCountry: "US",
      deviceType: "desktop",
      transactionType: "pos",
      geoLocationRegion: "North America",
      isInternational: "0",
      isHighRiskMerchantCategory: "0",
      isWeekend: "0",
      customerTotalTransactions30d: "22",
      customerRiskScore: "0.05",
      transactionAmount: "62.40",
      avgTransactionAmount30dCustomer: "71.80",
      transactionVelocity1h: "0",
      transactionVelocity24h: "2",
    },
  },
  {
    id: "suspicious",
    label: "Sospechosa",
    description: "Artículos de lujo, internacional, cuenta de 40 días e importe 12× su media.",
    expectedRisk: "medium",
    values: {
      ...INITIAL_FORM_VALUES,
      transactionHour: "22",
      transactionDayOfWeek: "3",
      accountAgeDays: "40",
      previousChargebacks: "2",
      merchantCategory: "luxury_goods",
      transactionCountry: "BR",
      deviceType: "mobile",
      transactionType: "online",
      geoLocationRegion: "South America",
      isInternational: "1",
      isHighRiskMerchantCategory: "0",
      isWeekend: "0",
      customerTotalTransactions30d: "6",
      customerRiskScore: "0.70",
      transactionAmount: "4560.00",
      avgTransactionAmount30dCustomer: "380.00",
      transactionVelocity1h: "5",
      transactionVelocity24h: "19",
    },
  },
  {
    id: "fraud",
    label: "Fraude probable",
    description: "Apuestas a las 3 a. m., cuenta de 9 días, 4 contracargos y 9 operaciones en 1 h.",
    expectedRisk: "high",
    values: {
      ...INITIAL_FORM_VALUES,
      transactionHour: "3",
      transactionDayOfWeek: "6",
      accountAgeDays: "9",
      previousChargebacks: "4",
      merchantCategory: "gambling",
      transactionCountry: "NG",
      deviceType: "mobile",
      transactionType: "online",
      geoLocationRegion: "Africa",
      isInternational: "1",
      isHighRiskMerchantCategory: "1",
      isWeekend: "1",
      customerTotalTransactions30d: "41",
      customerRiskScore: "0.92",
      transactionAmount: "7800.00",
      avgTransactionAmount30dCustomer: "210.00",
      transactionVelocity1h: "9",
      transactionVelocity24h: "35",
    },
  },
];
