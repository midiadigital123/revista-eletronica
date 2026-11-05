// S7: "Novo template" pela tela B. Cria pela lista, cai no editor com a versão 1 e exclui o template criado
// (D-207): nunca grava no "Padrão" real. Mesmo preparo de templates-editor.spec.ts (criar_demo 2026,
// E2E_ADMIN_*; o 2º teste usa E2E_IMPRESSO_*).
import { expect, test } from "@playwright/test";
import { entrar } from "./helpers";
import { excluirTemplate } from "./templates";

test("cria o template pela lista, cai no editor na versão 1 e exclui", async ({ page }) => {
  await entrar(page, "/ui/templates/2026/?aba=F1");
  const nome = `E2E Novo ${Date.now().toString(36).toUpperCase()}`;

  await page.getByRole("link", { name: "Novo template" }).click();
  await expect(page).toHaveURL(/\/ui\/templates\/2026\/novo\/\?aba=F1$/);
  await expect(page.getByLabel("Fascículo")).toHaveValue("F1");
  const lp = page.locator("#id_componente option", { hasText: "LP" }).first();
  await page.selectOption("#id_componente", (await lp.getAttribute("value"))!);
  await page.getByLabel("Nome").fill(nome);

  // Seção fora do fascículo: erro no campo, nada gravado.
  const texto = page.getByLabel("Texto inicial");
  const valido = await texto.inputValue();
  await texto.fill(`${valido}\n## passo1\nT\n\nX.\n`);
  await page.getByRole("button", { name: "Criar template" }).click();
  await expect(page.locator("#texto-erro")).toContainText("passo1");
  await expect(page.getByLabel("Nome")).toHaveValue(nome);

  await texto.fill(valido);
  await page.getByRole("button", { name: "Criar template" }).click();
  await expect(page).toHaveURL(/\/ui\/templates\/editar\/\d+\/$/);
  await expect(page.getByText("Template criado, com a versão 1.")).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: nome })).toBeVisible();
  await expect(page.getByText("Versão atual: 1")).toBeVisible();

  await page.getByRole("link", { name: "Excluir template…" }).click();
  await excluirTemplate(page, nome, "F1");
});

test("impresso não vê Novo template e recebe 403 na rota", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto("/admin/login/?next=/ui/templates/2026/");
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page.getByRole("heading", { level: 1, name: "Templates" })).toBeVisible();
  await expect(page.getByRole("link", { name: "Novo template" })).toHaveCount(0);
  expect((await page.goto("/ui/templates/2026/novo/"))!.status()).toBe(403);
});
