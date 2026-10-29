// Página única F1 + F2 (S08), sem servidor: fixtures/pagina.html é o HTML que o Django
// renderiza no modo zip (test_preview.py confere o gabarito; REGERAR_FIXTURES=1 regrava).
// page.route num host fictício serve os estáticos de nucleo/static/revista/ (D-130).
import { expect, test, type Page } from "@playwright/test";
import { readFileSync } from "node:fs";
import { extname, join } from "node:path";

const APP = join(__dirname, "..", "..");
const STATIC = join(APP, "nucleo", "static");
const HTML = readFileSync(join(__dirname, "..", "fixtures", "pagina.html"), "utf8");
const BASE = "http://pagina.teste/";
const TIPOS: Record<string, string> = { ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml" };
// PNG 1×1 para arquivos/capa.png
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
  "base64",
);

async function abrir(page: Page): Promise<string[]> {
  const erros: string[] = [];
  page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
  page.on("pageerror", (e) => erros.push(e.message));
  await page.route(`${BASE}**`, (route) => {
    const caminho = new URL(route.request().url()).pathname.slice(1);
    if (caminho === "index.html") return route.fulfill({ contentType: "text/html", body: HTML });
    if (caminho === "arquivos/capa.png") return route.fulfill({ contentType: "image/png", body: PNG });
    return route.fulfill({ contentType: TIPOS[extname(caminho)], body: readFileSync(join(STATIC, caminho)) });
  });
  await page.goto(`${BASE}index.html`);
  await expect(page.locator("body.app-initialized")).toBeAttached();
  await expect(page.locator("#revista.svg-tour")).toBeAttached();
  return erros;
}

test("F1: troca a etapa", async ({ page }) => {
  const erros = await abrir(page);
  const abas = page.locator(".filtro-btn");
  await expect(abas.first()).toHaveClass(/active/);
  await abas.nth(1).click();
  await expect(abas.nth(1)).toHaveClass(/active/);
  await expect(abas.nth(1)).toHaveText("9º Ano do Ensino Fundamental");
  expect(erros).toEqual([]);
});

test("F2: menu de capítulos, tour completo e dlg-p2", async ({ page }) => {
  const erros = await abrir(page);
  await page.getByRole("navigation", { name: "Capítulos" }).getByRole("link", { name: "Infográfico" }).click();
  await expect(page).toHaveURL(/#f2$/);

  const f2 = page.locator("#revista");
  await expect(f2.locator(".svg-tour__title")).toHaveText("Avaliação & Currículo");
  const principal = f2.locator(".svg-tour__actions .svg-tour__btn--primary");
  await principal.click(); // Iniciar tour
  await expect(f2.locator(".svg-tour__title")).toHaveText("Descritor");
  await principal.click();
  await expect(f2.locator(".svg-tour__title")).toHaveText("Itens");
  await expect(principal).toHaveText("Concluir");
  await principal.click();
  await expect(f2.locator(".svg-tour__title")).toHaveText("Tour concluído");

  // Botão do SVG (prefixo f2-) abre o <dialog> da seção dlg-p2, com título e foco dentro
  const botao = page.locator("#f2-btn-action-p2");
  await expect(botao).toHaveAttribute("role", "button");
  await botao.focus();
  await page.keyboard.press("Enter");
  const dialogo = page.getByRole("dialog", { name: "Itens por ano" });
  await expect(dialogo).toBeVisible();
  await expect(dialogo).toContainText("Detalhe do item.");
  await page.keyboard.press("Escape");
  await expect(dialogo).toBeHidden();
  await expect(botao).toBeFocused(); // foco volta ao botão
  expect(erros).toEqual([]);
});

test("Ctrl+→ dentro do F2 não muda o descritor do F1", async ({ page }) => {
  const erros = await abrir(page);
  const badge = page.locator(".descritor-badge");
  await expect(badge).toHaveText("D01");

  await page.locator("#revista").focus();
  await page.keyboard.press("Control+ArrowRight");
  await expect(badge).toHaveText("D01");

  // Controle: fora do F2 o atalho continua valendo
  await page.locator("#filtro .filtro-btn").first().focus();
  await page.keyboard.press("Control+ArrowRight");
  await expect(badge).toHaveText("D02");
  expect(erros).toEqual([]);
});

for (const largura of [1280, 390]) {
  test(`screenshot ${largura}px`, async ({ page }) => {
    await page.setViewportSize({ width: largura, height: 900 });
    const erros = await abrir(page);
    await page.screenshot({ path: join(__dirname, "..", "screenshots", `pagina-${largura}.png`), fullPage: true });
    expect(erros).toEqual([]);
  });
}
