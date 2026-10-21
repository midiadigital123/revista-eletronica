import { Router } from "express";
import multer from "multer";
import { Types } from "mongoose";
import { z } from "zod";
import { ITEM_MAX_BYTES, ITEM_MIMES, ParamsProjeto, type ItemPdf } from "../../contrato/schemas.js";
import { naoEncontrado, requisicaoInvalida } from "../../errors.js";
import { exigirBloqueio } from "../../middlewares/exigirBloqueio.js";
import { handler } from "../../middlewares/handler.js";
import { enviarArquivo, mimeDoConteudo } from "../imagens/routes.js";
import { mimeDoArquivo, salvarItem } from "../imagens/service.js";
import { obterProjeto } from "../projetos/repository.js";

/**
 * Montado em /api/projetos/:slug/itens. Arquivo (PDF, PNG ou JPG) do "Ver item" de uma linha da escala.
 * POST 🔒 (multipart "arquivo") devolve um ItemPdf; o editor o grava na linha via PUT escala.
 * GET /:id (stream). Arquivos compartilhados entre cópias do projeto e nunca removidos.
 */
export const itensRouter = Router({ mergeParams: true });

// id inválido vira 404 (como inexistente), não 400.
const ParamsItem = ParamsProjeto.extend({ id: z.string() });

type Tipo = NonNullable<ItemPdf["tipo"]>;

/** Tipo do item pelo mime declarado (undefined se não for aceito). */
const tipoDoMime = (mime: string) =>
  (Object.keys(ITEM_MIMES) as Tipo[]).find((t) => ITEM_MIMES[t] === mime);

/** Mime real pelos bytes mágicos (o declarado pelo navegador não é confiável). */
const mimeReal = (b: Buffer) =>
  b.toString("latin1", 0, 5) === "%PDF-" ? ITEM_MIMES.pdf : mimeDoConteudo(b);

const receberArquivo = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: ITEM_MAX_BYTES, files: 1 },
}).single("arquivo");

itensRouter.post(
  "/",
  receberArquivo,
  exigirBloqueio,
  handler({ params: ParamsProjeto }, async ({ params }, req, res) => {
    const arquivo = req.file;
    if (!arquivo) throw requisicaoInvalida("Envie o arquivo no campo arquivo", { campo: "arquivo" });
    const tipo = tipoDoMime(arquivo.mimetype);
    if (!tipo) throw requisicaoInvalida("Use um PDF, PNG ou JPG", { campo: "arquivo" });
    if (mimeReal(arquivo.buffer) !== arquivo.mimetype)
      throw requisicaoInvalida("O conteúdo do arquivo não é do tipo informado", { campo: "arquivo" });

    await obterProjeto(params.slug);
    const id = await salvarItem(arquivo.originalname, arquivo.mimetype, arquivo.buffer);
    const nome = arquivo.originalname.slice(0, 300); // limite do ItemPdf
    const item: ItemPdf = { id: id.toString(), nome, tamanho: arquivo.size, tipo };
    res.status(201).json(item);
  }),
);

itensRouter.get(
  "/:id",
  handler({ params: ParamsItem }, async ({ params }, _req, res) => {
    await obterProjeto(params.slug);
    if (!/^[a-f0-9]{24}$/.test(params.id)) throw naoEncontrado("Item");
    const id = new Types.ObjectId(params.id);
    await enviarArquivo(res, id, await mimeDoArquivo(id));
  }),
);
