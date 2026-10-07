import { Router } from "express";
import multer from "multer";
import { PDF_MAX_BYTES } from "../../contrato/schemas.js";
import { requisicaoInvalida } from "../../errors.js";
import { handler } from "../../middlewares/handler.js";
import { extrairPdf } from "./service.js";

/**
 * Montado em /api/extracao (já atrás de requireAuth). Sem bloqueio: não grava nada.
 * POST / (multipart "arquivo", PDF) → ResultadoExtracao. Ver docs/contrato.md.
 */
export const extracaoRouter = Router();

const receberPdf = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: PDF_MAX_BYTES, files: 1 },
}).single("arquivo");

extracaoRouter.post(
  "/",
  receberPdf,
  handler({}, async (_e, req, res) => {
    const arquivo = req.file;
    if (!arquivo) throw requisicaoInvalida("Envie o PDF no campo arquivo", { campo: "arquivo" });
    // Bytes mágicos: o mime declarado pelo navegador não é confiável.
    if (arquivo.buffer.toString("latin1", 0, 5) !== "%PDF-")
      throw requisicaoInvalida("O arquivo não é um PDF", { campo: "arquivo" });
    res.json(await extrairPdf(arquivo.buffer));
  }),
);
