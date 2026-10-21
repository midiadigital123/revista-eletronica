import type { Request, RequestHandler } from "express";
import { HEADER_SESSAO_EDICAO } from "../contrato/schemas.js";
import { requisicaoInvalida } from "../errors.js";
import { exigir, type Editor } from "../modules/bloqueio/service.js";
import { usuarioDaSessao } from "./auth.js";

/** Editor (usuário + aba) que fez a requisição. A aba vem do header X-Sessao-Edicao. */
export function editorDaRequisicao(req: Request): Editor {
  const usuario = usuarioDaSessao(req);
  const sessaoEdicao = req.get(HEADER_SESSAO_EDICAO);
  if (!sessaoEdicao || sessaoEdicao.length > 100)
    throw requisicaoInvalida(`Header ${HEADER_SESSAO_EDICAO} ausente`, {
      campo: HEADER_SESSAO_EDICAO,
    });
  return { usuarioId: usuario.id, nome: usuario.nome, sessaoEdicao };
}

/**
 * ponytail: verifica e depois o handler grava; se o TTL vencer entre os dois
 * (milissegundos), a escrita passa. Aceitável com heartbeat de 30 s em TTL de 2 min.
 * Rotas com upload rodam este middleware depois do multer, para a janela continuar curta.
 *
 * Exige que quem pede detenha o bloqueio do projeto `:slug`. Use em toda rota de
 * escrita de projeto (depois de requireAuth). 423 caso contrário.
 */
export const exigirBloqueio: RequestHandler = async (req, _res, next) => {
  try {
    await exigir(String(req.params.slug), editorDaRequisicao(req));
    next();
  } catch (erro) {
    next(erro);
  }
};
