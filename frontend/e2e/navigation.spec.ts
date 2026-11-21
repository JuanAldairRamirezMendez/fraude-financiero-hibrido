import { expect, test } from "@playwright/test";

test.describe("navegación", () => {
  test("recorre las vistas principales en escritorio", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name === "mobile", "en móvil se usa el menú off-canvas");

    await page.goto("/");
    await expect(page.getByRole("heading", { level: 1, name: "Resumen" })).toBeVisible();
    await expect(page.locator(".kpi-card")).toHaveCount(4);

    await page.getByRole("link", { name: "Evaluación" }).click();
    await expect(
      page.getByRole("heading", { level: 1, name: "Evaluación del modelo" }),
    ).toBeVisible();
    await expect(page.getByRole("table", { name: "Matriz de confusión" })).toBeVisible();

    await page.getByRole("link", { name: "Analizador" }).click();
    await expect(
      page.getByRole("heading", { level: 1, name: "Analizador de transacciones" }),
    ).toBeVisible();

    await page.getByRole("link", { name: "Revisión de casos" }).click();
    await expect(page.getByRole("heading", { level: 1, name: "Revisión de casos" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Salud del modelo" })).toHaveCount(0);
  });

  test("abre el menú off-canvas en móvil", async ({ page }, testInfo) => {
    test.skip(testInfo.project.name !== "mobile", "solo aplica al proyecto móvil");

    await page.goto("/");
    await page.getByRole("button", { name: /abrir menú/i }).click();
    await expect(page.getByRole("link", { name: "Evaluación" })).toBeVisible();

    await page.getByRole("link", { name: "Evaluación" }).click();
    await expect(
      page.getByRole("heading", { level: 1, name: "Evaluación del modelo" }),
    ).toBeVisible();
  });
});
