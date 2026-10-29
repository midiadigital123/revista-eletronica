// Revista F1 (JS/CSS portados) com os fixtures de 1, 3 e 4 cortes, sem servidor:
// as páginas saem de disco via page.route num host fictício (não usa a porta 8000).
import { expect, test, type Page } from "@playwright/test";
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
type Revista = Record<string, any>;

const fixture = (nome: string): Revista =>
  JSON.parse(readFileSync(join(APP, "nucleo", "tests", "fixtures", nome), "utf8"));
const etapas = (revista: Revista) => Object.keys(revista).filter((k) => k !== "pagina");

/** Mesmo que o escala.hbs: abas por etapa, uma variável CSS por padrão e o JSON seguro. */
function pagina(revista: Revista, comCores: boolean): string {
  const anos = etapas(revista);
  const n = Math.max(...anos.map((a) => (revista[a].padroes?.length ?? 0)), 1);
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

/** Abre a revista e devolve os erros do console/página (coletados até o fim do teste). */
async function abrir(page: Page, revista: Revista, comCores = true): Promise<string[]> {
  const erros: string[] = [];
  page.on("console", (m) => m.type() === "error" && erros.push(m.text()));
  page.on("pageerror", (e) => erros.push(e.message));
  await page.route(`${BASE}**`, (route) => {
    const caminho = new URL(route.request().url()).pathname.slice(1);
    if (caminho === "index.html")
      return route.fulfill({ contentType: "text/html", body: pagina(revista, comCores) });
    return route.fulfill({ contentType: TIPOS[extname(caminho)], body: readFileSync(join(F1, caminho)) });
  });
  await page.goto(`${BASE}index.html`);
  await expect(page.locator("body.app-initialized")).toBeAttached();
  return erros;
}

/** Régua da etapa ativa: uma barra e um rótulo por padrão, rótulos do JSON (de cima para baixo). */
async function conferirRegua(page: Page, ano: Ano) {
  await expect(page.locator(".escala-barra")).toHaveCount(ano.padroes.length);
  await expect(page.locator(".padrao-label > span")).toHaveText([...ano.padroes].reverse().map((p) => p.rotulo));
  if (ano.padroes.length === 5)
    await expect(page.locator(".escala-barra.padrao-5")).toHaveCSS("background-color", "rgb(255, 255, 255)");
}

const CASOS = [
  { nome: "revista-1corte.json", comCores: true },
  { nome: "revista-3cortes.json", comCores: true },
  { nome: "revista-4cortes.json", comCores: true },
  { nome: "revista-4cortes.json", comCores: false }, // cor do 5º vinda só do styles.css
  { nome: "revista-misto.json", comCores: true }, // 5ef com 1 corte, 9ef com 4
];

for (const { nome, comCores } of CASOS) {
  test(`f1 ${nome}${comCores ? "" : " (cores do CSS)"}`, async ({ page }) => {
    const revista = fixture(nome);
    const anos = etapas(revista);
    const erros = await abrir(page, revista, comCores);

    // Abas de etapa: uma por ano, a primeira ativa com o rótulo longo
    const abas = page.locator(".filtro-btn");
    await expect(abas).toHaveCount(anos.length);
    await expect(abas.first()).toHaveClass(/active/);
    await expect(abas.first()).toHaveText("5º Ano do Ensino Fundamental");

    // Régua no primeiro render (antes de clicar) e depois da troca de aba, cada uma com a sua etapa
    await conferirRegua(page, revista[anos[0]]);
    await abas.nth(1).click();
    await expect(abas.nth(1)).toHaveClass(/active/);
    await expect(abas.nth(1)).toHaveText("9º Ano do Ensino Fundamental");
    await conferirRegua(page, revista[anos[1]]);

    expect(erros).toEqual([]);
  });
}

// JSON errado é bug do resolver: um console.error com etapa e motivo, e nenhuma escala pela metade
const INVALIDOS: [string, (ano: Ano) => void, string][] = [
  ["padroes ausente", (ano) => delete (ano as Partial<Ano>).padroes, "Etapa 5ef: JSON da revista inválido: padroes ausente"],
  [
    "padroes com tamanho errado",
    (ano) => ano.padroes.pop(),
    "Etapa 5ef: JSON da revista inválido: padroes deve ter 4 itens (veio 3)",
  ],
];

for (const [caso, estragar, mensagem] of INVALIDOS) {
  test(`f1 inválido: ${caso}`, async ({ page }) => {
    const revista = fixture("revista-3cortes.json");
    estragar(revista["5ef"]);
    const erros = await abrir(page, revista);
    await expect(page.locator(".descritor-badge")).toHaveText("D01"); // o resto da etapa renderiza
    await expect(page.locator(".escala-content > *")).toHaveCount(0);
    expect(erros).toEqual([mensagem]);
  });
}

test("f1 rótulo do padrão é escapado", async ({ page }) => {
  const revista = fixture("revista-3cortes.json");
  const rotulo = "<img src=x onerror=alert(1)>";
  revista["5ef"].padroes[3].rotulo = rotulo;
  page.on("dialog", (d) => d.dismiss());
  const erros = await abrir(page, revista);
  await expect(page.locator(".padrao-label > span").first()).toHaveText(rotulo);
  await expect(page.locator(".padrao-label img")).toHaveCount(0);
  expect(erros).toEqual([]);
});
