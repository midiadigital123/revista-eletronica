import { Router } from "express";
import {
  AtualizarUsuarioEntrada,
  CriarUsuarioEntrada,
  ParamsUsuario,
} from "../../contrato/schemas.js";
import { requireAdmin, usuarioDaSessao } from "../../middlewares/auth.js";
import { handler } from "../../middlewares/handler.js";
import { atualizarUsuario, criarUsuario, excluirUsuario, listarUsuarios } from "./service.js";

/** Montado em /api/usuarios (já atrás de requireAuth). Só admin. */
export const usuariosRouter = Router();
usuariosRouter.use(requireAdmin);

usuariosRouter.get(
  "/",
  handler({}, async (_entrada, _req, res) => {
    res.json(await listarUsuarios());
  }),
);

usuariosRouter.post(
  "/",
  handler({ body: CriarUsuarioEntrada }, async ({ body }, _req, res) => {
    res.status(201).json(await criarUsuario(body));
  }),
);

usuariosRouter.patch(
  "/:id",
  handler({ params: ParamsUsuario, body: AtualizarUsuarioEntrada }, async ({ params, body }, _req, res) => {
    res.json(await atualizarUsuario(params.id, body));
  }),
);

usuariosRouter.delete(
  "/:id",
  handler({ params: ParamsUsuario }, async ({ params }, req, res) => {
    await excluirUsuario(params.id, usuarioDaSessao(req).id);
    res.status(204).end();
  }),
);
