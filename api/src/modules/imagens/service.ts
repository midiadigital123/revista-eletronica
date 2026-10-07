import { PassThrough, Readable } from "node:stream";
import { pipeline } from "node:stream/promises";
import mongoose, { Types } from "mongoose";
import { nomeArquivoImagem } from "../../contrato/schemas.js";
import { naoEncontrado } from "../../errors.js";
import type { ImagemArmazenada, ValorPagina } from "../projetos/model.js";

/**
 * DONO: A5b. Armazenamento de imagens de página no GridFS (bucket "imagens").
 * Outros módulos usam só estas assinaturas:
 *  - A5a: copiarImagens (criar projeto com origem "copiar"), removerImagens (não usado na exclusão lógica)
 *  - A7: abrirLeitura (preview e zip)
 */

const BUCKET = "imagens";

/** Criado sob demanda: a conexão abre antes do app, mas não antes da importação. */
function bancoAberto() {
  const db = mongoose.connection.db;
  if (!db) throw new Error("MongoDB não conectado");
  return db;
}

const bucket = () => new mongoose.mongo.GridFSBucket(bancoAberto(), { bucketName: BUCKET });

export const ehImagem = (valor: unknown): valor is ImagemArmazenada =>
  typeof valor === "object" && !Array.isArray(valor) && valor !== null && "arquivoId" in valor;

/** Grava o binário no GridFS e devolve os metadados a guardar em projeto.pagina[chave]. */
export async function salvarImagem(dados: {
  chave: string;
  mime: ImagemArmazenada["mime"];
  conteudo: Buffer;
}): Promise<ImagemArmazenada> {
  const nome = nomeArquivoImagem(dados.chave, dados.mime);
  const upload = bucket().openUploadStream(nome, {
    metadata: { chave: dados.chave, mime: dados.mime },
  });
  await pipeline(Readable.from([dados.conteudo]), upload);
  return { arquivoId: upload.id, nome, mime: dados.mime, tamanho: dados.conteudo.length };
}

/** Stream do arquivo; se não existir, o stream emite AppError 404. */
export function abrirLeitura(arquivoId: Types.ObjectId): Readable {
  const origem = bucket().openDownloadStream(arquivoId);
  const saida = new PassThrough();
  origem.on("error", (erro) =>
    saida.destroy(/FileNotFound/.test(erro.message) ? naoEncontrado("Imagem") : erro),
  );
  return origem.pipe(saida);
}

/** Remove arquivos do GridFS. Ignora ids inexistentes. */
export async function removerImagens(arquivoIds: Types.ObjectId[]): Promise<void> {
  if (arquivoIds.length === 0) return;
  const db = bancoAberto();
  await db.collection(`${BUCKET}.files`).deleteMany({ _id: { $in: arquivoIds } });
  await db.collection(`${BUCKET}.chunks`).deleteMany({ files_id: { $in: arquivoIds } });
}

/**
 * Duplica no GridFS todas as imagens da página e devolve uma cópia da página
 * apontando para os novos arquivos (textos são copiados como estão).
 */
export async function copiarImagens(
  pagina: Record<string, ValorPagina>,
): Promise<Record<string, ValorPagina>> {
  const copia: Record<string, ValorPagina> = { ...pagina };
  for (const [chave, valor] of Object.entries(pagina)) {
    if (!ehImagem(valor)) continue;
    const upload = bucket().openUploadStream(valor.nome, {
      metadata: { chave, mime: valor.mime },
    });
    await pipeline(abrirLeitura(valor.arquivoId), upload);
    copia[chave] = { ...valor, arquivoId: upload.id };
  }
  return copia;
}
