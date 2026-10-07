import type { Readable } from "node:stream";
import { camposDoTipo } from "../../contrato/campos-pagina.js";
import { renderRevista, arquivosEstaticosRevista } from "../revista/render.js";
import { abrirLeitura, ehImagem } from "../imagens/service.js";
import { obterProjeto, paraAnos, paraPagina } from "../projetos/repository.js";

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

/** Fonte única dos arquivos da revista: preview e zip usam esta lista. */
export async function montarPacote(slug: string): Promise<ArquivoPacote[]> {
  const projeto = await obterProjeto(slug);
  const html = Buffer.from(renderRevista({ anos: paraAnos(projeto), pagina: paraPagina(projeto) }));
  const arquivos: ArquivoPacote[] = [
    { caminho: "index.html", tipo: tipoDe("index.html"), abrir: () => html },
    ...arquivosEstaticosRevista().map(({ caminho, conteudo }) => ({
      caminho,
      tipo: tipoDe(caminho),
      abrir: () => conteudo,
    })),
  ];
  for (const { chave } of camposDoTipo("imagem")) {
    const imagem = projeto.pagina[chave];
    if (!ehImagem(imagem)) continue;
    arquivos.push({
      caminho: `arquivos/${imagem.nome}`,
      tipo: imagem.mime,
      abrir: () => abrirLeitura(imagem.arquivoId),
    });
  }
  return arquivos;
}
