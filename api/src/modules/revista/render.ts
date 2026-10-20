import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import Handlebars from "handlebars";
import { camposDoTipo } from "../../contrato/campos-pagina.js";
import { revistaDosAnos } from "../../contrato/revista.js";
import {
  Cores,
  PADROES,
  compararAnos,
  mesmasCores,
  nomeArquivoImagem,
  rotuloAno,
  type AnoProjeto,
  type Pagina,
} from "../../contrato/schemas.js";

/**
 * Renderiza revista/escala.hbs com os dados do projeto. Função pura (sem Mongo).
 * Ver docs/contrato.md, seção "Template da revista".
 */
export interface EntradaRender {
  anos: AnoProjeto[];
  /** Página no formato do contrato: textos e imagens ({nome, mime, tamanho}). */
  pagina: Pagina;
  /** Cores do projeto; null = padrão de styles.css. */
  cores: Cores | null;
}

export interface ArquivoRevista {
  caminho: string;
  conteudo: Buffer;
}

/**
 * Pasta revista/: `REVISTA_DIR` se definido (o Docker define); senão
 * `<raiz do repositório>/revista`, a partir de api/src/modules/revista/ ou
 * api/dist/modules/revista/ (ambos 3 níveis abaixo de api/).
 */
const pastaRevista = () =>
  process.env.REVISTA_DIR ?? join(dirname(fileURLToPath(import.meta.url)), "../../../../revista");

const lerRevista = (nome: string) => readFileSync(join(pastaRevista(), nome));

let template: HandlebarsTemplateDelegate | undefined;
let estaticos: ArquivoRevista[] | undefined;

/** Contexto `pagina` do template: textos como estão; imagens como `arquivos/<nome>`. */
function contextoPagina(pagina: Pagina): Record<string, string | string[]> {
  const contexto: Record<string, string | string[]> = {};
  for (const [chave, valor] of Object.entries(pagina)) {
    if (typeof valor === "string" || Array.isArray(valor)) contexto[chave] = valor;
  }
  for (const { chave } of camposDoTipo("imagem")) {
    const imagem = pagina[chave];
    if (imagem && typeof imagem === "object" && !Array.isArray(imagem))
      contexto[chave] = `arquivos/${nomeArquivoImagem(chave, imagem.mime)}`;
  }
  return contexto;
}

/** JSON seguro dentro de <script>: nada de `</script>` nem separadores de linha JS. */
const jsonSeguro = (valor: unknown) =>
  JSON.stringify(valor)
    .replaceAll("<", "\\u003c")
    .replaceAll(" ", "\\u2028")
    .replaceAll(" ", "\\u2029");

/** `:root{...}` que sobrescreve as cores dos padrões; "" nas cores padrão. Revalida: vai cru no <style>. */
export function cssDasCores(cores: Cores | null): string {
  if (mesmasCores(cores, null)) return "";
  const c = Cores.parse(cores);
  const vars = PADROES.map((p) => {
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(c[p].slice(i, i + 2), 16));
    return `--color-${p}:${c[p]};--color-${p}-bg:rgba(${r}, ${g}, ${b}, 0.1);`;
  });
  return `:root{${vars.join("")}}`;
}

/** HTML de index.html. */
export function renderRevista({ anos, pagina, cores }: EntradaRender): string {
  template ??= Handlebars.compile(lerRevista("escala.hbs").toString("utf8"));
  return template({
    // Abas da revista: uma por ano do projeto, na ordem das etapas (a primeira começa ativa).
    anos: anos
      .map(({ ano }) => ano)
      .sort(compararAnos)
      .map((chave) => ({ chave, rotulo: rotuloAno(chave) })),
    pagina: contextoPagina(pagina),
    cssCores: cssDasCores(cores),
    dadosRevista: jsonSeguro(revistaDosAnos(anos, pagina)),
  });
}

/** Arquivos estáticos da revista além do index.html (styles.css, script.js, ícones). */
export function arquivosEstaticosRevista(): ArquivoRevista[] {
  estaticos ??= [
    "styles.css",
    "script.js",
    "assets/seta-anterior.svg",
    "assets/seta-proxima.svg",
  ].map((caminho) => ({
    caminho,
    conteudo: lerRevista(caminho),
  }));
  return estaticos;
}
