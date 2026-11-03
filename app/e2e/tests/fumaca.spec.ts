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

// U1 (D-195): Alpine (build CSP) e SortableJS carregam em toda tela B, sem erro no console.
test("tela B carrega Alpine e SortableJS sem erro", async ({ page }) => {
  const erros: string[] = [];
  page.on("console", (m) => { if (m.type() === "error") erros.push(m.text()); });
  page.on("pageerror", (e) => erros.push(e.message));
  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  await expect.poll(() => page.evaluate(() => !!(window as any).Alpine && !!(window as any).Sortable)).toBe(true);
  expect(erros).toEqual([]);
});
