// Linha nova por botão, ordem automática e reordenar (U4). Preparo de painel.spec.ts (criar_demo
// --ano 2026 e o superusuário e2e). Grava: o componente criado fica no banco (como em anos.spec);
// a ordem das tarefas e dos descritores da MEC volta à original no fim de cada teste.
import { expect, test, type Page } from "@playwright/test";
import { entrar, liberarBloqueio } from "./helpers";

const ETAPA = /^\s*(\d+)\s*(EF|EM)\s*$/i;
const escolar = (a: string, b: string) => {
  const chave = (c: string) => {
    const m = ETAPA.exec(c);
    return m ? [["EF", "EM"].indexOf(m[2].toUpperCase()), Number(m[1])] : [2, 0];
  };
  const [x, y] = [chave(a), chave(b)];
  return x[0] - y[0] || x[1] - y[1] || a.localeCompare(b);
};

const reordenou = (page: Page) => page.waitForResponse((r) => r.url().endsWith("/reordenar/") && r.status() === 200);

test("ano: + Adicionar abre a linha com foco; Esc descarta; Enter grava; etapas na ordem escolar", async ({ page }) => {
  await entrar(page, "/ui/anos/2026/");
  const etapas = page.locator("#etapas-form");
  const codigos = (await etapas.locator("tbody input[name$='-codigo']").evaluateAll((l) => l.map((i) => (i as HTMLInputElement).value)));
  expect(codigos).toEqual([...codigos].sort(escolar));
  await expect(page.getByText("Preencha a última linha")).toHaveCount(0);
  await expect(etapas.getByLabel("Código (linha nova)")).toHaveCount(0); // sem linha vazia

  const adicionar = page.getByRole("button", { name: "Adicionar etapa" });
  await adicionar.click();
  await expect(etapas.getByLabel("Código (linha nova)")).toBeFocused();
  await expect(page.locator("#id_etapas-TOTAL_FORMS")).toHaveValue(String(codigos.length + 1));
  await page.keyboard.type("1EM");
  await page.keyboard.press("Escape");
  await expect(etapas.getByLabel("Código (linha nova)")).toHaveCount(0);
  await expect(page.locator("#id_etapas-TOTAL_FORMS")).toHaveValue(String(codigos.length));
  await expect(adicionar).toBeFocused();

  const codigo = `Z${Date.now().toString().slice(-5)}`;
  await page.getByRole("button", { name: "Adicionar componente" }).click();
  await expect(page.getByLabel("Código (linha nova)")).toBeFocused();
  await page.keyboard.type(codigo);
  await page.keyboard.press("Tab");
  await page.keyboard.type(`Componente E2E ${codigo}`);
  await page.keyboard.press("Enter");
  await expect(page.getByText("Componentes de 2026 salvos.")).toBeVisible();
  await expect(page.getByLabel(`Código (${codigo})`)).toHaveValue(codigo);
});

test("cortes: + Adicionar parceiro abaixo da grade abre a linha; Esc descarta", async ({ page }) => {
  await entrar(page, "/cortes/2026/");
  await expect(page.locator("#novo-parceiro")).toHaveCount(0);
  const adicionar = page.getByRole("button", { name: "Adicionar parceiro" });
  const [grade, botao] = await Promise.all([page.locator("#grade .grade-caixa").boundingBox(), adicionar.boundingBox()]);
  expect(botao!.y).toBeGreaterThan(grade!.y + grade!.height - 1); // logo abaixo da caixa (rolável) da grade
  await adicionar.click();
  await expect(page.locator("#novo-parceiro")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.locator("#novo-parceiro")).toHaveCount(0);
  await expect(adicionar).toBeFocused();
});

test("MEC: arrastar e os botões trocam a ordem das tarefas e dos descritores; + Adicionar tarefa", async ({ page }) => {
  await entrar(page, "/ui/matriz/2026/");
  await page.getByRole("link", { name: "Demonstração" }).first().click();
  await page.locator('a[href*="/ui/matriz/mec/"]').first().click();
  await expect(page.locator("#form-descritor")).toBeVisible();
  const ordem = (sel: string) => page.locator(`${sel} > [data-id]`).evaluateAll((l) => l.map((e) => (e as HTMLElement).dataset.id));

  // Tarefa nova: só pelo botão, com foco no Início; Esc descarta.
  await expect(page.getByText("Tarefa nova")).toHaveCount(0);
  await page.getByRole("button", { name: "Adicionar tarefa" }).click();
  await expect(page.locator("[data-linha-nova] [name$='-inicio']")).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(page.locator("[data-linha-nova]")).toHaveCount(0);

  // Arrastar a 1ª tarefa para o lugar da 2ª grava a ordem nova.
  const tarefas = "#tarefas-lista";
  const antes = await ordem(tarefas);
  expect(antes.length).toBeGreaterThan(1);
  const salvou = reordenou(page);
  await page.locator(`${tarefas} > [data-id] .alca`).first().dragTo(page.locator(`${tarefas} > [data-id]`).nth(1), { targetPosition: { x: 20, y: 60 } });
  await salvou;
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às/)).toBeVisible();
  const depois = await ordem(tarefas);
  expect(depois).not.toEqual(antes);
  await page.reload();
  expect(await ordem(tarefas)).toEqual(depois);

  // Teclado: "Mover para cima" devolve a tarefa ao 1º lugar.
  const movida = page.locator(`${tarefas} > [data-id="${antes[0]}"] [data-mover="-1"]`);
  for (let i = depois.indexOf(antes[0]); i > 0; i--) {
    const ok = reordenou(page);
    await movida.focus();
    await page.keyboard.press("Enter");
    await ok;
  }
  await expect(movida).toBeFocused();
  expect(await ordem(tarefas)).toEqual(antes);

  // Descritores (lista da MEC): para baixo e de volta, pelo teclado.
  const lista = "#lista-ordem";
  const descritores = await ordem(lista);
  if (descritores.length > 1) {
    const primeiro = page.locator(`${lista} > [data-id="${descritores[0]}"]`);
    let ok = reordenou(page);
    await primeiro.locator('[data-mover="1"]').focus();
    await page.keyboard.press("Enter");
    await ok;
    expect((await ordem(lista))[1]).toBe(descritores[0]);
    ok = reordenou(page);
    await primeiro.locator('[data-mover="-1"]').focus();
    await page.keyboard.press("Enter");
    await ok;
  }
  await page.reload();
  expect(await ordem(tarefas)).toEqual(antes);
  expect(await ordem(lista)).toEqual(descritores);
  await liberarBloqueio(page);
});
