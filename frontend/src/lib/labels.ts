/**
 * Etiquetas en español para los valores técnicos que llegan del modelo y de la API.
 * Los valores internos (claves, categorías, estados) no cambian: solo cómo se muestran.
 * Cualquier valor desconocido se devuelve tal cual para no ocultar información.
 */

export const FEATURE_LABELS: Record<string, string> = {
  transaction_hour: "Hora de la transacción",
  transaction_day_of_week: "Día de la semana",
  account_age_days: "Antigüedad de la cuenta",
  previous_chargebacks: "Contracargos previos",
  is_international: "Internacional",
  is_high_risk_merchant_category: "Comercio de alto riesgo",
  is_weekend: "Fin de semana",
  customer_total_transactions_30d: "Transacciones del cliente (30 d)",
  customer_risk_score: "Score de riesgo del cliente",
  transaction_amount: "Monto de la transacción",
  avg_transaction_amount_30d_customer: "Monto promedio (30 d)",
  transaction_velocity_1h: "Velocidad (1 h)",
  transaction_velocity_24h: "Velocidad (24 h)",
  merchant_category: "Categoría del comercio",
  transaction_country: "País",
  device_type: "Dispositivo",
  transaction_type: "Tipo de transacción",
  geo_location_region: "Región",
};

export const MERCHANT_CATEGORY_LABELS: Record<string, string> = {
  digital_subscriptions: "Suscripciones digitales",
  electronics: "Electrónica",
  fashion: "Moda",
  fuel: "Combustible",
  gambling: "Apuestas",
  grocery: "Supermercado",
  luxury_goods: "Artículos de lujo",
  online_services: "Servicios en línea",
  restaurant: "Restaurante",
  travel: "Viajes",
};

export const COUNTRY_LABELS: Record<string, string> = {
  AU: "Australia (AU)",
  BR: "Brasil (BR)",
  CA: "Canadá (CA)",
  DE: "Alemania (DE)",
  FR: "Francia (FR)",
  IN: "India (IN)",
  MX: "México (MX)",
  NG: "Nigeria (NG)",
  UK: "Reino Unido (UK)",
  US: "Estados Unidos (US)",
};

export const DEVICE_LABELS: Record<string, string> = {
  desktop: "Computadora",
  mobile: "Móvil",
  tablet: "Tablet",
  wearable: "Wearable",
};

export const TRANSACTION_TYPE_LABELS: Record<string, string> = {
  atm_withdrawal: "Retiro en cajero",
  card_present_moto: "Tarjeta presente / MOTO",
  online: "En línea",
  pos: "Punto de venta (POS)",
};

export const REGION_LABELS: Record<string, string> = {
  Africa: "África",
  Asia: "Asia",
  Europe: "Europa",
  "North America": "Norteamérica",
  "South America": "Sudamérica",
};

export const YES_NO_LABELS: Record<string, string> = { "0": "No", "1": "Sí" };

const CATEGORY_VALUE_LABELS: Record<string, Record<string, string>> = {
  merchant_category: MERCHANT_CATEGORY_LABELS,
  transaction_country: COUNTRY_LABELS,
  device_type: DEVICE_LABELS,
  transaction_type: TRANSACTION_TYPE_LABELS,
  geo_location_region: REGION_LABELS,
};

/** Traduce una variable del modelo, incluidas las one-hot (p. ej. `merchant_category_gambling`). */
export function featureLabel(feature: string): string {
  const direct = FEATURE_LABELS[feature];
  if (direct) return direct;

  for (const [prefix, values] of Object.entries(CATEGORY_VALUE_LABELS)) {
    if (feature.startsWith(`${prefix}_`)) {
      const value = feature.slice(prefix.length + 1);
      return `${FEATURE_LABELS[prefix]}: ${values[value] ?? value}`;
    }
  }
  return feature;
}

export function transactionTypeLabel(type: string): string {
  return TRANSACTION_TYPE_LABELS[type] ?? type;
}

export const TRANSACTION_STATUS_LABELS: Record<string, string> = {
  Flagged: "Bloqueada",
  Review: "En revisión",
  Approved: "Aprobada",
};

export const ALERT_STATUS_LABELS: Record<string, string> = {
  UNACKNOWLEDGED: "Sin revisar",
  ACKNOWLEDGED: "Revisada",
  RESOLVED: "Resuelta",
};

export const ALERT_TYPE_LABELS: Record<string, string> = {
  "Feature drift": "Deriva de variables",
  "Data quality": "Calidad de datos",
  "Prediction drift": "Deriva de predicciones",
  Performance: "Rendimiento",
};

const KPI_LABELS: Record<string, string> = {
  transactions: "Transacciones totales",
  "fraud-rate": "Tasa de fraude",
  "f1-score": "F1-Score del modelo",
  "pending-alerts": "Casos por revisar",
};

export function kpiLabel(id: string, fallback: string): string {
  return KPI_LABELS[id] ?? fallback;
}

type Rule = [RegExp, (...groups: string[]) => string];

function translateWith(rules: readonly Rule[], text: string): string {
  for (const [pattern, render] of rules) {
    const match = pattern.exec(text);
    if (match) return render(...match.slice(1));
  }
  return text;
}

const TREND_RULES: readonly Rule[] = [
  [/^Full dataset snapshot$/, () => "Instantánea completa del dataset"],
  [/^(\d[\d,.]*) labelled fraud cases$/, (n) => `${n} casos de fraude etiquetados`],
  [/^Tier 2 XGBoost holdout$/, () => "XGBoost Tier 2 · conjunto de prueba"],
  [
    /^Calibrated models*W+s*threshold ([d.]+)s*W+s*test set$/,
    (t) => `Modelo calibrado · umbral ${t} · prueba`,
  ],
  [/^(d[d,.]*) blocked at threshold ([d.]+)$/, (n, t) => `${n} bloqueadas con umbral ${t}`],
  [
    /^(\d[\d,.]*) flagged\s*\W+\s*(\d[\d,.]*) review$/,
    (a, b) => `${a} marcadas · ${b} en revisión`,
  ],
  [/^Stable$/, () => "Estable"],
  [/^(\d+) urgent$/, (n) => `${n} urgentes`],
];

export function kpiTrend(text: string): string {
  return translateWith(TREND_RULES, text);
}

const WINDOW_RULES: readonly Rule[] = [
  [/^Dataset snapshot\s*\W+\s*([\d,.]+) rows$/, (n) => `Instantánea del dataset · ${n} filas`],
  [/^Last 24 hours$/, () => "Últimas 24 horas"],
];

export function windowLabel(text: string): string {
  return translateWith(WINDOW_RULES, text);
}

const ALERT_DETAIL_RULES: readonly Rule[] = [
  [
    /^Transaction amount PSI ([\d.]+) remains within the ([\d.]+) warning threshold\.$/,
    (psi, limit) =>
      `El PSI del monto de transacción (${psi}) se mantiene bajo el umbral de alerta de ${limit}.`,
  ],
  [
    /^24h transaction velocity PSI ([\d.]+) remains within the configured threshold\.$/,
    (psi) =>
      `El PSI de la velocidad de transacciones en 24 h (${psi}) se mantiene bajo el umbral configurado.`,
  ],
  [
    /^Artifact (\S+) loaded with (\d+) features\.$/,
    (artifact, count) => `Artefacto ${artifact} cargado con ${count} variables.`,
  ],
];

export function alertDetail(text: string): string {
  return translateWith(ALERT_DETAIL_RULES, text);
}
