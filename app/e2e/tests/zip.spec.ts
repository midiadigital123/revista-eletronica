// Zip da revista (S15) aberto por file://, sem servidor. fixtures/revista.zip é o zip que o
// Django gera (test_empacotar confere o conteúdo; REGERAR_FIXTURES=1 regrava). O teste o
// extrai num diretório temporário e abre index.html direto do disco.
import { expect, test, type Page } from "@playwright/test";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";
import { inflateRawSync } from "node:zlib";

let pasta: string;

/** Extrai um zip simples (sem zip64) pelo diretório central: só stored e deflate. */
function extrair(zip: Buffer, destino: string) {
  const fim = zip.lastIndexOf(Buffer.from([0x50, 0x4b, 0x05, 0x06]));
  let p = zip.readUInt32LE(fim + 16);
  for (let n = zip.readUInt16LE(fim + 10); n > 0; n--) {
    const [nomeLen, extraLen, comentLen] = [28, 30, 32].map((o) => zip.readUInt16LE(p + o));
    const nome = zip.toString("utf8", p + 46, p + 46 + nomeLen);
    const local = zip.readUInt32LE(p + 42);
    const inicio = local + 30 + zip.readUInt16LE(local + 26) + zip.readUInt16LE(local + 28);
    const bruto = zip.subarray(inicio, inicio + zip.readUInt32LE(p + 20));
    mkdirSync(dirname(join(destino, nome)), { recursive: true });
    writeFileSync(join(destino, nome), zip.readUInt16LE(p + 10) === 8 ? inflateRawSync(bruto) : bruto);
    p += 46 + nomeLen + extraLen + comentLen;
  }
}

test.beforeAll(() => {
  pasta = mkdtempSync(join(tmpdir(), "revista-zip-"));
  extrair(readFileSync(join(__dirname, "..", "fixtures", "revista.zip")), pasta);
});
test.afterAll(() => rmSync(pasta, { recursive: true, force: true }));

async function abrir(page: Page): Promise<string[]> {
  const erros: string[] = [];
  page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
  page.on("pageerror", (e) => erros.push(e.message));
  page.on("requestfailed", (r) => erros.push(`falhou: ${r.url()}`));
  await page.goto(pathToFileURL(join(pasta, "index.html")).href);
  await expect(page.locator("body.app-initialized")).toBeAttached();
  return erros;
}

test("F1: file:// renderiza a escala", async ({ page }) => {
  const erros = await abrir(page);
  await expect(page.locator(".escala-barra")).toHaveCount(5); // 4 cortes = 5 padrões
  await expect(page.locator(".descritor-badge")).toHaveText("D01");
  await expect(page.locator(".escala-content > *").first()).toBeVisible();
  await expect(page.locator(".hero-image img")).toHaveJSProperty("complete", true);
  expect(await page.locator(".hero-image img").evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  expect(erros).toEqual([]);
});

test("F1: file:// abre o item da tarefa (arquivos/itens/item1.png)", async ({ page }) => {
  const erros = await abrir(page);
  await page.locator(".ver-item-btn").first().click();
  const imagem = page.locator("#itemModalImagem");
  await expect(imagem).toBeVisible();
  await expect(imagem).toHaveAttribute("src", "arquivos/itens/item1.png");
  await expect.poll(() => imagem.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);
  expect(erros).toEqual([]);
});

test("F2: file:// abre o tour e o dlg-p2", async ({ page }) => {
  const erros = await abrir(page);
  const f2 = page.locator("#revista");
  await expect(f2).toHaveClass(/svg-tour/);
  await page.getByRole("navigation", { name: "Capítulos" }).getByRole("link", { name: "Infográfico" }).click();
  await expect(f2.locator(".svg-tour__title")).toHaveText("Avaliação & Currículo");
  await f2.locator(".svg-tour__actions .svg-tour__btn--primary").click(); // Iniciar tour
  await expect(f2.locator(".svg-tour__title")).toHaveText("Descritor");

  await page.locator("#f2-btn-action-p2").focus(); // teclado, como no pagina.spec (o clique no <g> não chega)
  await page.keyboard.press("Enter");
  const dialogo = page.getByRole("dialog", { name: "Itens por ano" });
  await expect(dialogo).toBeVisible();
  await expect(dialogo).toContainText("Detalhe do item.");
  expect(erros).toEqual([]);
});
