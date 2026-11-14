import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import BenchmarkPage from "./BenchmarkPage";
import { MODEL_RESULTS } from "./data";

function renderPage() {
  return render(
    <MemoryRouter>
      <BenchmarkPage />
    </MemoryRouter>,
  );
}

describe("BenchmarkPage", () => {
  it("muestra las tres familias del sistema híbrido", () => {
    renderPage();

    expect(screen.getByRole("heading", { name: "Redes neuronales" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Machine Learning" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Técnicas de ensamble" })).toBeInTheDocument();
  });

  it("lista todos los modelos evaluados en la tabla", () => {
    renderPage();

    const table = screen.getByRole("table", { name: "Métricas de los modelos evaluados" });
    expect(within(table).getAllByRole("row")).toHaveLength(MODEL_RESULTS.length + 1);
    expect(within(table).getByText("Producción")).toBeInTheDocument();
  });

  it("ordena el gráfico según la métrica elegida", async () => {
    const user = userEvent.setup();
    renderPage();

    const firstBar = () =>
      within(screen.getByRole("list", { name: /Modelos ordenados por/ })).getAllByRole(
        "listitem",
      )[0];

    expect(firstBar()).toHaveTextContent("XGBoost");

    await user.click(screen.getByRole("button", { name: "Recall" }));

    expect(screen.getByRole("button", { name: "Recall" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(firstBar()).toHaveTextContent("SVM lineal");
  });

  it("enlaza al analizador para probar el modelo", () => {
    renderPage();

    expect(screen.getByRole("link", { name: /probar el modelo en vivo/i })).toHaveAttribute(
      "href",
      "/analyzer",
    );
  });
});
