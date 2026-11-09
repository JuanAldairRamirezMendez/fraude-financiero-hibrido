import { expect, test } from "@playwright/test";

test.describe("analyzer", () => {
  test("analiza una transacción de alto riesgo y muestra la explicación", async ({ page }) => {
    await page.goto("/analyzer");

    await page.getByLabel("Transaction hour").fill("22");
    await page.getByLabel("Day of week").fill("0");
    await page.getByLabel("Merchant category", { exact: true }).selectOption("gambling");
    await page.getByLabel("Transaction country").selectOption("IN");
    await page.getByLabel("Geographic region").selectOption("South America");
    await page.getByLabel("International").selectOption("1");
    await page.getByLabel("High-risk merchant category").selectOption("1");
    await page.getByLabel("Account age (days)").fill("1");
    await page.getByLabel("Previous chargebacks").fill("10");
    await page.getByLabel("Customer transactions (30d)").fill("100");
    await page.getByLabel("Customer risk score").fill("1");
    await page.getByLabel("Transaction amount").fill("7550.07");
    await page.getByLabel("Average amount (30d)").fill("10");
    await page.getByLabel("Transaction velocity (1h)").fill("100");
    await page.getByLabel("Transaction velocity (24h)").fill("500");
    await page.getByRole("button", { name: /analyze transaction/i }).click();

    await expect(page.getByText("Risk Assessment")).toBeVisible();
    await expect(page.locator(".gauge-readout strong")).toHaveText("96%");
    await expect(page.locator(".shap-row")).toHaveCount(8);
    await expect(page.getByText("BLOCKED", { exact: true })).toBeVisible();
    await expect(page.getByText(/Decision ID/)).toBeVisible();
  });

  test("valida el formulario antes de llamar al servicio", async ({ page }) => {
    await page.goto("/analyzer");

    await page.getByLabel("Transaction amount").fill("0");
    await page.getByRole("button", { name: /analyze transaction/i }).click();

    await expect(page.getByRole("alert").filter({ hasText: "Ingresa un valor entre 0.01 y 1000000" })).toBeVisible();
    await expect(page.getByText("Sin análisis todavía")).toBeVisible();
  });
});
