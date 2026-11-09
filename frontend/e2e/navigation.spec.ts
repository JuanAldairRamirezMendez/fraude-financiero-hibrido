import { expect, test } from "@playwright/test";

test.describe("navegación", () => {
  test("recorre las vistas principales en escritorio", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === "mobile", "en móvil se usa el menú off-canvas");

    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1, name: "Overview" })).toBeVisible();
    await expect(page.locator(".kpi-card")).toHaveCount(4);

    await page.getByRole("link", { name: "Analyzer" }).click();
    await expect(
      page.getByRole("heading", { level: 1, name: "Transaction Analyzer" }),
    ).toBeVisible();

    await page.getByRole("link", { name: "Models" }).click();
    await expect(page.getByRole("heading", { level: 1, name: "Model Health" })).toBeVisible();
    await expect(page.locator(".status-banner")).toContainText("Stable");
  });

  test("abre el menú off-canvas en móvil", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "mobile", "solo aplica al proyecto móvil");

    await page.goto("/");
    await page.getByRole("button", { name: /abrir menú/i }).click();
    await expect(page.getByRole("link", { name: "Models" })).toBeVisible();

    await page.getByRole("link", { name: "Models" }).click();
    await expect(page.getByRole("heading", { level: 1, name: "Model Health" })).toBeVisible();
  });
});
