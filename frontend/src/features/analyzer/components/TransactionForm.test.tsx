import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TransactionForm } from "./TransactionForm";

describe("TransactionForm", () => {
  it("envía una transacción válida con el contrato tipado", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<TransactionForm isPending={false} onSubmit={onSubmit} />);

    const amount = screen.getByLabelText("Transaction amount");
    await user.clear(amount);
    await user.type(amount, "1200");
    await user.click(screen.getByRole("button", { name: /analyze transaction/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        transactionAmount: 1200,
        decisionThreshold: 0.5,
        previousChargebacks: 0,
        merchantCategory: "travel",
      }),
    );
  });

  it("muestra errores accesibles y no envía datos inválidos", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<TransactionForm isPending={false} onSubmit={onSubmit} />);

    const amount = screen.getByLabelText("Transaction amount");
    await user.clear(amount);
    await user.type(amount, "0");
    await user.click(screen.getByRole("button", { name: /analyze transaction/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/Ingresa un valor entre 0.01 y 1000000/)).toBeInTheDocument();
    expect(amount).toHaveAttribute("aria-invalid", "true");
  });

  it("deshabilita el envío mientras analiza", () => {
    render(<TransactionForm isPending onSubmit={() => undefined} />);

    const button = screen.getByRole("button", { name: /analyzing/i });

    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });
});
