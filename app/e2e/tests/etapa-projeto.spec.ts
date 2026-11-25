// Etapa do projeto (D-280, D-288, D-292, D-294): a cópia local de uma etapa da matriz ("Editar só neste
// projeto"), o aviso no editor da matriz, o desfazer, a revisão quando a base muda, o modal de impacto e o
// que o Impresso vê. Preparo de impresso.spec.ts (criar_demo --ano 2026, E2E_ADMIN_* e E2E_IMPRESSO_*).
// Cada teste cria a própria matriz (matrizPropria, cópia "E2E …" da Demonstração) e a própria revista
// (revistaPropria com essa matriz) e grava só nelas (D-225): copiar a partir da Demonstração poria o aviso
// "têm cópia a partir desta etapa" nos outros specs. A cópia do projeto é editada pela tela B
// (/ui/matriz/mec/<pk>/): o admin filtra por matriz e não a acha. O limpar.ts apaga tudo no fim (D-224).
// Fora daqui, com teste Django: "Apontar" (etapa não canônica, D-295) e a imagem do item na revisão.
import { expect, test, type Browser, type Page } from "@playwright/test";
import { alpinePronto, entrar, liberarBloqueio, matrizPropria, revistaPropria } from "./helpers";

const ORIGINAL = "Descritor 1 de demonstração (5EF).";
const marca = () => Date.now().toString(36).toUpperCase();

/** Matriz e revista próprias; devolve também o nome do projeto (o que as telas mostram). */
async function preparar(page: Page, prefixo: string) {
  await entrar(page, "/ui/matriz/2026/");
  const matriz = await matrizPropria(page, prefixo);
  const { nome, revista } = await revistaPropria(page, prefixo, matriz.nome);
  return { matriz, revista, parceiro: nome, projeto: `${nome} projeto` };
}

/** A linha de 5EF LP no cartão "Etapas do projeto" da aba Matriz. */
const linha5ef = (page: Page) =>
  page.locator(".pj-etapas-projeto li").filter({ has: page.locator("strong", { hasText: /^5EF LP$/ }) });

