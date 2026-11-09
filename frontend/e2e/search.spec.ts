import { expect, test } from "@playwright/test";

test.describe("búsqueda global", () => {
  test("filtra las transacciones por cliente", async ({ page }) => {
    await page.goto("/");

    const search = page.getByLabel("Buscar transacciones por ID o cliente");
    await search.fill("Olivia");
    await search.press("Enter");

    await expect(page).toHaveURL(/\?q=Olivia/);
    await expect(page.getByRole("cell", { name: "Olivia Martin" })).toBeVisible();
    await expect(page.locator("tbody tr")).toHaveCount(1);
  });

  test("muestra el estado vacío sin coincidencias", async ({ page }) => {
    await page.goto("/?q=sin-coincidencias");

    await expect(page.getByText("Sin transacciones de alto riesgo")).toBeVisible();
  });
});
