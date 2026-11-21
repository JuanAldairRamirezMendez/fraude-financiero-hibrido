import { describe, expect, it } from "vitest";

import {
  BLOCK_THRESHOLD,
  INITIAL_FORM_VALUES,
  normalizeDateTime,
  validateTransactionForm,
  type TransactionFormValues,
} from "./validation";

describe("validateTransactionForm", () => {
  it("construye la compra con tarjeta, fecha, monto, categoría y distancia", () => {
    const result = validateTransactionForm(INITIAL_FORM_VALUES);

    expect(result.errors).toEqual({});
    expect(result.input).toMatchObject({
      cardId: INITIAL_FORM_VALUES.cardId,
      category: INITIAL_FORM_VALUES.category,
      decisionThreshold: Number(BLOCK_THRESHOLD),
    });
    expect(Object.keys(result.input ?? {}).sort()).toEqual([
      "amount",
      "blockThreshold",
      "cardId",
      "category",
      "decisionThreshold",
      "merchantDistanceKm",
      "transactionTime",
    ]);
  });

  it("rechaza valores fuera de rango, tarjetas desconocidas y fechas fuera del dataset", () => {
    const values: TransactionFormValues = {
      ...INITIAL_FORM_VALUES,
      amount: "0",
      cardId: "TARJ-9999",
      category: "gambling",
      transactionTime: "2023-05-01T10:00:00",
    };
    const result = validateTransactionForm(values);

    expect(result.input).toBeNull();
    expect(result.errors.amount).toBeDefined();
    expect(result.errors.cardId).toMatch(/catálogo/);
    expect(result.errors.category).toBeDefined();
    expect(result.errors.transactionTime).toMatch(/2019/);
  });

  it("usa un único umbral: aprobar o bloquear, sin franja de revisión", () => {
    const result = validateTransactionForm({ ...INITIAL_FORM_VALUES, decisionThreshold: "0.3" });

    expect(result.input?.decisionThreshold).toBe(0.3);
    expect(result.input?.blockThreshold).toBe(0.3);
  });

  it("acepta la hora sin segundos que envían algunos navegadores", () => {
    expect(normalizeDateTime("2020-07-07T11:47")).toBe("2020-07-07T11:47:00");
    expect(normalizeDateTime("2020-07-07T11:47:35")).toBe("2020-07-07T11:47:35");
  });
});
