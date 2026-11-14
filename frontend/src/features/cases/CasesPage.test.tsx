import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { FraudCase } from "./api";

vi.mock("@/config/env", () => ({ env: { apiBaseUrl: "/api/v1", useMocks: false } }));
vi.mock("@/app/auth/AuthContext", () => ({ useAuth: () => ({ user: { username: "ana" } }) }));

const apiRequest = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiRequest: (...args: unknown[]) => apiRequest(...args),
}));

const { CasesPage } = await import("./CasesPage");

function makeCase(overrides: Partial<FraudCase> = {}): FraudCase {
  return {
    id: "c1",
    caseNumber: "CASE-AAA111",
    decisionId: "DEC-1",
    status: "new",
    assignedTo: null,
    verdict: null,
    feedbackComment: null,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    resolvedAt: null,
    notes: [],
    decision: {
      probability: 0.48,
      score: 48,
      level: "medium",
      decision: "block",
      modelVersion: "test",
      transaction: {
        transactionAmount: 4560,
        avgTransactionAmount30dCustomer: 380,
        merchantCategory: "luxury_goods",
        transactionCountry: "BR",
        geoLocationRegion: "South America",
        previousChargebacks: 2,
      },
      shap: [{ feature: "previous_chargebacks", impact: 1.2, direction: "increases" }],
    },
    ...overrides,
  };
}

function renderPage(entry = "/cases") {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[entry]}>
        <CasesPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("CasesPage", () => {
  beforeEach(() => apiRequest.mockReset());

  it("muestra la cola, los indicadores y el detalle del caso pendiente", async () => {
    const resolved = makeCase({
      id: "c2",
      caseNumber: "CASE-BBB222",
      status: "resolved",
      verdict: "confirmed_fraud",
      resolvedAt: new Date().toISOString(),
    });
    apiRequest.mockResolvedValue({ items: [makeCase(), resolved], total: 2 });

    renderPage();

    const queue = await screen.findByRole("list", { name: "Cola de casos" });
    expect(within(queue).getByText("CASE-AAA111")).toBeInTheDocument();
    expect(within(queue).queryByText("CASE-BBB222")).not.toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "CASE-AAA111" })).toBeInTheDocument();
    expect(screen.getAllByText("Contracargos previos").length).toBeGreaterThan(0);
    expect(screen.getByText("Artículos de lujo")).toBeInTheDocument();
  });

  it("libera una transacción con el veredicto del analista", async () => {
    const user = userEvent.setup();
    apiRequest.mockImplementation((path: string, options?: { method?: string }) =>
      Promise.resolve(options?.method === "PATCH" ? makeCase() : { items: [makeCase()], total: 1 }),
    );

    renderPage();

    await user.type(await screen.findByLabelText(/Comentario del analista/), "Cliente confirmó");
    await user.click(screen.getByRole("button", { name: /Liberar transacción/ }));

    expect(apiRequest).toHaveBeenCalledWith("/cases/c1", {
      method: "PATCH",
      body: {
        status: "resolved",
        verdict: "false_positive",
        assignedTo: "ana",
        note: "Cliente confirmó",
        feedbackComment: "Cliente confirmó",
      },
    });
  });

  it("invita a usar el Analizador cuando no hay casos", async () => {
    apiRequest.mockResolvedValue({ items: [], total: 0 });

    renderPage();

    expect(await screen.findByText("No hay transacciones bloqueadas")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir al Analizador" })).toHaveAttribute(
      "href",
      "/analyzer",
    );
  });
});
