import { Router } from "express";
import { ParamsProjeto } from "../../contrato/schemas.js";
import { handler } from "../../middlewares/handler.js";
import { editorDaRequisicao } from "../../middlewares/exigirBloqueio.js";
import { adquirir, liberar, renovar } from "./service.js";

/** Montado em /api/projetos/:slug/bloqueio */
export const bloqueioRouter = Router({ mergeParams: true });

bloqueioRouter.post(
  "/",
  handler({ params: ParamsProjeto }, async ({ params }, req, res) => {
    res.status(201).json(await adquirir(params.slug, editorDaRequisicao(req)));
  }),
);

bloqueioRouter.put(
  "/",
  handler({ params: ParamsProjeto }, async ({ params }, req, res) => {
    res.json(await renovar(params.slug, editorDaRequisicao(req)));
  }),
);

bloqueioRouter.delete(
  "/",
  handler({ params: ParamsProjeto }, async ({ params }, req, res) => {
    await liberar(params.slug, editorDaRequisicao(req));
    res.status(204).end();
  }),
);
