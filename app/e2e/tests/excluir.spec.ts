// Exclusão do que não está em uso (E0 de D-205/D-206/D-208): a página /ui/excluir/<modelo>/<pk>/, acessada
// direto (os botões nas telas vêm nos passos E1–E5). Mesmo preparo de impresso.spec.ts: criar_demo 2026, o ano
// 2025 vazio, E2E_ADMIN_* (superusuário) e E2E_IMPRESSO_*. Grava de verdade, mas deixa o banco como achou: o
// parceiro "E2E…" criado aqui sai, o desativar volta a ativo, e o ano aberto aqui (o próximo, 2027) é apagado.
// Nunca apaga 2025 nem 2026. Rode só contra um banco descartável.
import { expect, test, type Page } from "@playwright/test";
import { entrar } from "./helpers";

async function criarParceiro(page: Page, nome: string) {
  await page.goto("/admin/nucleo/parceiro/add/");
  await page.fill("#id_nome", nome);
  await page.click("input[name=_continue]");
  await expect(page).toHaveURL(/\/admin\/nucleo\/parceiro\/\d+\/change\//);
  return page.url().match(/parceiro\/(\d+)\/change/)![1];
}

/** Confirmação forte: o botão só libera com o texto exato (ui.js); o servidor confere de novo. */
async function confirmar(page: Page, texto: string, botao: string) {
  const enviar = page.getByRole("button", { name: botao });
  await expect(enviar).toBeDisabled();
  await page.getByLabel("Para confirmar, digite").fill(texto);
  await enviar.click();
}

test("exclui um parceiro livre digitando o nome", async ({ page }) => {
  await entrar(page);
  const nome = `E2E Excluir ${Date.now().toString(36).toUpperCase()}`;
  const pk = await criarParceiro(page, nome);

  await page.goto(`/ui/excluir/parceiro/${pk}/?voltar=/ui/anos/`);
  await expect(page.getByRole("heading", { level: 1, name: `Excluir o parceiro ${nome}` })).toBeVisible();
  await expect(page.getByText("Nada usa isto.")).toBeVisible();
  await confirmar(page, nome, "Excluir");

  await expect(page).toHaveURL(/\/ui\/anos\/$/);
  await expect(page.getByText(`Exclusão feita: o parceiro ${nome}.`)).toBeVisible();
  expect((await page.goto(`/ui/excluir/parceiro/${pk}/`))!.status()).toBe(404);
});

test("parceiro em uso mostra o que impede e oferece desativar", async ({ page }) => {
  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  // Uma célula preenchida da grade: o nome dela é c-<parceiro>-<etapa>-<componente>.
  const campo = await page.locator("[data-grade] tbody input[name^='c-']").evaluateAll(
    (els) => (els as HTMLInputElement[]).find((e) => e.value.trim())?.name,
  );
  expect(campo).toBeTruthy();
  const pk = campo!.split("-")[1];

  await page.goto(`/ui/excluir/parceiro/${pk}/`);
  await expect(page.getByText("Não dá para excluir: isto está em uso.")).toBeVisible();
  const linha = page.getByRole("row", { name: /^Cortes/ });
  await expect(linha).toBeVisible();
  await expect(linha.getByRole("link").first()).toHaveAttribute("href", "/ui/projeto/ano/2026/cortes/");
  await expect(page.getByRole("button", { name: "Excluir" })).toHaveCount(0);

  // D-208: desativar e voltar a ativo (o demo fica como estava).
  await page.getByRole("button", { name: "Desativar o parceiro" }).click();
  await expect(page.getByText(/desativado: sai da grade/)).toBeVisible();
  await page.getByRole("button", { name: "Reativar o parceiro" }).click();
  await expect(page.getByText(/reativado\./)).toBeVisible();
  await expect(page.getByRole("button", { name: "Desativar o parceiro" })).toBeVisible();
});

test("Admin apaga o ano que o próprio teste abriu", async ({ page }) => {
  await entrar(page, "/ui/anos/");
  const anos = (await page.locator("tbody th[scope=row]").allTextContents()).map(Number);
  const novo = Math.max(...anos) + 1;
  expect([2025, 2026]).not.toContain(novo);
  await page.getByLabel("Ano novo").fill(String(novo));
  await page.getByRole("button", { name: "Abrir ano" }).click();
  await expect(page.getByText(`Ano ${novo} aberto a partir de`)).toBeVisible();

  await page.goto(`/ui/excluir/ano/${novo}/`);
  await expect(page.getByRole("heading", { level: 1, name: `Apagar o ano ${novo}` })).toBeVisible();
  await expect(page.getByRole("row", { name: /^Templates \d+/ })).toBeVisible(); // o abrir ano copiou templates
  await expect(page.getByRole("row", { name: /^Versões de template \d+/ })).toBeVisible();
  await page.getByLabel("Para confirmar, digite").fill("2026"); // o ano errado não libera
  await expect(page.getByRole("button", { name: `Apagar o ano ${novo}` })).toBeDisabled();
  await confirmar(page, String(novo), `Apagar o ano ${novo}`);

  await expect(page).toHaveURL(/\/ui\/anos\/$/);
  await expect(page.getByText(`Ano ${novo} apagado, com tudo o que era dele.`)).toBeVisible();
  await expect(page.getByRole("rowheader", { name: String(novo), exact: true })).toHaveCount(0);
  await expect(page.getByRole("rowheader", { name: "2026", exact: true })).toBeVisible();
});

test("impresso não chega à página de excluir", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto("/admin/login/?next=/ui/anos/");
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page).not.toHaveURL(/\/admin\/login\//);
  expect((await page.goto("/ui/excluir/ano/2025/"))!.status()).toBe(403);
});
