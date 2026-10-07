import type { Readable } from "node:stream";
import Handlebars from "handlebars";
import { camposDoTipo } from "../../contrato/campos-pagina.js";
import { rotuloCaderno, type CadernoProjeto } from "../../contrato/schemas.js";
import { renderRevista, arquivosEstaticosRevista } from "../revista/render.js";
import { abrirLeitura, ehImagem } from "../imagens/service.js";
import { obterProjeto, paraCadernos, paraPagina } from "../projetos/repository.js";

/** Arquivo da revista: conteúdo em memória ou stream aberto sob demanda. */
export interface ArquivoPacote {
  caminho: string;
  tipo: string;
  abrir: () => Buffer | Readable;
}

const TIPOS: Record<string, string> = {
  html: "text/html; charset=utf-8",
  css: "text/css; charset=utf-8",
  js: "text/javascript; charset=utf-8",
  png: "image/png",
  jpg: "image/jpeg",
  webp: "image/webp",
  svg: "image/svg+xml",
};

const tipoDe = (caminho: string) =>
  TIPOS[caminho.split(".").pop() ?? ""] ?? "application/octet-stream";

const esc = Handlebars.Utils.escapeExpression;

/** index.html da raiz: um link por caderno. */
function indiceRaiz(nome: string, cadernos: CadernoProjeto[]): Buffer {
  const links = cadernos
    .map(({ id }) => `    <li><a href="${esc(id)}/index.html">${esc(rotuloCaderno(id))}</a></li>`)
    .join("\n");
  return Buffer.from(`<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${esc(nome)}</title>
</head>
<body>
  <h1>${esc(nome)}</h1>
  <ul>
${links}
  </ul>
</body>
</html>
`);
}

/**
 * Fonte única dos arquivos da revista: preview e zip usam esta lista.
 * Um `index.html` na raiz com links e uma pasta por caderno (`<caderno>/index.html`,
 * estáticos e `arquivos/<imagem>`); a página (textos/imagens) é a mesma em todas.
 */
export async function montarPacote(slug: string): Promise<ArquivoPacote[]> {
  const projeto = await obterProjeto(slug);
  const pagina = paraPagina(projeto);
  const cadernos = paraCadernos(projeto);
  const raiz = indiceRaiz(projeto.nome, cadernos);
  const arquivos: ArquivoPacote[] = [
    { caminho: "index.html", tipo: tipoDe("index.html"), abrir: () => raiz },
  ];
  for (const { id, anos } of cadernos) {
    const html = Buffer.from(renderRevista({ anos, pagina }));
    arquivos.push(
      { caminho: `${id}/index.html`, tipo: tipoDe("index.html"), abrir: () => html },
      ...arquivosEstaticosRevista().map(({ caminho, conteudo }) => ({
        caminho: `${id}/${caminho}`,
        tipo: tipoDe(caminho),
        abrir: () => conteudo,
      })),
    );
    for (const { chave } of camposDoTipo("imagem")) {
      const imagem = projeto.pagina[chave];
      if (!ehImagem(imagem)) continue;
      arquivos.push({
        caminho: `${id}/arquivos/${imagem.nome}`,
        tipo: imagem.mime,
        abrir: () => abrirLeitura(imagem.arquivoId),
      });
    }
  }
  return arquivos;
}
