import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import anatomy from "../anatomy.json";
import { FraudAnatomy } from "./FraudAnatomy";

describe("FraudAnatomy", () => {
  it("resume el episodio con los datos reales de la tarjeta", () => {
    render(<FraudAnatomy />);

    expect(screen.getByText(anatomy.cardId)).toBeInTheDocument();
    expect(
      screen.getByText(`Bloqueó ${anatomy.model.fraudsBlocked} de ${anatomy.model.frauds} fraudes`),
    ).toBeInTheDocument();
    expect(screen.getByRole("img", { name: /Compras de la tarjeta/ })).toBeInTheDocument();
  });

  it("ofrece las compras como tabla accesible", async () => {
    const user = userEvent.setup();
    render(<FraudAnatomy />);

    await user.click(screen.getByText(/Ver las \d+ compras como tabla/));
    const table = screen.getByRole("table", { name: `Compras de la tarjeta ${anatomy.cardId}` });
    expect(within(table).getAllByRole("row")).toHaveLength(anatomy.purchases.length + 1);
  });
});
