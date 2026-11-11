// Passo Infográficos da ficha da revista (fase 3 do F2). Parceiro "E2E Infográfico …" próprio (D-225) com
// cortes de 2EF e 5EF LP: a cascata cria os 2 cartões (Alfa e Outras Etapas). O Alfa fica no mínimo (3 passos
// desligados e a habilidade); o Outras Etapas é preenchido inteiro (textos, grade, 4 itens com imagem). A
// prévia mostra o tour e a imagem da tarefa 1; desligar "Progressão" tira o bloco da prévia.
// A matriz Demonstração não tem 2EF: a Situação fica em 5 de 6, só com essa pendência (o 6 de 6 está no
// revistaPropria). Preparo de painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e); o limpar.ts
// apaga tudo no fim (D-224).
import { expect, test } from "@playwright/test";
import { CAPA, alpinePronto, entrar, fichaComTemplates, infograficoMinimo, liberarBloqueio, preencher, salvarInfografico } from "./helpers";

const QUINTO = "5º ano do Ensino Fundamental";
// Títulos dos passos no template "Padrão (F2)" de LP (carregar_templates).
const [DESCRITOR, HABILIDADES, PROGRESSAO, TAREFAS] = [
  "Descritor", "Descrição das habilidades no referencial curricular", "Progressão da habilidade", "Tarefas por nível de complexidade",
];

test("infográficos: 2 cartões, Outras Etapas inteiro, prévia com tour e imagem, desligar Progressão", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const salvar = (acao: () => Promise<unknown>) => salvarInfografico(page, acao);

  await entrar(page);
  const { revista } = await fichaComTemplates(page, "Infográfico", ["2EF LP", "5EF LP"]);
  const cartoes = page.locator(".inf-card");
  await expect(cartoes.locator("h3")).toHaveText(["Avaliação e Currículo – Alfa", "Avaliação e Currículo – Outras Etapas"]);
  const outras = cartoes.nth(1);

  // 1. Alfa no mínimo.
  await infograficoMinimo(page, cartoes.nth(0));

  // 2. Outras Etapas inteiro: habilidade e os 3 textos, a grade (2 marcas, código e texto) e os 4 itens.
  for (const [rotulo, valor] of [
    ["Habilidade destacada", "Habilidade E2E das outras etapas."],
    ["Texto do clique ❶ (descritor)", "Descritor E2E."],
    ["Texto do clique ❷ (habilidades)", "Habilidades E2E."],
    ["Texto do clique ❸ (progressão)", "Progressão E2E."],
  ]) {
    await salvar(() => preencher(outras.getByLabel(rotulo, { exact: true }), valor));
  }
  await salvar(() => outras.getByLabel(`Marca: ${QUINTO}`).selectOption("I"));
  await salvar(() => outras.getByLabel("Marca: 9º ano do Ensino Fundamental").selectOption("C"));
  await salvar(() => preencher(outras.getByLabel(`Código: ${QUINTO}`), "EF05LP01"));
  await salvar(() => preencher(outras.getByLabel(`Texto: ${QUINTO}`), "Texto E2E do 5º ano."));
  for (const n of [1, 2, 3, 4]) {
    const tarefa = outras.getByRole("group", { name: `Tarefa ${n}`, exact: true });
    await salvar(() => tarefa.locator("input[type=file]").setInputFiles({ ...CAPA, name: `item-${n}.png` }));
    await expect(tarefa.locator("img.inf-miniatura")).toBeVisible(); // a imagem troca o passo inteiro
    await salvar(() => tarefa.getByLabel("Etapa", { exact: true }).selectOption("5EF"));
    await salvar(() => preencher(tarefa.getByLabel("Descritor", { exact: true }), `D0${n}`));
  }
  const tarefa1 = outras.getByRole("group", { name: "Tarefa 1", exact: true });
  await salvar(() => preencher(tarefa1.getByLabel("Texto alternativo"), "Imagem E2E da tarefa 1"));

  // 3. Capa: só a matriz (sem 2EF) fica pendente.
  await page.setInputFiles("#arquivo-capa", CAPA);
  await expect(page.locator("#arquivos img.revista-capa")).toBeVisible();
  const situacao = page.locator("#situacao");
  await expect(situacao).toContainText("5 de 6 prontos");
  await expect(situacao.locator(".revista-checklist > li", { hasText: "Infográficos" })).toHaveAttribute("data-ok", "");
  await expect(situacao.locator(".revista-checklist li li")).toHaveText(["A matriz não tem a etapa: 2EF."]);
  const previa = `/preview/${revista}/f2/outras/`;
  await expect(outras.getByRole("link", { name: /Abrir prévia/ })).toHaveAttribute("href", previa);
  await liberarBloqueio(page);

  // 4. Prévia: o tour passa pelos 4 passos; o + da tarefa 1 abre o dialog com a imagem.
  await page.goto(previa);
  const f2 = page.locator("#revista");
  await expect(f2).toHaveClass(/svg-tour/);
  const titulo = f2.locator(".svg-tour__title");
  const principal = f2.locator(".svg-tour__actions .svg-tour__btn--primary");
  for (const passo of [DESCRITOR, HABILIDADES, PROGRESSAO, TAREFAS]) {
    await principal.click(); // Iniciar tour, depois Próximo
    await expect(titulo).toHaveText(passo);
  }
  await expect(page.locator("#f2-progressao")).toHaveCount(1);
  await page.reload(); // o dialog abre da visão geral (o tour acima terminou em Tarefas)
  await page.locator("#f2-btn-action-tarefa-1").focus(); // teclado: o clique no <g> do SVG não chega
  await page.keyboard.press("Enter");
  const dialogo = page.locator("#dlg-tarefa-1");
  await expect(dialogo).toBeVisible();
  const imagem = dialogo.getByRole("img", { name: "Imagem E2E da tarefa 1" });
  await expect.poll(() => imagem.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  await page.keyboard.press("Escape");
  await expect(dialogo).toBeHidden();

  // 5. Desligar "Progressão" na ficha: o bloco e o passo saem da prévia.
  await page.goto(`/ui/revista/2026/${revista}/`);
  await alpinePronto(page);
  await salvar(() => outras.getByLabel("Progressão", { exact: true }).uncheck());
  await expect(situacao).toContainText("5 de 6 prontos");
  await liberarBloqueio(page);
  await page.goto(previa);
  await expect(f2).toHaveClass(/svg-tour/);
  await expect(page.locator("#f2-habilidades")).toHaveCount(1);
  await expect(page.locator("#f2-progressao")).toHaveCount(0);
  for (const passo of [DESCRITOR, HABILIDADES, TAREFAS]) {
    await principal.click();
    await expect(titulo).toHaveText(passo);
  }
  expect(erros).toEqual([]);
});
