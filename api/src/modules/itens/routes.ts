import { Router } from "express";
import multer from "multer";
import { Types } from "mongoose";
import { z } from "zod";
import { ITEM_MAX_BYTES, ParamsProjeto, type ItemPdf } from "../../contrato/schemas.js";
import { naoEncontrado, requisicaoInvalida } from "../../errors.js";
import { exigirBloqueio } from "../../middlewares/exigirBloqueio.js";
import { handler } from "../../middlewares/handler.js";
import { enviarArquivo } from "../imagens/routes.js";
import { salvarItem } from "../imagens/service.js";
import { obterProjeto } from "../projetos/repository.js";

/**
 * Montado em /api/projetos/:slug/itens. PDF do "Ver item" de uma linha da escala.
 * POST 🔒 (multipart "arquivo") devolve um ItemPdf; o editor o grava na linha via PUT escala.
 * GET /:id (stream). Arquivos compartilhados entre cópias do projeto e nunca removidos.
 */
export const itensRouter = Router({ mergeParams: true });

// id inválido vira 404 (como inexistente), não 400.
const ParamsItem = ParamsProjeto.extend({ id: z.string() });

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
    if (!arquivo) throw requisicaoInvalida("Envie o PDF no campo arquivo", { campo: "arquivo" });
    if (arquivo.mimetype !== "application/pdf")
      throw requisicaoInvalida("Use um arquivo PDF", { campo: "arquivo" });
    if (arquivo.buffer.toString("latin1", 0, 5) !== "%PDF-")
      throw requisicaoInvalida("O conteúdo do arquivo não é um PDF", { campo: "arquivo" });

    await obterProjeto(params.slug);
    const id = await salvarItem(arquivo.originalname, arquivo.buffer);
    const nome = arquivo.originalname.slice(0, 300); // limite do ItemPdf
    const item: ItemPdf = { id: id.toString(), nome, tamanho: arquivo.size };
    res.status(201).json(item);
  }),
);

itensRouter.get(
  "/:id",
  handler({ params: ParamsItem }, async ({ params }, _req, res) => {
    await obterProjeto(params.slug);
    if (!/^[a-f0-9]{24}$/.test(params.id)) throw naoEncontrado("Item");
    await enviarArquivo(res, new Types.ObjectId(params.id), "application/pdf");
  }),
);
