// Revista em páginas (sumário, F1 e um F2 por infográfico), sem servidor: fixtures/pagina/<nome>.html
// é o HTML que o Django renderiza no modo zip (test_preview.py confere os gabaritos;
// REGERAR_FIXTURES=1 regrava). page.route num host fictício serve os estáticos de nucleo/static/revista/
// (D-130) e o PNG 1×1 em arquivos/ (capa e imagens dos itens do infográfico).
import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { extname, join } from "node:path";

const APP = join(__dirname, "..", "..");
const STATIC = join(APP, "nucleo", "static");
const PAGINAS = join(__dirname, "..", "fixtures", "pagina");
const BASE = "http://pagina.teste/";
const TIPOS: Record<string, string> = { ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml" };
// PNG 1×1 para arquivos/capa.png e arquivos/infograficos/*.png
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
  "base64",
);

async function abrir(page: Page, nome = "index.html"): Promise<string[]> {
  const erros: string[] = [];
  page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
  page.on("pageerror", (e) => erros.push(e.message));
  await page.route(`${BASE}**`, (route) => {
    const caminho = new URL(route.request().url()).pathname.slice(1);
    if (extname(caminho) === ".html") return route.fulfill({ contentType: "text/html", body: readFileSync(join(PAGINAS, caminho)) });
    if (caminho.startsWith("arquivos/")) return route.fulfill({ contentType: "image/png", body: PNG });
    return route.fulfill({ contentType: TIPOS[extname(caminho)], body: readFileSync(join(STATIC, caminho)) });
  });
  await page.goto(`${BASE}${nome}`);
  return erros;
}

async function abrirF1(page: Page): Promise<string[]> {
  const erros = await abrir(page, "f1.html");
  await expect(page.locator("body.app-initialized")).toBeAttached();
  return erros;
}

async function abrirOutrasEtapas(page: Page): Promise<string[]> {
  const erros = await abrir(page, "f2-outras-etapas.html");
  await expect(page.locator("#revista.svg-tour")).toBeAttached();
  return erros;
}

test("sumário: os 3 links abrem a página certa", async ({ page }) => {
  const erros = await abrir(page);
  await expect(page).toHaveTitle("Análise de GO");
  const sumario = page.getByRole("navigation", { name: "Sumário" });
  for (const [link, titulo] of [
    ["Escalas de proficiência", "Escalas de proficiência – Análise de GO"],
    ["Avaliação e Currículo – Alfa", "Avaliação e Currículo – Alfa – Análise de GO"],
    ["Avaliação e Currículo – Outras Etapas", "Avaliação e Currículo – Outras Etapas – Análise de GO"],
  ]) {
    await sumario.getByRole("link", { name: link, exact: true }).click();
    await expect(page).toHaveTitle(titulo);
    await page.getByRole("link", { name: "Voltar ao sumário" }).click();
    await expect(page).toHaveTitle("Análise de GO");
  }
  expect(erros).toEqual([]);
});

test("F1: troca a etapa", async ({ page }) => {
  const erros = await abrirF1(page);
  const abas = page.locator(".filtro-btn");
  await expect(abas.first()).toHaveClass(/active/);
  await abas.nth(1).click();
  await expect(abas.nth(1)).toHaveClass(/active/);
  await expect(abas.nth(1)).toHaveText("9º Ano do Ensino Fundamental");
  await expect(abas.nth(1)).toHaveAttribute("aria-pressed", "true");
  await expect(abas.first()).toHaveAttribute("aria-pressed", "false");
  await expect(page.getByRole("group", { name: "Etapa de ensino" })).toBeVisible();
  expect(erros).toEqual([]);
});

