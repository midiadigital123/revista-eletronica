// Revista F1 (JS/CSS portados) com os fixtures de 1, 3 e 4 cortes, sem servidor:
// as páginas saem de disco via page.route num host fictício (não usa a porta 8000).
import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { extname, join } from "node:path";

const APP = join(__dirname, "..", "..");
const F1 = join(APP, "nucleo", "static", "revista", "f1");
const HTML = readFileSync(join(__dirname, "..", "fixtures", "f1.html"), "utf8");
const BASE = "http://f1.teste/";
const TIPOS: Record<string, string> = { ".js": "text/javascript", ".css": "text/css", ".svg": "image/svg+xml" };

// Paleta global (D-064): com n padrões usam-se as cores 1..n; 5º provisório #FFF
const PALETA = ["#f72628", "#ff8d43", "#b3ccff", "#0ed3ff", "#ffffff"];

type Ano = { cortes: Record<string, number>; padroes: { chave: string; rotulo: string }[] };

/** Mesmo que o escala.hbs: abas por etapa, uma variável CSS por padrão e o JSON seguro. */
function pagina(revista: Record<string, unknown>, n: number, comCores: boolean): string {
  const anos = Object.keys(revista).filter((k) => k !== "pagina");
  const abas = anos
    .map((a, i) => `<button class="filtro-btn tab${i ? "" : " active"}" data-filter="${a}" role="tab">${a}</button>`)
    .join("");
  const cores = comCores
    ? `:root{${PALETA.slice(0, n)
        .map((c, i) => {
          const [r, g, b] = [1, 3, 5].map((j) => parseInt(c.slice(j, j + 2), 16));
          return `--color-padrao-${i + 1}:${c};--color-padrao-${i + 1}-bg:rgba(${r}, ${g}, ${b}, 0.1);`;
        })
        .join("")}}`
    : "";
  const dados = JSON.stringify(revista).replaceAll("<", "\\u003c");
  return HTML.replace("__ABAS__", abas).replace("__CORES__", cores).replace("__DADOS__", () => dados);
}

const CASOS = [
  { fixture: "revista-1corte.json", padroes: 2, comCores: true },
  { fixture: "revista-3cortes.json", padroes: 4, comCores: true },
  { fixture: "revista-4cortes.json", padroes: 5, comCores: true },
  { fixture: "revista-4cortes.json", padroes: 5, comCores: false }, // cor do 5º vinda só do styles.css
];

for (const { fixture, padroes, comCores } of CASOS) {
  test(`f1 ${fixture}${comCores ? "" : " (cores do CSS)"}`, async ({ page }) => {
    const revista = JSON.parse(readFileSync(join(APP, "nucleo", "tests", "fixtures", fixture), "utf8"));
    const anos = Object.keys(revista).filter((k) => k !== "pagina");
    const primeiro: Ano = revista[anos[0]];
    expect(primeiro.padroes).toHaveLength(padroes);

    const erros: string[] = [];
    page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
    page.on("pageerror", (e) => erros.push(e.message));

    await page.route(`${BASE}**`, (route) => {
      const caminho = new URL(route.request().url()).pathname.slice(1);
      if (caminho === "index.html")
        return route.fulfill({ contentType: "text/html", body: pagina(revista, padroes, comCores) });
      return route.fulfill({ contentType: TIPOS[extname(caminho)], body: readFileSync(join(F1, caminho)) });
    });
    await page.goto(`${BASE}index.html`);
    await expect(page.locator("body.app-initialized")).toBeAttached();

    // Abas de etapa: uma por ano, a primeira ativa com o rótulo longo
    const abas = page.locator(".filtro-btn");
    await expect(abas).toHaveCount(anos.length);
    await expect(abas.first()).toHaveClass(/active/);
    await expect(abas.first()).toHaveText("5º Ano do Ensino Fundamental");
    await abas.nth(1).click();
    await expect(abas.nth(1)).toHaveClass(/active/);
    await expect(abas.nth(1)).toHaveText("9º Ano do Ensino Fundamental");

    // Régua: uma barra e um rótulo por padrão, rótulos do JSON (de cima para baixo)
    await expect(page.locator(".escala-barra")).toHaveCount(padroes);
    await expect(page.locator(".padrao-label > span")).toHaveText(
      [...primeiro.padroes].reverse().map((p) => p.rotulo),
    );

    if (padroes === 5)
      await expect(page.locator(".escala-barra.padrao-5")).toHaveCSS("background-color", "rgb(255, 255, 255)");

    expect(erros).toEqual([]);
  });
}
