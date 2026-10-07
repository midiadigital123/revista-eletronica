import type { ErrorRequestHandler, RequestHandler } from "express";
import mongoose from "mongoose";
import { MulterError } from "multer";
import { ZodError } from "zod";
import type { ErroApi } from "../contrato/schemas.js";
import { AppError } from "../errors.js";

export const rotaNaoEncontrada: RequestHandler = (_req, res) => {
  res.status(404).json({ erro: "Rota não encontrada" } satisfies ErroApi);
};

/** Converte qualquer erro no formato ErroApi do contrato. Último middleware do app. */
export const errorHandler: ErrorRequestHandler = (erro, req, res, _next) => {
  const [status, corpo] = traduzir(erro);
  if (status >= 500) req.log?.error({ err: erro }, "erro não tratado");
  res.status(status).json(corpo);
};

function traduzir(erro: unknown): [number, ErroApi] {
  if (erro instanceof AppError) {
    const { campo, detalhes, bloqueio } = erro.opcoes;
    return [erro.status, { erro: erro.erro, campo, detalhes, bloqueio }];
  }
  if (erro instanceof ZodError) {
    const detalhes = erro.issues.map((i) => ({ campo: i.path.join("."), erro: i.message }));
    return [
      400,
      { erro: detalhes[0]?.erro ?? "Dados inválidos", campo: detalhes[0]?.campo, detalhes },
    ];
  }
  if (erro instanceof MulterError) {
    if (erro.code === "LIMIT_FILE_SIZE") return [413, { erro: "Arquivo grande demais" }];
    return [400, { erro: erro.message, campo: erro.field }];
  }
  if (erro instanceof mongoose.Error.VersionError)
    return [409, { erro: "O projeto mudou durante a gravação; recarregue e tente de novo" }];
  if (erro instanceof mongoose.Error.ValidationError) {
    const detalhes = Object.values(erro.errors).map((e) => ({ campo: e.path, erro: e.message }));
    return [400, { erro: "Dados inválidos", campo: detalhes[0]?.campo, detalhes }];
  }
  if (erro instanceof mongoose.Error.CastError)
    return [400, { erro: `Valor inválido em ${erro.path}`, campo: erro.path }];
  const e = erro as { type?: string; status?: number; code?: number; keyValue?: object };
  if (e.type === "entity.too.large") return [413, { erro: "Conteúdo grande demais" }];
  if (e.type === "entity.parse.failed") return [400, { erro: "JSON inválido" }];
  if (e.code === 11000) {
    const campo = Object.keys(e.keyValue ?? {})[0];
    return [409, { erro: "Registro duplicado", campo }];
  }
  if (e.status && e.status >= 400 && e.status < 500)
    return [e.status, { erro: "Requisição inválida" }];
  return [500, { erro: "Erro interno do servidor" }];
}