test("F1: seletor de descritores devolve o foco e anuncia", async ({ page }) => {
  const erros = await abrirF1(page);
  const toggle = page.locator("#dropdownToggle");
  await toggle.click();
  await page.locator("#tagPanel .descritor-btn", { hasText: "D02" }).click();
  await expect(toggle).toBeFocused();
  await expect(page.locator("#tagPanel")).toBeHidden();
  await expect(page.locator('#tagPanel .descritor-btn[aria-current="true"]')).toHaveText("D02");
  await expect(page.locator("#anuncio")).toHaveText(/^D02: /);

  await toggle.click();
  await page.locator("#tagPanel .descritor-btn").first().focus();
  await page.keyboard.press("Escape");
  await expect(page.locator("#tagPanel")).toBeHidden();
  await expect(toggle).toBeFocused();

  // Escala: cada linha com texto diz padrão e níveis ao leitor de tela
  await expect(page.locator(".linha-conteudo p .rv-sr-only").first()).toHaveText(/^Padrão 0\d, níve/);
  await expect(page.locator(".escala-label-top")).toContainText("Máximo da escala");
  expect(erros).toEqual([]);
});

test("F2 Outras Etapas: tour completo e Anterior na visão geral", async ({ page }) => {
  const erros = await abrirOutrasEtapas(page);
  const f2 = page.locator("#revista");
  const titulo = f2.locator(".svg-tour__title");
  const principal = f2.locator(".svg-tour__actions .svg-tour__btn--primary");
  await expect(titulo).toHaveText("Avaliação & Currículo");
  for (const passo of ["Descritor", "Habilidades", "Progressão", "Tarefas"]) {
    await principal.click(); // Iniciar tour, depois Próximo
    await expect(titulo).toHaveText(passo);
  }
  await expect(principal).toHaveText("Concluir");
  await principal.click();
  await expect(titulo).toHaveText("Tour concluído");
  await principal.click(); // Recomeçar tour
  await expect(titulo).toHaveText("Descritor");
  // "Anterior" some na visão geral: o foco vai para o botão principal
  const anterior = f2.locator(".svg-tour__actions .svg-tour__btn:not(.svg-tour__btn--primary)");
  await anterior.focus();
  await page.keyboard.press("Enter");
  await expect(titulo).toHaveText("Avaliação & Currículo");
  await expect(principal).toBeFocused();
  expect(erros).toEqual([]);
});

test("F2 Outras Etapas: + das habilidades abre o dialog e Esc devolve o foco", async ({ page }) => {
  const erros = await abrirOutrasEtapas(page);
  const botao = page.locator("#f2-btn-action-habilidades");
  await expect(botao).toHaveAttribute("role", "button");
  await botao.focus(); // teclado: o clique no <g> do SVG não chega
  await page.keyboard.press("Enter");
  const dialogo = page.getByRole("dialog", { name: "Habilidades" });
  await expect(dialogo).toBeVisible();
  await expect(dialogo).toContainText("Este quadro traz as habilidades relacionadas a essa aprendizagem"); // texto_habilidades do docx
  await page.keyboard.press("Escape");
  await expect(dialogo).toBeHidden();
  await expect(botao).toBeFocused();
  expect(erros).toEqual([]);
});

test("F2 Outras Etapas: dlg-tarefa-1 mostra a imagem do item", async ({ page }) => {
  const erros = await abrirOutrasEtapas(page);
  await page.locator("#f2-btn-action-tarefa-1").focus();
  await page.keyboard.press("Enter");
  const dialogo = page.locator("#dlg-tarefa-1");
  await expect(dialogo).toBeVisible();
  const imagem = dialogo.getByRole("img", { name: "Tirinha de quatro quadrinhos" });
  await expect.poll(() => imagem.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  expect(erros).toEqual([]);
});

for (const nome of ["index", "f2-outras-etapas"]) {
  for (const largura of [1280, 390]) {
    test(`screenshot ${nome} ${largura}px`, async ({ page }) => {
      await page.setViewportSize({ width: largura, height: 900 });
      const erros = await abrir(page, `${nome}.html`);
      await page.screenshot({ path: join(__dirname, "..", "screenshots", `pagina-${nome}-${largura}.png`), fullPage: true });
      expect(erros).toEqual([]);
    });
  }
}
