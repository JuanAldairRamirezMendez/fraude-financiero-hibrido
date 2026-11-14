import { describe, expect, it } from "vitest";

import { alertDetail, featureLabel, kpiLabel, kpiTrend, windowLabel } from "./labels";

describe("labels", () => {
  it("traduce variables simples y one-hot del modelo", () => {
    expect(featureLabel("customer_risk_score")).toBe("Score de riesgo del cliente");
    expect(featureLabel("merchant_category_gambling")).toBe("Categoría del comercio: Apuestas");
    expect(featureLabel("geo_location_region_North America")).toBe("Región: Norteamérica");
    expect(featureLabel("transaction_country_NG")).toBe("País: Nigeria (NG)");
  });

  it("devuelve el valor original si no lo conoce", () => {
    expect(featureLabel("nueva_variable")).toBe("nueva_variable");
    expect(kpiTrend("texto desconocido")).toBe("texto desconocido");
    expect(kpiLabel("otro", "Fallback")).toBe("Fallback");
  });

  it("traduce los textos del snapshot del backend", () => {
    expect(kpiLabel("fraud-rate", "Fraud rate")).toBe("Tasa de fraude");
    expect(kpiTrend("1500 labelled fraud cases")).toBe("1500 casos de fraude etiquetados");
    expect(kpiTrend("654 flagged · 303 review")).toBe("654 marcadas · 303 en revisión");
    expect(windowLabel("Dataset snapshot · 100,000 rows")).toBe(
      "Instantánea del dataset · 100,000 filas",
    );
    expect(
      alertDetail("Artifact xgboost-tier2-isotonic-f88d84b82069 loaded with 46 features."),
    ).toBe("Artefacto xgboost-tier2-isotonic-f88d84b82069 cargado con 46 variables.");
  });
});
