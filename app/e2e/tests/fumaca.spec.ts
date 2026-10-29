import { expect, test } from "@playwright/test";

test("abre a página de login do admin", async ({ page }) => {
  await page.goto("/admin/login/");
  await expect(page.locator("#id_username")).toBeVisible();
  await expect(page.locator("#id_password")).toBeVisible();
});

// Opcional: só roda com E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA no ambiente.
test("entra no admin com o superusuário", async ({ page }) => {
  const usuario = process.env.E2E_ADMIN_USUARIO;
  const senha = process.env.E2E_ADMIN_SENHA;
  test.skip(!usuario || !senha, "defina E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA");

  await page.goto("/admin/login/");
  await page.fill("#id_username", usuario!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page).toHaveURL(/\/admin\/$/);
  await expect(page.locator("#user-tools")).toBeVisible();
});
