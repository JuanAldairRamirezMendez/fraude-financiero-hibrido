import { expect, test } from "@playwright/test";

test.describe("analyzer", () => {
  test("analiza una transacción de alto riesgo y muestra la explicación", async ({ page }) => {
    await page.goto("/analyzer");

    await page.getByLabel("Hora de la transacción (0-23)").fill("22");
    await page.getByLabel("Día de la semana").selectOption("0");
    await page.getByLabel("Categoría del comercio", { exact: true }).selectOption("gambling");
    await page.getByLabel("País de la transacción").selectOption("IN");
    await page.getByLabel("Región geográfica").selectOption("South America");
    await page.getByLabel("Internacional", { exact: true }).selectOption("1");
    await page.getByLabel("Comercio de alto riesgo").selectOption("1");
    await page.getByLabel("Antigüedad de la cuenta (días)").fill("1");
    await page.getByLabel("Contracargos previos").fill("10");
    await page.getByLabel("Transacciones del cliente (30 días)").fill("100");
    await page.getByLabel("Score de riesgo del cliente (0-10)").fill("1");
    await page.getByLabel("Monto de la transacción").fill("7550.07");
    await page.getByLabel("Monto promedio (30 días)").fill("10");
    await page.getByLabel("Transacciones en la última hora").fill("100");
    await page.getByLabel("Transacciones en las últimas 24 h").fill("500");
    await page.getByRole("button", { name: /analizar transacción/i }).click();

    await expect(page.getByText("Evaluación de riesgo")).toBeVisible();
    await expect(page.locator(".gauge-readout strong")).toHaveText("96%");
    await expect(page.locator(".shap-row")).toHaveCount(8);
    await expect(page.getByText("BLOQUEADA", { exact: true })).toBeVisible();
    await expect(page.getByText(/ID de decisión/)).toBeVisible();
  });

  test("valida el formulario antes de llamar al servicio", async ({ page }) => {
    await page.goto("/analyzer");

    await page.getByLabel("Monto de la transacción").fill("0");
    await page.getByRole("button", { name: /analizar transacción/i }).click();

    await expect(page.getByRole("alert").filter({ hasText: "Ingresa un valor entre 0.01 y 1000000" })).toBeVisible();
    await expect(page.getByText("Sin análisis todavía")).toBeVisible();
  });
});
