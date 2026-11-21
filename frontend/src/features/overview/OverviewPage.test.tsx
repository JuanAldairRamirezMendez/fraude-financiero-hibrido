import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import OverviewPage from "./OverviewPage";

function renderPage(entry: string) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[entry]}>
        <OverviewPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("OverviewPage", () => {
  it("muestra el estado de carga y luego los indicadores y el perfil de fraude", async () => {
    renderPage("/");

    expect(screen.getByText("Cargando panel de transacciones…")).toBeInTheDocument();
    expect(
      await screen.findByText("Transacciones totales", undefined, { timeout: 3000 }),
    ).toBeInTheDocument();
    expect(screen.getByText("¿Dónde se concentra el fraude?")).toBeInTheDocument();
  });

  it("ya no muestra la tabla de transacciones del snapshot", async () => {
    renderPage("/");

    await screen.findByText("Transacciones totales", undefined, { timeout: 3000 });
    expect(screen.queryByText("Transacciones recientes de alto riesgo")).not.toBeInTheDocument();
    expect(screen.queryByText("Transacciones del snapshot")).not.toBeInTheDocument();
  });
});
