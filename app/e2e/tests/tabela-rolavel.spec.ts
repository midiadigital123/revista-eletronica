// Tabela rolável (U10a): invólucro .tabela-rolavel (componente Alpine tabelaRolavel) com cabeçalho e
// 1ª coluna fixos e sombra de borda ligada a data-rolou-esq / data-rolou-dir. Precisa da demo de 2026.
import { expect, test, type Locator, type Page } from "@playwright/test";
import { entrar } from "./helpers";

const rolar = (caixa: Locator, x: number | "fim", y = 0) =>
  caixa.evaluate((c, [x, y]) => { c.scrollTo(x === "fim" ? c.scrollWidth : (x as number), y as number); }, [x, y] as const);
const xDe = async (l: Locator) => (await l.boundingBox())!.x;

async function conferir(page: Page, url: string, form: string) {
  await entrar(page, url);
  await page.setViewportSize({ width: 1024, height: 700 });
  await page.goto(url);
  const caixa = page.locator(`${form} .tabela-rolavel`);
  const fixa = caixa.locator("tbody th").first();

  // Início: tem mais à direita, nada escondido à esquerda.
  expect(await caixa.evaluate((c) => c.scrollWidth > c.clientWidth)).toBe(true);
  await expect(caixa).toHaveAttribute("data-rolou-dir", "");
  await expect(caixa).not.toHaveAttribute("data-rolou-esq");

  // Rolar de lado: a 1ª coluna fica no mesmo x e a borda esquerda ganha a sombra.
  const x0 = await xDe(fixa);
  await rolar(caixa, 200);
  await expect(caixa).toHaveAttribute("data-rolou-esq", "");
  expect(await xDe(fixa)).toBeCloseTo(x0, 0);

  // No fim: a sombra da direita some.
  await rolar(caixa, "fim");
  await expect(caixa).not.toHaveAttribute("data-rolou-dir");
  await expect(caixa).toHaveAttribute("data-rolou-esq", "");
  expect(await xDe(fixa)).toBeCloseTo(x0, 0);

  // De volta ao início: a sombra da esquerda some.
  await rolar(caixa, 0);
  await expect(caixa).not.toHaveAttribute("data-rolou-esq");
  await expect(caixa).toHaveAttribute("data-rolou-dir", "");

  // Rolar na vertical (caixa baixa de propósito: a demo tem poucas linhas): o thead fica no topo.
  await caixa.evaluate((c) => { c.style.maxHeight = "7rem"; });
  const topo = await caixa.evaluate((c) => c.getBoundingClientRect().top + c.clientTop);
  await rolar(caixa, 0, 30);
  expect(await caixa.evaluate((c) => c.scrollTop)).toBeGreaterThan(0);
  const th = caixa.locator("thead th").first();
  expect((await th.boundingBox())!.y).toBeCloseTo(topo, 0);
}

test("tabela rolável: grade de Cortes", async ({ page }) => {
  await conferir(page, "/ui/projeto/ano/2026/cortes/", "#grade");
});

test("tabela rolável: planilha de Variáveis", async ({ page }) => {
  await conferir(page, "/ui/projeto/ano/2026/variaveis/", "#variaveis-form");
});

test("tabela rolável: sem rolagem não liga nada; o redimensionamento religa", async ({ page }) => {
  await entrar(page, "/ui/anos/2026/");
  await page.setViewportSize({ width: 390, height: 800 });
  await page.goto("/ui/anos/2026/");
  const caixa = page.locator("#padroes .tabela-rolavel");
  await expect(caixa).toHaveAttribute("data-rolou-dir", "");
  await page.setViewportSize({ width: 1440, height: 800 });
  await expect(caixa).not.toHaveAttribute("data-rolou-dir");
  await expect(caixa).not.toHaveAttribute("data-rolou-esq");
});

test("tabela rolável: a página não rola de lado em 1440, 1024, 768 e 390px", async ({ page }) => {
  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  const telas = ["/ui/projeto/ano/2026/cortes/", "/ui/projeto/ano/2026/variaveis/", "/painel/2026/",
    "/ui/projeto/ano/2026/", "/ui/anos/2026/"];
  for (const largura of [1440, 1024, 768, 390]) {
    await page.setViewportSize({ width: largura, height: 800 });
    for (const url of telas) {
      await page.goto(url);
      await expect(page.locator(".tabela-rolavel").first()).toBeVisible();
      const sobra = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(sobra, `${url} em ${largura}px`).toBeLessThanOrEqual(0);
    }
  }
});
