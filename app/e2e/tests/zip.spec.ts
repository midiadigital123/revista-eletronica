// Zip da revista (S15) aberto por file://, sem servidor. fixtures/revista.zip é o zip que o
// Django gera (test_empacotar confere o conteúdo; REGERAR_FIXTURES=1 regrava). O teste o
// extrai num diretório temporário e percorre as páginas a partir do index.html (sumário).
import { expect, test } from "@playwright/test";
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

test("file://: sumário → F1 com o item → sumário → Outras Etapas com a imagem da tarefa", async ({ page }) => {
  const erros: string[] = [];
  page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
  page.on("pageerror", (e) => erros.push(e.message));
  page.on("requestfailed", (r) => erros.push(`falhou: ${r.url()}`));
  const largura = (img: HTMLImageElement) => img.naturalWidth;
  await page.goto(pathToFileURL(join(pasta, "index.html")).href);
  await expect.poll(() => page.locator(".hero-image img").evaluate(largura)).toBeGreaterThan(0); // capa
  const sumario = page.getByRole("navigation", { name: "Sumário" });

  // F1: a escala e o "Ver item" com arquivos/itens/item1.png
  await sumario.getByRole("link", { name: "Escalas de proficiência" }).click();
  await expect(page.locator("body.app-initialized")).toBeAttached();
  await expect(page.locator(".escala-barra")).toHaveCount(5); // 4 cortes = 5 padrões
  await expect(page.locator(".descritor-badge")).toHaveText("D01");
  await page.locator(".ver-item-btn").first().click();
  const item = page.locator("#itemModalImagem");
  await expect(item).toBeVisible();
  await expect(item).toHaveAttribute("src", "arquivos/itens/item1.png");
  await expect.poll(() => item.evaluate(largura)).toBeGreaterThan(0);
  await page.locator("#itemModalClose").click();

  // F2 Outras Etapas: tour até Tarefas e dlg-tarefa-1 com a imagem
  await page.getByRole("link", { name: "Voltar ao sumário" }).click();
  await sumario.getByRole("link", { name: "Avaliação e Currículo – Outras Etapas" }).click();
  const f2 = page.locator("#revista");
  await expect(f2).toHaveClass(/svg-tour/);
  const principal = f2.locator(".svg-tour__actions .svg-tour__btn--primary");
  for (const passo of ["Descritor", "Habilidades", "Progressão", "Tarefas"]) {
    await principal.click();
    await expect(f2.locator(".svg-tour__title")).toHaveText(passo);
  }
  await page.locator("#f2-btn-action-tarefa-1").focus(); // teclado, como no pagina.spec (o clique no <g> não chega)
  await page.keyboard.press("Enter");
  const tarefa = page.locator("#dlg-tarefa-1");
  await expect(tarefa).toBeVisible();
  await expect.poll(() => tarefa.getByRole("img", { name: "Tirinha de quatro quadrinhos" }).evaluate(largura)).toBeGreaterThan(0);
  expect(erros).toEqual([]);
});
