import { expect, test } from "@playwright/test";

test.describe("analyzer", () => {
  test("analiza una transacción de alto riesgo y muestra la explicación", async ({ page }) => {
    await page.goto("/analyzer");

    // Escenario real del periodo de prueba de Sparkov: ráfaga nocturna de compras.
    await page.getByRole("button", { name: /fraude probable/i }).click();
    await page.getByRole("button", { name: /analizar transacción/i }).click();

    await expect(page.getByText("Evaluación de riesgo")).toBeVisible();
    await expect(page.locator(".gauge-readout strong")).toHaveText("100%");
    await expect(page.locator(".shap-row")).toHaveCount(8);
    await expect(page.getByText("BLOQUEADA", { exact: true })).toBeVisible();
    await expect(page.getByLabel("Historial de la tarjeta")).toBeVisible();
    await expect(page.getByText(/ID de decisión/)).toBeVisible();
  });

  test("valida el formulario antes de llamar al servicio", async ({ page }) => {
    await page.goto("/analyzer");

    await page.getByLabel("Monto (US$)").fill("0");
    await page.getByRole("button", { name: /analizar transacción/i }).click();

    await expect(
      page.getByRole("alert").filter({ hasText: "Ingresa un valor entre 0.01 y 50000" }),
    ).toBeVisible();
    await expect(page.getByText("Sin análisis todavía")).toBeVisible();
  });
});
