import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { mockOverview } from "../mocks";
import { HighRiskTable } from "./HighRiskTable";

describe("HighRiskTable", () => {
  it("pagina las transacciones de alto riesgo", async () => {
    const user = userEvent.setup();

    render(<HighRiskTable transactions={mockOverview.transactions} />);

    expect(screen.getByText("TXN-8492A")).toBeInTheDocument();
    expect(screen.queryByText("TXN-2F31B")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Next" }));

    expect(screen.getByText("TXN-2F31B")).toBeInTheDocument();
    expect(screen.queryByText("TXN-8492A")).not.toBeInTheDocument();
  });

  it("muestra el estado vacío y deshabilita la exportación", () => {
    render(<HighRiskTable transactions={[]} />);

    expect(screen.getByText("Sin transacciones de alto riesgo")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export CSV" })).toBeDisabled();
  });
});
