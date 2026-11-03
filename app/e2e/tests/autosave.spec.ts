// Autosave por campo (U3): a célula da planilha de variáveis salva ao sair dela, o status mostra
// "Salvo às HH:MM" e recarregar não pede confirmação. Com a rede caída, o status mostra
// "Não salvo: sem conexão · Tentar de novo" e só então sair da página pede confirmação.
// Preparar como em painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e). Grava de verdade
// numa variável do 1º projeto do ano e devolve o valor original no fim.
import { expect, test, type Page } from "@playwright/test";
import { entrar, liberarBloqueio, novoParceiro } from "./helpers";

const ROTA = "**/ui/projeto/*/campo/";

/** Variável de texto livre do 1º projeto da planilha (a regional raramente entra nos templates). */
/** O Alpine já iniciou o `saida` (o :data-estado só existe depois): o `change` já tem quem ouça. */
const pronto = (page: Page) => expect(page.locator("[data-status-salvo]")).toHaveAttribute("data-estado", "");

const celula = (page: Page) => page.locator('tbody[id^="projeto-"]').first().locator('input.input[name$="-nome_regional"]');

/** Sai do campo e espera a resposta do autosave (o "Salvo às" de antes já estaria visível). */
async function sairESalvar(page: Page) {
  const resposta = page.waitForResponse((r) => /\/(campo|celula)\/$/.test(new URL(r.url()).pathname) && r.request().method() === "POST");
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

test("cortes: a célula salva sozinha; a outra aba com o valor antigo recebe conflito, não grava por cima", async ({ page, context }) => {
  const nome = `E2E Autosave ${Date.now().toString(36).toUpperCase()}`;
  await entrar(page, "/cortes/2026/");
  await novoParceiro(page, nome);
  await pronto(page);
  const celulaDe = (p: Page) => p.getByLabel(`${nome} 5EF LP`, { exact: true });
  const status = (p: Page) => p.locator("[data-status-salvo]");

  // Erro de validação: fica na célula, nada grava.
  await celulaDe(page).fill("300 150");
  await page.keyboard.press("Tab");
  await expect(status(page).getByText("Não salvo: corrija o campo marcado")).toBeVisible();
  await expect(celulaDe(page)).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByText("cortes precisam ser crescentes")).toBeVisible();

  // Corrigido: grava e normaliza.
  await celulaDe(page).fill("150 300");
  await sairESalvar(page);
  await expect(celulaDe(page)).toHaveValue("150, 300");
  await expect(celulaDe(page)).not.toHaveAttribute("aria-invalid", "true");

  // Duas abas: a 2ª abre agora (vê 150, 300); a 1ª grava 160, 300; a 2ª tenta 170, 300.
  const outra = await context.newPage();
  await outra.goto("/cortes/2026/");
  await pronto(outra);
  await celulaDe(page).fill("160, 300");
  await sairESalvar(page);
  await celulaDe(outra).fill("170, 300");
  await outra.keyboard.press("Tab");
  await expect(status(outra).getByText("Não salvo: outra pessoa mudou este valor")).toBeVisible();
  await expect(outra.getByText("agora: 160, 300")).toBeVisible();
  await page.reload();
  await expect(celulaDe(page)).toHaveValue("160, 300");

  // "Tentar de novo" na 2ª aba grava por cima, de propósito.
  await status(outra).getByRole("button", { name: "Tentar de novo" }).click();
  await expect(status(outra).getByText(/Salvo às/)).toBeVisible();
  await page.reload();
  await expect(celulaDe(page)).toHaveValue("170, 300");
  await outra.close();
});

test("descritor: salva sozinho; com o bloqueio perdido, nada aparece como salvo e a tela fica só leitura", async ({ page, context }) => {
  await entrar(page, "/ui/matriz/2026/");
  await page.getByRole("link", { name: "Demonstração" }).first().click();
  await page.locator('a[href*="/ui/matriz/mec/"]').first().click();
  await pronto(page);
  const descricao = page.locator("#form-descritor [name=descricao]");
  const original = await descricao.inputValue();

  await descricao.fill(`${original} E2E`);
  await sairESalvar(page);
  await descricao.fill(original);
  await sairESalvar(page);

  // A mesma pessoa abre a MEC em outra aba: o bloqueio passa para ela (D-191).
  const outra = await context.newPage();
  await outra.goto(page.url());
  await expect(outra.locator("#form-descritor [name=descricao]")).toBeEditable();
  await descricao.fill(`${original} perdido`);
  await page.keyboard.press("Tab");
  const status = page.locator("[data-status-salvo]");
  await expect(status.getByText("Não salvo: a página ficou somente leitura")).toBeVisible();
  await expect(status.getByText(/Salvo às/)).toBeHidden();
  await expect(page.getByRole("alert").filter({ hasText: "perdeu o bloqueio" })).toBeVisible();
  await expect(descricao).not.toBeEditable();
  await expect(outra.locator("#form-descritor [name=descricao]")).toHaveValue(original);
  await liberarBloqueio(outra);
  await outra.close();
});

// O cliente diante da resposta de impacto (o servidor real é coberto em test_ui_autosave): a rota
// responde com o modal do U2; Esc volta o valor gravado e o foco; confirmar reenvia com a confirmação.
test("impacto no autosave: Esc volta o valor e o foco; confirmar reenvia confirmado", async ({ page }) => {
  await entrar(page, "/ui/variaveis/2026/");
  await pronto(page);
  const campo = celula(page);
  const original = await campo.inputValue();
  const html = `<dialog class="dialogo impacto" x-data="impacto" data-abrir-ao-carregar data-form="variaveis-form" data-campo="confirmar_impacto" aria-labelledby="t-e2e" @cancel.prevent="cancelar">
    <h2 id="t-e2e">Salvar tira o “Validado” de 1 revista(s)</h2><ul class="impacto-lista"><li>E2E Revista</li></ul>
    <footer><button type="button" class="btn btn-outline" @click="cancelar" autofocus>Cancelar</button>
    <button type="button" class="btn btn-destrutivo" @click="confirmar">Salvar e tirar Validado</button></footer></dialog>`;
  const enviados: string[] = [];
  await page.route(ROTA, async (r) => {
    const confirmado = (r.request().postData() ?? "").includes('name="confirmar_impacto"');
    enviados.push(confirmado ? "confirmado" : "simples");
    const corpo = confirmado ? { ok: true, salvo_em: "10:15" } : { ok: false, impacto: { titulo: "Salvar", perdem: ["E2E Revista"], afetadas: 1, html } };
    await r.fulfill({ json: corpo });
  });
  const modal = page.getByRole("dialog", { name: "Salvar tira o “Validado” de 1 revista(s)" });

  await campo.fill("E2E Com impacto");
  await page.keyboard.press("Tab");
  await expect(modal).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(modal).toHaveCount(0);
  await expect(campo).toHaveValue(original);
  await expect(campo).toBeFocused();

  await campo.fill("E2E Com impacto");
  await page.keyboard.press("Tab");
  await modal.getByRole("button", { name: "Salvar e tirar Validado" }).click();
  await expect(page.locator("[data-status-salvo]").getByText("Salvo às 10:15")).toBeVisible();
  expect(enviados).toEqual(["simples", "simples", "confirmado"]);
  await page.unroute(ROTA);
  await campo.fill(original); // o valor de verdade não mudou (a rota foi simulada)
  const dialogos: string[] = [];
  page.on("dialog", (d) => { dialogos.push(d.type()); void d.dismiss(); });
  await page.reload();
  expect(dialogos).toEqual([]);
});
