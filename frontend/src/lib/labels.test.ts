import { describe, expect, it } from "vitest";

import { alertDetail, featureLabel, kpiLabel, kpiTrend, windowLabel } from "./labels";

describe("labels", () => {
  it("traduce variables simples y one-hot del modelo", () => {
    expect(featureLabel("monto_24h")).toBe("Gasto en 24 h");
    expect(featureLabel("categoria")).toBe("Categoría del comercio");
    expect(featureLabel("cat_shopping_net")).toBe("Categoría: Tienda en línea");
  });

  it("sigue traduciendo las variables de casos antiguos", () => {
    expect(featureLabel("customer_risk_score")).toBe("Score de riesgo del cliente");
    expect(featureLabel("merchant_category_gambling")).toBe("Categoría del comercio: Apuestas");
  });

  it("devuelve el valor original si no lo conoce", () => {
    expect(featureLabel("nueva_variable")).toBe("nueva_variable");
    expect(kpiTrend("texto desconocido")).toBe("texto desconocido");
    expect(kpiLabel("otro", "Fallback")).toBe("Fallback");
  });

  it("traduce los textos del snapshot del backend", () => {
    expect(kpiLabel("fraud-rate", "Fraud rate")).toBe("Tasa de fraude");
    expect(kpiTrend("1500 labelled fraud cases")).toBe("1500 casos de fraude etiquetados");
    expect(kpiTrend("Test set · threshold 0.466")).toBe("Conjunto de prueba · umbral 0.466");
    expect(kpiTrend("2,078 blocked at threshold 0.466")).toBe("2,078 bloqueadas con umbral 0.466");
    expect(kpiTrend("Test period Jun–Dec 2020")).toBe("Periodo de prueba jun–dic 2020");
    expect(windowLabel("Dataset snapshot · 100,000 rows")).toBe(
      "Instantánea del dataset · 100,000 filas",
    );
    expect(
      alertDetail("Artifact xgboost-tier2-isotonic-f88d84b82069 loaded with 46 features."),
    ).toBe("Artefacto xgboost-tier2-isotonic-f88d84b82069 cargado con 46 variables.");
  });
});
