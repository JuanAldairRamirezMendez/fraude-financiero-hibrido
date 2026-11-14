import { fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import EvaluationPage from "./EvaluationPage";
import { EVALUATION, cheapestThreshold, costAt, countsAt, metricsOf } from "./data";

describe("datos de evaluación", () => {
  it("cubre el conjunto de prueba completo en cada umbral", () => {
    for (const row of EVALUATION.thresholds) {
      expect(row.tp + row.fp + row.fn + row.tn).toBe(EVALUATION.dataset.testRows);
      expect(row.tp + row.fn).toBe(EVALUATION.dataset.testFrauds);
    }
  });

  it("detecta menos fraude y da menos falsas alarmas al subir el umbral", () => {
    const low = countsAt(0.1);
    const high = countsAt(0.9);
    expect(low.tp).toBeGreaterThan(high.tp);
    expect(low.fp).toBeGreaterThan(high.fp);
  });

  it("calcula métricas y costo de forma coherente", () => {
    const metrics = metricsOf({ tp: 3, fp: 1, fn: 1, tn: 95 });
    expect(metrics.precision).toBeCloseTo(0.75);
    expect(metrics.recall).toBeCloseTo(0.75);
    expect(metrics.f1).toBeCloseTo(0.75);

    const cheapest = cheapestThreshold(25);
    for (const row of EVALUATION.thresholds.filter((r) => r.threshold > 0 && r.threshold < 1)) {
      expect(costAt(cheapest, 25).total).toBeLessThanOrEqual(costAt(row, 25).total);
    }
  });
});

describe("EvaluationPage", () => {
  it("muestra el resultado con el umbral calibrado", () => {
    render(<EvaluationPage />);

    const matrix = screen.getByRole("table", { name: "Matriz de confusión" });
    expect(within(matrix).getByText(String(EVALUATION.calibrated.tp))).toBeInTheDocument();
    expect(screen.getByText("calibrado")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "¿Qué aprendió el modelo?" })).toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: "IA vs. reglas tradicionales" }),
    ).not.toBeInTheDocument();
  });

  it("actualiza la matriz al mover el umbral y permite volver al calibrado", async () => {
    const user = userEvent.setup();
    render(<EvaluationPage />);

    fireEvent.change(screen.getByLabelText(/Umbral:/), { target: { value: "0.9" } });

    const matrix = screen.getByRole("table", { name: "Matriz de confusión" });
    expect(within(matrix).getByText(String(countsAt(0.9).tp))).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Volver al umbral calibrado/ }));
    expect(screen.getByText("calibrado")).toBeInTheDocument();
  });
});