/** Abre a aba Matriz do projeto do `parceiro` (pela Lista) e devolve a URL dela. */
async function abaMatriz(page: Page, parceiro: string) {
  await page.goto("/ui/projeto/ano/2026/");
  await page.getByRole("link", { name: parceiro }).first().click();
  await expect(page).toHaveURL(/\/ui\/projeto\/\d+\//);
  const url = `${new URL(page.url()).pathname}?aba=matriz`;
  await page.goto(url);
  await expect(linha5ef(page)).toBeVisible();
  return url;
}

/** "Editar só neste projeto" em 5EF LP: cria a cópia e cai no editor dela. Devolve a URL do editor. */
async function criarCopia(page: Page, parceiro: string, matriz: string) {
  const aba = await abaMatriz(page, parceiro);
  await expect(linha5ef(page)).toContainText(`usa a matriz ${matriz}`);
  await linha5ef(page).getByRole("button", { name: /^Editar só neste projeto/ }).click();
  await expect(page).toHaveURL(/\/ui\/matriz\/mec\/\d+\/$/);
  await expect(page.locator("#mensagens")).toContainText("5EF LP: cópia criada.");
  return { aba, copia: new URL(page.url()).pathname };
}

/** O editor de 5EF LP da matriz `url` (a página da matriz). */
async function editorDaMatriz(page: Page, url: string) {
  await page.goto(url);
  await page.getByRole("link", { name: "5EF LP", exact: true }).click();
  await expect(page).toHaveURL(/\/ui\/matriz\/mec\/\d+\/$/);
  return new URL(page.url()).pathname;
}

/** No editor `editor` (matriz ou cópia), abre o descritor `codigo` e devolve o campo Descrição. */
async function descricaoDe(page: Page, editor: string, codigo: string) {
  await page.goto(editor);
  const link = page.locator("#lista-descritores a").filter({ has: page.locator(".matriz-codigo", { hasText: new RegExp(`^${codigo}$`) }) });
  await page.goto((await link.getAttribute("href"))!);
  await alpinePronto(page);
  return page.locator("#form-descritor [name=descricao]");
}

/** Troca a descrição e sai do campo; devolve a resposta do autosave (ok ou impacto). */
async function descrever(page: Page, editor: string, codigo: string, texto: string) {
  const campo = await descricaoDe(page, editor, codigo);
  const resposta = page.waitForResponse((r) => r.url().endsWith("/campo/") && r.request().method() === "POST");
  await campo.fill(texto);
  await campo.press("Tab");
  return (await resposta).json();
}

const salvo = (page: Page) => page.locator("[data-status-salvo]").getByText(/Salvo às \d\d:\d\d/);

/** O HTML do F1 da prévia: os descritores vão no JSON da página. */
const previa = async (page: Page, revista: string) => (await page.request.get(`/preview/${revista}/f1/`)).text();

/** Ficha da revista (tela B): a Situação. */
async function situacao(page: Page, revista: string) {
  await page.goto(`/ui/revista/2026/${revista}/`);
  await alpinePronto(page);
  return page.locator("#situacao");
}

async function validar(page: Page, revista: string) {
  const s = await situacao(page, revista);
  await s.locator("#botao-validado").click();
  await expect(s).toContainText("Validada por");
  await liberarBloqueio(page);
}

async function entrarComo(browser: Browser, usuario: string, senha: string, destino: string) {
  const page = await (await browser.newContext()).newPage();
  await page.goto(`/admin/login/?next=${encodeURIComponent(destino)}`);
  await page.fill("#id_username", usuario);
  await page.fill("#id_password", senha);
  await page.click("input[type=submit]");
  await expect(page).not.toHaveURL(/\/entrar\//);
  return page;
}

test("cópia local: a edição vale só para o projeto, a matriz avisa e desfazer volta à matriz", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const { matriz, revista, parceiro, projeto } = await preparar(page, "Etapa copia");
  const novo = `Texto so do projeto ${marca()}.`;

  // 1. "Editar só neste projeto" abre o editor da cópia; a descrição nova aparece na prévia.
  const { aba, copia } = await criarCopia(page, parceiro, matriz.nome);
  await expect(page.getByText(/têm cópia a partir desta etapa/)).toHaveCount(0); // a cópia não é base de ninguém
  expect((await descrever(page, copia, "D01", novo)).ok).toBe(true);
  await expect(salvo(page)).toBeVisible();
  expect(await previa(page, revista)).toContain(novo);

  // 2. A matriz continua com o texto antigo e avisa quem copiou dela.
  const daMatriz = await editorDaMatriz(page, matriz.url);
  expect(daMatriz).not.toBe(copia);
  await expect(page.getByText(`1 projeto(s) têm cópia a partir desta etapa: ${projeto}.`)).toBeVisible();
  await expect(await descricaoDe(page, daMatriz, "D01")).toHaveValue(ORIGINAL);
  await liberarBloqueio(page);

  // 3. Desfazer pede "5EF LP"; a linha volta a usar a matriz e a prévia, ao texto dela.
  await page.goto(aba);
  await expect(linha5ef(page)).toContainText(`cópia do projeto · base: 5EF LP da ${matriz.nome}`);
  await linha5ef(page).getByRole("link", { name: /^Desfazer/ }).click();
  const enviar = page.locator("form [data-confirmado]"); // o rótulo muda com a cópia local: não depender dele
  await expect(enviar).toBeDisabled();
  await page.getByLabel("Para confirmar, digite").fill("5EF LP");
  await enviar.click();
  await expect(page).toHaveURL(/\?aba=matriz$/);
  await expect(linha5ef(page)).toContainText(`usa a matriz ${matriz.nome}`);
  await expect(linha5ef(page).getByRole("button", { name: /^Editar só neste projeto/ })).toBeVisible();
  expect(await previa(page, revista)).not.toContain(novo);
  expect((await page.goto(copia))!.status()).toBe(404);
  expect(erros).toEqual([]);
});

test("a base mudou: o Validado espera a revisão; manter o do projeto e concluir libera", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const { matriz, revista, parceiro } = await preparar(page, "Etapa revisao");
  const m = marca();
  const [doProjeto, daBase, soBase] = [`Projeto E2E ${m} um.`, `Base E2E ${m} um.`, `Base E2E ${m} dois.`];

  // 1. D01 muda na cópia e na matriz (conflito); D02 só na matriz (entra sem conflito).
  const { aba, copia } = await criarCopia(page, parceiro, matriz.nome);
  expect((await descrever(page, copia, "D01", doProjeto)).ok).toBe(true);
  const daMatriz = await editorDaMatriz(page, matriz.url);
  expect((await descrever(page, daMatriz, "D01", daBase)).ok).toBe(true);
  expect((await descrever(page, daMatriz, "D02", soBase)).ok).toBe(true);
  await expect(salvo(page)).toBeVisible();
  await liberarBloqueio(page);

  // 2. A revista ganha a pendência e o "Validar revista" fica travado; a prévia segue com a cópia.
  const s = await situacao(page, revista);
  await expect(s).toContainText("A etapa 5EF tem mudanças da base para revisar.");
  await expect(s.locator("#botao-validado")).toBeDisabled();
  await liberarBloqueio(page);
  const antes = await previa(page, revista);
  expect(antes).toContain(doProjeto);
  expect(antes).not.toContain(soBase);

  // 3. Aba Matriz: "A base mudou" e o link da revisão. O conflito vem aberto, sem escolha, com o que a
  // base trocou; o que só a base mudou vem recolhido, já em "Usar o da base".
  await page.goto(aba);
  await expect(linha5ef(page).getByText("A base mudou")).toBeVisible();
  await linha5ef(page).getByRole("link", { name: /^Revisar mudanças da base/ }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Revisar mudanças da base · 5EF LP" })).toBeVisible();
  const cartao = (titulo: string) => page.locator("fieldset.rev-cartao").filter({ has: page.locator("legend", { hasText: titulo }) });
  const decisao = page.locator(".rev-grupo").filter({ hasText: "Precisa da sua decisão" }).locator("fieldset.rev-cartao");
  await expect(decisao).toHaveCount(1);
  await expect(decisao.locator("legend")).toHaveText("D01 · Descrição");
  await expect(decisao).toContainText(doProjeto);
  await expect(decisao.locator("del").first()).toBeVisible();
  await expect(decisao.locator("ins").filter({ hasText: m })).toBeVisible();
  await expect(decisao.getByRole("radio", { checked: true })).toHaveCount(0);
  const entram = page.locator("details.rev-grupo");
  await expect(entram.locator("> summary")).toHaveText("Entram da base sem conflito (1)");
  await expect(entram.locator("fieldset.rev-cartao legend")).toHaveText("D02 · Descrição");
  await expect(cartao("D02 · Descrição").getByLabel("Usar o da base")).toBeChecked();

  // 4. Manter o do projeto no conflito e concluir: o selo some, D01 fica com o projeto e D02 vem da base.
  await decisao.getByLabel("Manter o do projeto").check();
  await page.getByRole("button", { name: "Concluir revisão" }).click();
  await expect(page).toHaveURL(/\?aba=matriz$/);
  await expect(page.locator("#mensagens")).toContainText("Revisão de 5EF LP concluída: 1 mudança(s) da base aplicada(s).");
  await expect(linha5ef(page)).toContainText("cópia do projeto");
  await expect(linha5ef(page).getByText("A base mudou")).toHaveCount(0);
  await expect(linha5ef(page).getByRole("link", { name: /^Revisar mudanças da base/ })).toHaveCount(0);
  const depois = await previa(page, revista);
  expect(depois).toContain(doProjeto);
  expect(depois).toContain(soBase);
  expect(depois).not.toContain(daBase);

  // 5. Sem a pendência, a revista valida.
  await validar(page, revista);
  expect(erros).toEqual([]);
});

test("mudar a base de uma cópia validada: o modal avisa da revisão e o Impresso vê o que mudou na cópia", async ({ page, browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: impSenha } = process.env;
  test.skip(!imp || !impSenha, "defina E2E_IMPRESSO_*");
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const { matriz, revista, parceiro, projeto } = await preparar(page, "Etapa impresso");
  const m = marca();
  const [daBase, descritorNovo] = [`Base E2E ${m} um.`, `Descritor novo E2E ${m}.`];

  // 1. Cópia sem edição, "Validado" e a foto do Impresso: é contra ela que o "o que mudou" compara.
  const { aba, copia } = await criarCopia(page, parceiro, matriz.nome);
  await liberarBloqueio(page);
  await validar(page, revista);
  const impresso = await entrarComo(browser, imp!, impSenha!, `/ui/impresso/2026/?revista=${revista}`);
  impresso.on("pageerror", (e) => erros.push(e.message));
  const urlImpresso = impresso.url();
  await impresso.click("#botao-impressa");
  await expect(impresso.locator("#mensagens")).toContainText("Revista Impressa Atualizada");
  await expect(impresso.locator("#botao-impressa")).toHaveCount(0);

  // 2. Mudar D01 na matriz: nada grava antes do modal, que lista a revista e onde a mudança abre revisão.
  const daMatriz = await editorDaMatriz(page, matriz.url);
  const resposta = await descrever(page, daMatriz, "D01", daBase);
  expect(resposta.ok).toBe(false);
  const modal = page.getByRole("dialog", { name: "Salvar “Descrição” de D01 tira o “Validado” de 1 revista(s)" });
  await expect(modal).toBeVisible();
  await expect(modal.locator(".impacto-lista li")).toHaveCount(1);
  await expect(modal.locator(".impacto-lista")).toContainText(parceiro);
  await expect(modal.getByText(`Abre revisão em 1 projeto(s) com cópia desta etapa: ${projeto}.`)).toBeVisible();
  await modal.getByRole("button", { name: /e tirar Validado$/ }).click();
  await expect(salvo(page)).toBeVisible();
  await liberarBloqueio(page);

  // 3. Revisão sem conflito: a mudança da base já vem em "Usar o da base"; concluir a traz para a cópia.
  await page.goto(aba);
  await linha5ef(page).getByRole("link", { name: /^Revisar mudanças da base/ }).click();
  await expect(page.getByText("Precisa da sua decisão")).toHaveCount(0);
  await expect(page.locator("details.rev-grupo > summary")).toHaveText("Entram da base sem conflito (1)");
  await expect(page.locator("fieldset.rev-cartao").getByLabel("Usar o da base")).toBeChecked();
  await page.getByRole("button", { name: "Concluir revisão" }).click();
  await expect(page.locator("#mensagens")).toContainText("Revisão de 5EF LP concluída: 1 mudança(s) da base aplicada(s).");

  // 4. Um descritor a mais, só na cópia; a revista valida de novo.
  await page.goto(copia);
  await alpinePronto(page);
  await page.getByRole("navigation", { name: /^Descritores de/ }).getByRole("button", { name: "Novo descritor" }).click();
  const dialogo = page.locator("#dlg-novo");
  await dialogo.getByLabel("Código").fill("D99");
  await dialogo.getByLabel("Descrição").fill(descritorNovo);
  await dialogo.getByRole("button", { name: "Criar descritor" }).click();
  await expect(page.locator("#titulo-descritor")).toContainText("D99");
  await liberarBloqueio(page);
  await validar(page, revista);

  // 5. O Impresso vê, na etapa 5EF, o descritor que mudou (o que saiu e o que entrou) e o descritor novo.
  await impresso.goto(urlImpresso);
  const grupo = impresso.locator("#grupo-F1-5ef");
  await expect(grupo).toBeVisible();
  const item = (codigo: string) => grupo.locator(".impresso-item").filter({ has: impresso.getByRole("heading", { name: `5EF · ${codigo}`, exact: true }) });
  await expect(grupo.locator(".impresso-item")).toHaveCount(2); // só o que mudou: D02 e D03 ficam de fora
  await expect(item("D01").locator(".impresso-item-cab")).toContainText("alterado");
  await expect(item("D01").locator("del").filter({ hasText: "demonstração" })).toBeVisible();
  await expect(item("D01").locator("ins").filter({ hasText: m })).toBeVisible();
  await expect(item("D99").locator(".impresso-item-cab")).toContainText("novo");
  await expect(item("D99").getByRole("textbox")).toHaveValue(new RegExp(`Descritor novo E2E ${m}\\.`));
  await expect(impresso.locator("#botao-impressa")).toBeVisible();
  await impresso.context().close();
  expect(erros).toEqual([]);
});
