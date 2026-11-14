import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/config/env", () => ({ env: { apiBaseUrl: "/api/v1", useMocks: true } }));

const { default: AnalyzerPage } = await import("./AnalyzerPage");

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>
        <AnalyzerPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AnalyzerPage", () => {
  it("conserva el formulario y el último análisis al salir y volver", async () => {
    const user = userEvent.setup();
    const first = renderPage();

    await user.click(screen.getByRole("button", { name: /Fraude probable/ }));
    await user.click(screen.getByRole("button", { name: /Analizar transacción/ }));
    expect(
      await screen.findByText("Bloqueada por riesgo de fraude", undefined, { timeout: 3000 }),
    ).toBeInTheDocument();

    // Equivale a ir a Revisión de casos: la página se desmonta por completo.
    first.unmount();
    renderPage();

    expect(screen.getByText("Bloqueada por riesgo de fraude")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Fraude probable/ })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.queryByText("Sin análisis todavía")).not.toBeInTheDocument();
  });
});
