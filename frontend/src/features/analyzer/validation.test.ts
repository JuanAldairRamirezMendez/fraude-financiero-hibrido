import { describe, expect, it } from "vitest";

import {
  INITIAL_FORM_VALUES,
  validateTransactionForm,
  type TransactionFormValues,
} from "./validation";

describe("validateTransactionForm", () => {
  it("construye el payload real de 18 features", () => {
    const result = validateTransactionForm(INITIAL_FORM_VALUES);

    expect(result.errors).toEqual({});
    expect(result.input).toMatchObject({
      transactionAmount: 484.15,
      merchantCategory: "travel",
      transactionCountry: "US",
      decisionThreshold: 0.5,
    });
    expect(Object.keys(result.input ?? {})).toHaveLength(19);
  });

  it("rechaza valores fuera de rango y categorias vacias", () => {
    const values: TransactionFormValues = {
      ...INITIAL_FORM_VALUES,
      transactionAmount: "0",
      transactionHour: "24",
      merchantCategory: "",
    };
    const result = validateTransactionForm(values);

    expect(result.input).toBeNull();
    expect(result.errors.transactionAmount).toBeDefined();
    expect(result.errors.transactionHour).toBeDefined();
    expect(result.errors.merchantCategory).toBeDefined();
  });
});
