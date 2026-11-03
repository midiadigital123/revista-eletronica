// Página do ano (S4 de D-190): /ui/anos/<ano>/ com etapas e componentes.
// Mesmo preparo de impresso.spec.ts (E2E_ADMIN_* e, para o 2º teste, E2E_IMPRESSO_*).
// Grava de verdade: o componente criado fica no banco (não há excluir na tela); rode só contra banco de dev.
import { expect, test, type Page } from "@playwright/test";
import { entrar } from "./helpers";

/** Abre a lista de anos e clica no link do maior ano. Devolve o ano. */
async function abrirMaiorAno(page: Page) {
  await page.goto("/ui/anos/");
  const anos = (await page.locator("tbody th[scope=row]").allTextContents()).map(Number);
  expect(anos.length).toBeGreaterThan(0);
  const ano = Math.max(...anos);
  await page.getByRole("link", { name: `Etapas e componentes de ${ano}` }).click();
  await expect(page.getByRole("heading", { level: 1, name: `Ano ${ano}` })).toBeVisible();
  return ano;
}

test("adiciona um componente na página do ano", async ({ page }) => {
  await entrar(page, "/ui/anos/");
  const ano = await abrirMaiorAno(page);
  const codigo = `Z${Date.now().toString().slice(-5)}`;

  await page.getByLabel("Código (linha nova)").last().fill(codigo);
  await page.getByLabel("Nome (linha nova)").fill(`Componente E2E ${codigo}`);
  await page.getByRole("button", { name: "Salvar componentes" }).click();

  await expect(page.getByText(`Componentes de ${ano} salvos.`)).toBeVisible();
  await expect(page.getByLabel(`Código (${codigo})`)).toHaveValue(codigo);
});

test("impresso não vê o botão de salvar", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto("/admin/login/?next=/ui/anos/");
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  const ano = await abrirMaiorAno(page);

  await expect(page.getByRole("heading", { name: "Componentes" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Salvar componentes" })).toHaveCount(0);
  await expect(page.getByLabel("Código (linha nova)")).toHaveCount(0);
  await expect(page.getByText(`Ano ${ano}`).first()).toBeVisible();
});
