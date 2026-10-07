import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { arquivosEstaticosRevista, renderRevista } from "../src/modules/revista/render.js";
import { anosDaRevista, revistaDosAnos } from "../src/contrato/revista.js";
import { Revista, type AnoProjeto, type Pagina } from "../src/contrato/schemas.js";

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
    const html = renderRevista({ anos, pagina: {} });
    expect(html).toContain("<h1>ANÁLISE DOS RESULTADOS PARA INTERVENÇÃO PEDAGÓGICA</h1>");
    expect(html).toContain("Nesta seção, é apresentada");
  });

  it("sem imagem do hero não aponta para o servidor do Figma", () => {
    const html = renderRevista({ anos, pagina: {} });
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
    const html = renderRevista({ anos, pagina });
    expect(html).toContain("<h1>Revista &lt;b&gt;2026&lt;/b&gt;</h1>");
    expect(html).toContain("<p>Primeiro</p>");
    expect(html).toContain("<p>Segundo</p>");
    expect(html).not.toContain("Nesta seção, é apresentada");
    expect(html).toContain('<img src="arquivos/heroImagem.png"');
  });

  it("#dados-revista é parseável e igual a revistaDosAnos", () => {
    const pagina: Pagina = { heroTitulo: "T" };
    expect(dadosDoHtml(renderRevista({ anos, pagina }))).toEqual(revistaDosAnos(anos, pagina));
  });

  it("conteúdo com </script> e U+2028 não quebra o bloco", () => {
    const [primeiro, ...resto] = anos as [AnoProjeto, ...AnoProjeto[]];
    const [d, ...outros] = primeiro.descritores;
    const hostil: AnoProjeto = {
      ...primeiro,
      descritores: [{ ...d!, description: "a</script><script>alert(1)</script>b c d" }, ...outros],
    };
    const pagina: Pagina = {};
    const html = renderRevista({ anos: [hostil, ...resto], pagina });
    expect(html.match(/<script\b/g)).toHaveLength(2); // dados + script.js
    expect(dadosDoHtml(html)).toEqual(revistaDosAnos([hostil, ...resto], pagina));
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
