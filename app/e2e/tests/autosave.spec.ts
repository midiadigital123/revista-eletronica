// Autosave por campo (U3): a célula da planilha de variáveis salva ao sair dela, o status mostra
// "Salvo às HH:MM" e recarregar não pede confirmação. Com a rede caída, o status mostra
// "Não salvo: sem conexão · Tentar de novo" e só então sair da página pede confirmação.
// Preparar como em painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e). Grava de verdade
// numa variável do 1º projeto do ano e devolve o valor original no fim.
import { expect, test, type Page } from "@playwright/test";
import { entrar } from "./helpers";

const ROTA = "**/ui/projeto/*/campo/";

/** Variável de texto livre do 1º projeto da planilha (a regional raramente entra nos templates). */
/** O Alpine já iniciou o `saida` (o :data-estado só existe depois): o `change` já tem quem ouça. */
const pronto = (page: Page) => expect(page.locator("[data-status-salvo]")).toHaveAttribute("data-estado", "");

const celula = (page: Page) => page.locator('tbody[id^="projeto-"]').first().locator('input.input[name$="-nome_regional"]');

/** Sai do campo e espera a resposta do autosave (o "Salvo às" de antes já estaria visível). */
async function sairESalvar(page: Page) {
  const resposta = page.waitForResponse((r) => r.url().includes("/campo/") && r.request().method() === "POST");
  await page.keyboard.press("Tab");
  await resposta;
  const status = page.locator("[data-status-salvo]");
  const modal = page.getByRole("dialog");
  await expect(status.getByText(/Salvo às \d\d:\d\d/).or(modal)).toBeVisible();
  if (await modal.isVisible()) await modal.getByRole("button", { name: /e tirar Validado$/ }).click(); // revista validada usa a variável
  await expect(status.getByText(/Salvo às \d\d:\d\d/)).toBeVisible();
}

test("variável salva ao sair do campo e recarregar não pede confirmação", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  await entrar(page, "/ui/variaveis/2026/");
  await pronto(page);
  await expect(page.locator("[data-status-salvo]").getByText("Cada campo salva sozinho")).toBeVisible();
  const campo = celula(page);
  const original = await campo.inputValue();
  const novo = `E2E Regional ${Date.now().toString(36)}`;

  await campo.fill(novo);
  await sairESalvar(page);

  const dialogos: string[] = [];
  page.on("dialog", (d) => { dialogos.push(d.type()); void d.dismiss(); });
  await page.reload();
  await expect(celula(page)).toHaveValue(novo);
  expect(dialogos).toEqual([]);
  await pronto(page);

  await celula(page).fill(original);
  await sairESalvar(page);
  expect(erros).toEqual([]);
});

test("rede caída: Não salvo · Tentar de novo e aviso ao sair só nesse caso", async ({ page }) => {
  await entrar(page, "/ui/variaveis/2026/");
  await pronto(page);
  const campo = celula(page);
  const original = await campo.inputValue();
  const status = page.locator("[data-status-salvo]");

  await page.route(ROTA, (r) => r.abort("internetdisconnected"));
  await campo.fill(`E2E Sem rede ${Date.now().toString(36)}`);
  await page.keyboard.press("Tab");
  await expect(status.getByText("Não salvo: sem conexão")).toBeVisible();
  await expect(status.getByText(/Salvo às/)).toBeHidden(); // o campo não aparece como salvo
  await expect(status.getByRole("button", { name: "Tentar de novo" })).toBeVisible();

  // Sair agora pede confirmação (beforeunload); recusar mantém a página.
  const dialogo = page.waitForEvent("dialog");
  await page.close({ runBeforeUnload: true });
  const d = await dialogo;
  expect(d.type()).toBe("beforeunload");
  await d.dismiss();
  expect(page.isClosed()).toBe(false);

  // A rede volta: "Tentar de novo" grava e o aviso de saída some.
  await page.unroute(ROTA);
  await status.getByRole("button", { name: "Tentar de novo" }).click();
  await expect(status.getByText(/Salvo às \d\d:\d\d/)).toBeVisible();
  await campo.fill(original);
  await sairESalvar(page);
  const dialogos: string[] = [];
  page.on("dialog", (x) => { dialogos.push(x.type()); void x.dismiss(); });
  await page.reload();
  expect(dialogos).toEqual([]);
});
