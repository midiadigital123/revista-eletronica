// Página do ano (S4 de D-190): /ui/anos/<ano>/ com etapas e componentes.
// Mesmo preparo de impresso.spec.ts (E2E_ADMIN_* e, para o 2º teste, E2E_IMPRESSO_*).
// Grava de verdade, mas deixa o banco como achou: o componente criado aqui sai pelo "Excluir" da linha, e o ano
// aberto no último teste (o próximo, 2027) é apagado nele mesmo (E1 de D-205/D-206). Nunca apaga 2025 nem 2026.
// Rode só contra um banco descartável.
import { expect, test, type Page } from "@playwright/test";
import { alpinePronto, entrar } from "./helpers";

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

  await page.getByRole("button", { name: "Adicionar componente" }).click(); // U4: a linha nasce no botão
  await page.getByLabel("Código (linha nova)").fill(codigo);
  await page.getByLabel("Nome (linha nova)").fill(`Componente E2E ${codigo}`);
  await page.getByRole("button", { name: "Incluir componente" }).click();

  await expect(page.getByText(`Componentes de ${ano} salvos.`)).toBeVisible();
  await expect(page.getByLabel(`Código (${codigo})`)).toHaveValue(codigo);

  // U3: o nome do componente gravado salva sozinho ao sair do campo.
  await alpinePronto(page);
  const nome = page.getByLabel(`Nome (${codigo})`);
  await nome.fill(`Componente E2E ${codigo} renomeado`);
  const salvou = page.waitForResponse((r) => r.url().endsWith("/campo/") && r.status() === 200);
  await page.keyboard.press("Tab");
  await salvou;
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às/)).toBeVisible();
  await page.reload();
  await expect(page.getByLabel(`Nome (${codigo})`)).toHaveValue(`Componente E2E ${codigo} renomeado`);
  // E1 de D-205: o "Excluir" da linha é link para a página de excluir; sem uso, sai digitando o código.
  await page.getByRole("link", { name: `Excluir componente ${codigo}` }).click();
  await expect(page.getByRole("heading", { level: 1, name: `Excluir o componente ${codigo} de ${ano}` })).toBeVisible();
  await expect(page.getByText("Nada usa isto.")).toBeVisible();
  const excluir = page.getByRole("button", { name: "Excluir", exact: true });
  await expect(excluir).toBeDisabled();
  await page.getByLabel("Para confirmar, digite").fill(codigo);
  await excluir.click();
  await expect(page).toHaveURL(new RegExp(`/ui/anos/${ano}/$`));
  await expect(page.getByText(`Exclusão feita: o componente ${codigo} de ${ano}.`)).toBeVisible();
  await expect(page.getByLabel(`Código (${codigo})`)).toHaveCount(0);
});

test("etapa em uso mostra o que impede e volta para o ano", async ({ page }) => {
  await entrar(page, "/ui/anos/");
  const ano = await abrirMaiorAno(page);
  await page.getByRole("link", { name: "Excluir etapa 5EF" }).click(); // o demo tem cortes e matriz em 5EF
  await expect(page.getByText("Não dá para excluir: isto está em uso.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Excluir", exact: true })).toHaveCount(0);
  await page.getByRole("link", { name: "Voltar sem excluir" }).first().click();
  await expect(page).toHaveURL(new RegExp(`/ui/anos/${ano}/$`));
});

test("impresso não vê o botão de salvar", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto("/admin/login/?next=/ui/anos/");
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page.getByRole("rowheader", { name: "2026", exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: /^Excluir ano/ })).toHaveCount(0); // E1: só o Admin (D-206)
  const ano = await abrirMaiorAno(page);

  await expect(page.getByRole("heading", { name: "Componentes" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Adicionar componente" })).toHaveCount(0);
  await expect(page.getByLabel("Código (linha nova)")).toHaveCount(0);
  await expect(page.getByText(`Ano ${ano}`).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /^Excluir/ })).toHaveCount(0); // E1: o Impresso nunca exclui
});

test("salva o Padrão 5 com o mesmo nome", async ({ page }) => {
  await entrar(page, "/ui/anos/");
  const ano = await abrirMaiorAno(page);
  await expect(page.getByRole("heading", { name: "Padrões" })).toBeVisible();

  // Mesmo valor: não altera o banco nem tira o Validado de ninguém.
  const nome = page.getByLabel("Nome do Padrão 5", { exact: true });
  const atual = await nome.inputValue();
  await nome.fill(atual);
  await page
    .locator("tr", { has: page.getByLabel("Nome do Padrão 5", { exact: true }) })
    .getByRole("button", { name: "Salvar" })
    .click();

  await expect(page.getByText(`Padrão 5 de ${ano} salvo.`)).toBeVisible();
});

test("impresso não vê o input de cor do Padrão 1", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto("/admin/login/?next=/ui/anos/");
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await abrirMaiorAno(page);

  await expect(page.getByRole("heading", { name: "Padrões" })).toBeVisible();
  await expect(page.getByLabel("Cor do Padrão 1", { exact: true })).toHaveCount(0);
});

test("Admin apaga pelo link \"Excluir ano\" o ano que o próprio teste abriu", async ({ page }) => {
  await entrar(page, "/ui/anos/");
  const anos = (await page.locator("tbody th[scope=row]").allTextContents()).map(Number);
  const novo = Math.max(...anos) + 1;
  expect([2025, 2026]).not.toContain(novo);
  await page.getByLabel("Ano novo").fill(String(novo));
  await page.getByRole("button", { name: "Abrir ano" }).click();
  await expect(page.getByText(`Ano ${novo} aberto a partir de`)).toBeVisible();

  await page.getByRole("link", { name: `Excluir ano ${novo}` }).click();
  await expect(page).toHaveURL(new RegExp(`/ui/excluir/ano/${novo}/\\?voltar=/ui/anos/$`));
  await expect(page.getByRole("heading", { level: 1, name: `Apagar o ano ${novo}` })).toBeVisible();
  const apagar = page.getByRole("button", { name: `Apagar o ano ${novo}` });
  await expect(apagar).toBeDisabled();
  await page.getByLabel("Para confirmar, digite").fill(String(novo));
  await apagar.click();

  await expect(page).toHaveURL(/\/ui\/anos\/$/);
  await expect(page.getByText(`Ano ${novo} apagado, com tudo o que era dele.`)).toBeVisible();
  await expect(page.getByRole("rowheader", { name: String(novo), exact: true })).toHaveCount(0);
  await expect(page.getByRole("rowheader", { name: "2026", exact: true })).toBeVisible();
});
