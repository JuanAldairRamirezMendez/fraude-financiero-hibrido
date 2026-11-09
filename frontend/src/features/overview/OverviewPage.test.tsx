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
  it("muestra el estado de carga y luego los datos", async () => {
    renderPage("/");

    expect(screen.getByText("Cargando panel de transacciones…")).toBeInTheDocument();
    expect(
      await screen.findByText("Olivia Martin", undefined, { timeout: 3000 }),
    ).toBeInTheDocument();
    expect(screen.getByText("Total transactions")).toBeInTheDocument();
  });

  it("filtra la tabla por el término de búsqueda", async () => {
    renderPage("/?q=olivia");

    expect(
      await screen.findByText("Olivia Martin", undefined, { timeout: 3000 }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Noah Williams")).not.toBeInTheDocument();
    expect(screen.getByText(/Showing/, { selector: ".chart-toolbar > span" })).toHaveTextContent(
      "Showing 1 of 1,428,391 processed transactions",
    );
  });

  it("muestra el estado vacío cuando no hay coincidencias", async () => {
    renderPage("/?q=sin-coincidencias");

    expect(
      await screen.findByText("Sin transacciones de alto riesgo", undefined, { timeout: 3000 }),
    ).toBeInTheDocument();
  });
});
