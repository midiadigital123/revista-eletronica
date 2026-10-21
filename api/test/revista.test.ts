import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { arquivosEstaticosRevista, cssDasCores, renderRevista } from "../src/modules/revista/render.js";
import { anosDaRevista, revistaDosAnos } from "../src/contrato/revista.js";
import { CORES_PADRAO, Revista, type AnoProjeto, type Cores, type Pagina } from "../src/contrato/schemas.js";

const fixture = Revista.parse(
  JSON.parse(readFileSync(new URL("./fixtures/revista.json", import.meta.url), "utf8")),
);
const anos = anosDaRevista(fixture);

/** Extrai e parseia o conteúdo do bloco #dados-revista. */
function dadosDoHtml(html: string): unknown {
  const m = /<script type="application\/json" id="dados-revista">([\s\S]*?)<\/script>/.exec(html);
  expect(m).not.toBeNull();
  return JSON.parse(m![1]!);
}

describe("renderRevista", () => {
  it("usa o título padrão sem página", () => {
    const html = renderRevista({ anos, pagina: {}, cores: null });
    expect(html).toContain("<h1>ANÁLISE DOS RESULTADOS PARA INTERVENÇÃO PEDAGÓGICA</h1>");
    expect(html).toContain("Nesta seção, é apresentada");
  });

  it("sem imagem do hero não aponta para o servidor do Figma", () => {
    const html = renderRevista({ anos, pagina: {}, cores: null });
    expect(html).not.toContain("localhost:3845");
    expect(html).not.toContain("Ilustração pedagógica");
    expect(html).toContain('<img src="assets/seta-anterior.svg"');
    expect(html).toContain('<img src="assets/seta-proxima.svg"');
  });

  it("aplica título, parágrafos e imagem personalizados (com escape)", () => {
    const pagina: Pagina = {
      heroTitulo: "Revista <b>2026</b>",
      introParagrafos: ["Primeiro", "Segundo"],
      heroImagem: { nome: "x.png", mime: "image/png", tamanho: 10 },
    };
    const html = renderRevista({ anos, pagina, cores: null });
    expect(html).toContain("<h1>Revista &lt;b&gt;2026&lt;/b&gt;</h1>");
    expect(html).toContain("<p>Primeiro</p>");
    expect(html).toContain("<p>Segundo</p>");
    expect(html).not.toContain("Nesta seção, é apresentada");
    expect(html).toContain('<img src="arquivos/heroImagem.png"');
  });

  it("#dados-revista é parseável e igual a revistaDosAnos", () => {
    const pagina: Pagina = { heroTitulo: "T" };
    expect(dadosDoHtml(renderRevista({ anos, pagina, cores: null }))).toEqual(revistaDosAnos(anos, pagina));
  });

  it("conteúdo com </script> e U+2028 não quebra o bloco", () => {
    const [primeiro, ...resto] = anos as [AnoProjeto, ...AnoProjeto[]];
    const [d, ...outros] = primeiro.descritores;
    const hostil: AnoProjeto = {
      ...primeiro,
      descritores: [{ ...d!, description: "a</script><script>alert(1)</script>b c d" }, ...outros],
    };
    const pagina: Pagina = {};
    const html = renderRevista({ anos: [hostil, ...resto], pagina, cores: null });
    expect(html.match(/<script\b/g)).toHaveLength(2); // dados + script.js
    expect(dadosDoHtml(html)).toEqual(revistaDosAnos([hostil, ...resto], pagina));
  });

  it("gera uma aba por ano do projeto, na ordem das etapas", () => {
    const [base] = anos as [AnoProjeto];
    const html = renderRevista({
      anos: [
        { ...base, ano: "5ef" },
        { ...base, ano: "2ef" },
      ],
      pagina: {},
      cores: null,
    });
    const abas = [
      ...html.matchAll(
        /<button class="filtro-btn tab( active)?" data-filter="(\w+)"[^>]*>([^<]*)</g,
      ),
    ].map((m) => [m[2], m[3], Boolean(m[1])]);
    expect(abas).toEqual([
      ["2ef", "2º EF", true],
      ["5ef", "5º EF", false],
    ]);
    expect(html).not.toMatch(/data-filter="(9ef|3em)"/);
  });
});

const verdes: Cores = {
  "padrao-1": "#14532d",
  "padrao-2": "#228b22",
  "padrao-3": "#90ee90",
  "padrao-4": "#0b6b3a",
};

describe("cores do projeto", () => {
  it("sem cores ou com as cores padrão não há <style>", () => {
    expect(renderRevista({ anos, pagina: {}, cores: null })).not.toContain("<style>");
    expect(renderRevista({ anos, pagina: {}, cores: { ...CORES_PADRAO } })).not.toContain("<style>");
  });

  it("cores verdes viram variáveis em :root com -bg a 10%", () => {
    const html = renderRevista({ anos, pagina: {}, cores: verdes });
    expect(html).toContain("<style>:root{");
    expect(html).toContain("--color-padrao-4:#0b6b3a;");
    expect(html).toContain("--color-padrao-4-bg:rgba(11, 107, 58, 0.1);");
    expect(html.indexOf("styles.css")).toBeLessThan(html.indexOf("--color-padrao-1:"));
  });

  it("cssDasCores lança com valor malicioso", () => {
    expect(() => cssDasCores({ ...verdes, "padrao-1": "red;}</style><script>" })).toThrow();
  });
});

describe("arquivosEstaticosRevista", () => {
  it("devolve styles.css, script.js e os ícones com conteúdo", () => {
    const arquivos = arquivosEstaticosRevista();
    expect(arquivos.map((a) => a.caminho)).toEqual([
      "styles.css",
      "script.js",
      "assets/seta-anterior.svg",
      "assets/seta-proxima.svg",
    ]);
    for (const a of arquivos) expect(a.conteudo.length).toBeGreaterThan(0);
  });
});
