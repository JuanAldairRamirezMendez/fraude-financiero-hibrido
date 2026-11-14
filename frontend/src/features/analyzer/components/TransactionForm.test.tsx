import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { TransactionForm } from "./TransactionForm";

describe("TransactionForm", () => {
  it("envía una transacción válida con el contrato tipado", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<TransactionForm isPending={false} onSubmit={onSubmit} />);

    const amount = screen.getByLabelText("Monto de la transacción");
    await user.clear(amount);
    await user.type(amount, "1200");
    await user.click(screen.getByRole("button", { name: /analizar transacción/i }));

    expect(onSubmit).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        transactionAmount: 1200,
        decisionThreshold: 0.247,
        previousChargebacks: 0,
        merchantCategory: "travel",
      }),
      null,
    );
  });

  it("muestra errores accesibles y no envía datos inválidos", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<TransactionForm isPending={false} onSubmit={onSubmit} />);

    const amount = screen.getByLabelText("Monto de la transacción");
    await user.clear(amount);
    await user.type(amount, "0");
    await user.click(screen.getByRole("button", { name: /analizar transacción/i }));

    expect(onSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/Ingresa un valor entre 0.01 y 1000000/)).toBeInTheDocument();
    expect(amount).toHaveAttribute("aria-invalid", "true");
  });

  it("deshabilita el envío mientras analiza", () => {
    render(<TransactionForm isPending onSubmit={() => undefined} />);

    const button = screen.getByRole("button", { name: /analizando/i });

    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
  });

  it("carga un escenario de demostración y lo envía", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<TransactionForm isPending={false} onSubmit={onSubmit} />);

    const fraud = screen.getByRole("button", { name: /fraude probable/i });
    await user.click(fraud);

    expect(fraud).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByLabelText("Monto de la transacción")).toHaveValue(7800);
    expect(screen.getByText(/Apuestas a las 3 a\. m\./)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /analizar transacción/i }));

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        merchantCategory: "gambling",
        transactionCountry: "NG",
        previousChargebacks: 4,
        transactionAmount: 7800,
      }),
      null,
    );
  });

  it("desmarca el escenario cuando se edita un campo", async () => {
    const user = userEvent.setup();

    render(<TransactionForm isPending={false} onSubmit={() => undefined} />);

    const normal = screen.getByRole("button", { name: /compra habitual/i });
    await user.click(normal);
    expect(normal).toHaveAttribute("aria-pressed", "true");

    await user.type(screen.getByLabelText("Monto de la transacción"), "1");

    expect(normal).toHaveAttribute("aria-pressed", "false");
  });

  it("carga una transacción real y la envía junto con su muestra", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<TransactionForm isPending={false} onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /transacción real al azar/i }));
    expect(screen.getByText(/se revela después del análisis/)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /analizar transacción/i }));

    const [input, sample] = onSubmit.mock.calls[0];
    expect(sample).not.toBeNull();
    expect(input.transactionAmount).toBe(Number(sample.values.transactionAmount));
    expect(input.decisionThreshold).toBe(0.247);
  });

  it("descarta la muestra real si se edita un campo", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<TransactionForm isPending={false} onSubmit={onSubmit} />);

    await user.click(screen.getByRole("button", { name: /transacción real al azar/i }));
    await user.type(screen.getByLabelText("Monto de la transacción"), "1");
    await user.click(screen.getByRole("button", { name: /analizar transacción/i }));

    expect(onSubmit.mock.calls[0][1]).toBeNull();
  });
});
