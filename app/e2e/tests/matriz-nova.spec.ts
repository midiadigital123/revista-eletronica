// Nova matriz pela tela B (S6): criar no ano → cai no Reimportar → importar a planilha de exemplo → ver os
// descritores → excluir a matriz que o teste criou (E3, ui_excluir). Não deixa nada no banco. O Impresso
// (E2E_IMPRESSO_*) não vê o botão e leva 403 na rota.
import { expect, test } from "@playwright/test";
import path from "node:path";
import { entrar } from "./helpers";

const PLANILHA = path.resolve(__dirname, "../../nucleo/tests/fixtures/planilha-3cortes-LP-5ef.xlsx");

test("Matriz: Nova matriz → importar a planilha → descritores → excluir", async ({ page }) => {
  await entrar(page, "/ui/matriz/2026/");
  const nome = `E2E Nova ${Date.now().toString(36).toUpperCase()}`;
  await page.locator("header.pagina-cab").getByRole("button", { name: "Nova matriz" }).click();
  const dialogo = page.locator("#dlg-nova");
  await expect(dialogo.getByLabel("Ano").locator("option:checked")).toHaveText("2026"); // pré-preenchido com o ano da lista
  await dialogo.getByLabel("Nome").fill(nome);
  await dialogo.getByRole("button", { name: "Criar matriz" }).click();

  await expect(page).toHaveURL(/\/ui\/matriz\/m\/\d+\/reimportar\/$/);
  await expect(page.getByText(/criada\. Importe o arquivo/)).toBeVisible();
  await page.getByLabel("Arquivo").setInputFiles(PLANILHA);
  await page.getByRole("button", { name: "Importar e substituir" }).click();

  await expect(page).toHaveURL(/\/ui\/matriz\/m\/\d+\/$/);
  await expect(page.getByRole("heading", { level: 1, name: nome })).toBeVisible();
  const detalhe = page.url();
  await page.locator('a[href*="/ui/matriz/mec/"]').first().click();
  await expect(page.getByRole("link", { name: /D01/ }).first()).toBeVisible();

  await page.goto(detalhe);
  await page.locator(".zona-perigo").getByRole("link", { name: "Excluir matriz…" }).click();
  await expect(page.getByText("Nada usa isto.")).toBeVisible();
  await page.getByLabel("Para confirmar, digite").fill(nome);
  await page.getByRole("button", { name: "Excluir" }).click();
  await expect(page).toHaveURL(/\/ui\/matriz\/2026\/$/);
  await expect(page.getByRole("link", { name: nome })).toHaveCount(0);
});

test("Matriz: o Impresso não vê Nova matriz e leva 403", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto("/admin/login/?next=/ui/matriz/2026/");
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page.getByRole("heading", { level: 1, name: "Matrizes" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Nova matriz" })).toHaveCount(0);
  expect((await page.goto("/ui/matriz/2026/nova/"))!.status()).toBe(403);
});
