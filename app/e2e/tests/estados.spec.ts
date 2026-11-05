// Estados dos controles (U10b): a linha nova entra com a animação `entra` (120 ms, --ease-saida), cada
// estado do status do autosave entra com transição de 180 ms, e o campo em envio fica aria-busy com o
// girando no status. Preparo de painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e).
// Grava só no projeto que o teste cria (parceiroComProjeto, D-225); o limpar.ts apaga no fim (D-224).
import { expect, test, type Page } from "@playwright/test";
import { alpinePronto, entrar, parceiroComProjeto, regional } from "./helpers";

const ROTA = "**/ui/projeto/*/campo/";
const estilo = (page: Page, seletor: string, props: string[]) =>
  page.locator(seletor).first().evaluate((e, ps) => Object.fromEntries(ps.map((p) => [p, getComputedStyle(e).getPropertyValue(p)])), props);

test("linha nova entra com a animação entra de 120 ms e o status troca com transição de 180 ms", async ({ page }) => {
  await entrar(page, "/ui/anos/2026/");
  await alpinePronto(page);
  expect(await estilo(page, "[data-status-salvo] > span", ["transition-duration", "transition-property"])).toEqual({
    "transition-duration": "0.18s", "transition-property": "opacity",
  });

  await page.getByRole("button", { name: "Adicionar etapa" }).click();
  const linha = "#etapas-form [data-linha-nova]";
  await expect(page.locator(linha)).toHaveCount(1);
  expect(await estilo(page, linha, ["animation-name", "animation-duration", "animation-timing-function"])).toEqual({
    "animation-name": "entra", "animation-duration": "0.12s", "animation-timing-function": "cubic-bezier(0.16, 1, 0.3, 1)",
  });
  await page.keyboard.press("Escape");
  await expect(page.locator(linha)).toHaveCount(0);
});

test("campo em envio fica aria-busy e o status mostra Salvando… com o girando", async ({ page }) => {
  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  const nome = await parceiroComProjeto(page, "Ocupado");
  await page.goto("/ui/projeto/ano/2026/variaveis/");
  await alpinePronto(page);
  const campo = regional(page, nome);
  const status = page.locator("[data-status-salvo]");

  let soltar = () => {};
  const segura = new Promise<void>((r) => (soltar = r));
  await page.route(ROTA, async (r) => {
    await segura;
    await r.continue();
  });
  await campo.fill("Regional ocupada");
  await page.keyboard.press("Tab");
  await expect(campo).toHaveAttribute("aria-busy", "true");
  await expect(campo).toHaveCSS("cursor", "progress");
  const salvando = status.locator("span", { has: page.locator(".girando") }); // o texto do erro também guarda "Salvando…", escondido
  await expect(salvando).toBeVisible();
  await expect(salvando).toHaveText("Salvando…");
  await expect(status.locator(".girando")).toHaveCSS("opacity", "1");

  soltar();
  await expect(status.getByText(/Salvo às \d\d:\d\d/)).toBeVisible(); // projeto novo: sem revista validada, sem modal
  await expect(campo).not.toHaveAttribute("aria-busy");
  await page.unroute(ROTA);
});
