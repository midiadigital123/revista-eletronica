import type { RequestHandler } from "express";
import { naoAutenticado, proibido } from "../errors.js";
import { UsuarioModel } from "../modules/usuarios/model.js";

/**
 * Exige sessão de um usuário que ainda existe e está ativo. Atualiza nome e
 * perfil na sessão a cada requisição: desativar ou rebaixar vale na hora.
 */
export const requireAuth: RequestHandler = async (req, _res, next) => {
  try {
    const sessao = req.session.usuario;
    if (!sessao) return next(naoAutenticado());
    const usuario = await UsuarioModel.findById(sessao.id).lean();
    if (!usuario?.ativo) {
      req.session.usuario = undefined;
      return next(naoAutenticado());
    }
    req.session.usuario = { id: sessao.id, nome: usuario.nome, perfil: usuario.perfil };
    next();
  } catch (erro) {
    next(erro);
  }
};

/** Use depois de requireAuth. */
export const requireAdmin: RequestHandler = (req, _res, next) => {
  next(req.session.usuario?.perfil === "admin" ? undefined : proibido());
};

/** Usuário da sessão; use só em rotas atrás de requireAuth. */
export function usuarioDaSessao(req: Express.Request) {
  const usuario = req.session.usuario;
  if (!usuario) throw naoAutenticado();
  return usuario;
}
