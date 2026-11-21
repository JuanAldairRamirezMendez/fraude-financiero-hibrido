/**
 * Etiquetas en español para los valores técnicos que llegan del modelo y de la API.
 * Los valores internos (claves, categorías, estados) no cambian: solo cómo se muestran.
 * Cualquier valor desconocido se devuelve tal cual para no ocultar información.
 */

export const FEATURE_LABELS: Record<string, string> = {
  monto: "Monto",
  log_monto: "Monto (escala logarítmica)",
  hora: "Hora de la compra",
  dia_semana: "Día de la semana",
  nocturna: "Compra nocturna",
  edad: "Edad del cliente",
  genero_m: "Género del cliente",
  log_poblacion: "Población de la ciudad",
  distancia_km: "Distancia al comercio",
  monto_vs_categoria: "Monto frente a su categoría",
  categoria: "Categoría del comercio",
  compras_previas: "Compras previas de la tarjeta",
  seg_desde_anterior: "Tiempo desde la compra anterior",
  monto_vs_promedio_tarjeta: "Monto frente al promedio de la tarjeta",
  monto_z_tarjeta: "Desvío del gasto habitual",
  misma_categoria_previas: "Compras previas en la categoría",
  compras_1h: "Compras en la última hora",
  monto_1h: "Gasto en la última hora",
  compras_24h: "Compras en 24 h",
  monto_24h: "Gasto en 24 h",
  compras_7d: "Compras en 7 días",
  monto_7d: "Gasto en 7 días",
  monto_vs_24h: "Peso de la compra en el gasto de 24 h",
};

/** Variables del modelo anterior: los casos antiguos de la base de datos aún las traen. */
const LEGACY_FEATURE_LABELS: Record<string, string> = {
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
  entertainment: "Entretenimiento",
  food_dining: "Restaurantes",
  gas_transport: "Gasolina y transporte",
  grocery_net: "Supermercado en línea",
  grocery_pos: "Supermercado",
  health_fitness: "Salud y deporte",
  home: "Hogar",
  kids_pets: "Niños y mascotas",
  misc_net: "Varios en línea",
  misc_pos: "Varios",
  personal_care: "Cuidado personal",
  shopping_net: "Tienda en línea",
  shopping_pos: "Tienda",
  travel: "Viajes",
};

const LEGACY_CATEGORY_LABELS: Record<string, string> = {
  digital_subscriptions: "Suscripciones digitales",
  electronics: "Electrónica",
  fashion: "Moda",
  fuel: "Combustible",
  gambling: "Apuestas",
  grocery: "Supermercado",
  luxury_goods: "Artículos de lujo",
  online_services: "Servicios en línea",
  restaurant: "Restaurante",
};

/** Canal de la compra, derivado de la categoría (*_net en línea, *_pos presencial). */
export const TRANSACTION_TYPE_LABELS: Record<string, string> = {
  online: "En línea",
  pos: "Presencial",
  other: "Otros comercios",
  atm_withdrawal: "Retiro en cajero",
  card_present_moto: "Tarjeta presente / MOTO",
};

export const GENDER_LABELS: Record<string, string> = { F: "Mujer", M: "Hombre" };

export function categoryLabel(category: string): string {
  return MERCHANT_CATEGORY_LABELS[category] ?? LEGACY_CATEGORY_LABELS[category] ?? category;
}

/** Traduce una variable del modelo, incluidas las one-hot de categoría (p. ej. `cat_travel`). */
export function featureLabel(feature: string): string {
  const direct = FEATURE_LABELS[feature] ?? LEGACY_FEATURE_LABELS[feature];
  if (direct) return direct;
  if (feature.startsWith("cat_")) return `Categoría: ${categoryLabel(feature.slice(4))}`;
  if (feature.startsWith("merchant_category_")) {
    return `Categoría del comercio: ${categoryLabel(feature.slice(18))}`;
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
  [/^Test period Jun\W+Dec 2020$/, () => "Periodo de prueba jun–dic 2020"],
  [/^(\d[\d,.]*) labelled fraud cases$/, (n) => `${n} casos de fraude etiquetados`],
  [/^Test set\s*\W+\s*threshold ([\d.]+)$/, (t) => `Conjunto de prueba · umbral ${t}`],
  [/^(\d[\d,.]*) blocked at threshold ([\d.]+)$/, (n, t) => `${n} bloqueadas con umbral ${t}`],
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
