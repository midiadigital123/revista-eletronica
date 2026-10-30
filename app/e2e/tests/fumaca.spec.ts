import { expect, test } from "@playwright/test";
import { entrar } from "./helpers";

test("abre a página de login do admin", async ({ page }) => {
  await page.goto("/admin/login/");
  await expect(page.locator("#id_username")).toBeVisible();
  await expect(page.locator("#id_password")).toBeVisible();
});

// Opcional: só roda com E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA no ambiente.
test("entra no admin com o superusuário", async ({ page }) => {
  await entrar(page);
  await expect(page).toHaveURL(/\/admin\/$/);
  await expect(page.locator("#user-tools")).toBeVisible();
});
