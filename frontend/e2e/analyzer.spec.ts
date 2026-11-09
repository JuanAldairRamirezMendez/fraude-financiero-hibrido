import { expect, test } from "@playwright/test";

test.describe("analyzer", () => {
  test("analiza una transacción de alto riesgo y muestra la explicación", async ({ page }) => {
    await page.goto("/analyzer");

    await page.getByLabel("Transaction amount").fill("12000");
    await page.getByRole("button", { name: /analyze transaction/i }).click();

    await expect(page.getByText("Risk Assessment")).toBeVisible();
    await expect(page.locator(".gauge-readout strong")).toHaveText("99%");
    await expect(page.locator(".shap-row")).toHaveCount(6);
    await expect(page.getByText("BLOCKED", { exact: true })).toBeVisible();
    await expect(page.getByText(/Decision ID/)).toBeVisible();
  });

  test("valida el formulario antes de llamar al servicio", async ({ page }) => {
    await page.goto("/analyzer");

    await page.getByLabel("Transaction amount").fill("0");
    await page.getByRole("button", { name: /analyze transaction/i }).click();

    await expect(page.getByText("Ingresa un monto mayor a 0.")).toBeVisible();
    await expect(page.getByText("Sin análisis todavía")).toBeVisible();
  });
});
