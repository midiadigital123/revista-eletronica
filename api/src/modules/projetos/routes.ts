import { Router } from "express";
import { z } from "zod";
import {
  AtualizarAnoEntrada,
  AtualizarDescritorEntrada,
  AtualizarProjetoEntrada,
  CriarAnoEntrada,
  CriarDescritorEntrada,
  CriarProjetoEntrada,
  LinhasPadrao,
  PaginaPatch,
  ParamsAno,
  ParamsDescritor,
  ParamsProjeto,
} from "../../contrato/schemas.js";
import { editorDaRequisicao, exigirBloqueio } from "../../middlewares/exigirBloqueio.js";
import { handler } from "../../middlewares/handler.js";
import * as service from "./service.js";

/**
 * Montado em /api/projetos (já atrás de requireAuth). CRUD de projeto, anos,
 * descritores, escala, página (textos) e exportação JSON. Escritas usam exigirBloqueio.
 */
export const projetosRouter = Router();

// O contrato pede 404 (não 400) para padrão inexistente: o service valida o padrão.
const ParamsEscala = ParamsDescritor.extend({ padrao: z.string() });

const descritor = "/:slug/anos/:ano/descritores/:codigo";

// ---------- projeto

projetosRouter.get(
  "/",
  handler({}, async (_e, _req, res) => {
    res.json(await service.listar());
  }),
);

projetosRouter.post(
  "/",
  handler({ body: CriarProjetoEntrada }, async ({ body }, req, res) => {
    res.status(201).json(await service.criar(body, editorDaRequisicao(req)));
  }),
);

projetosRouter.get(
  "/:slug",
  handler({ params: ParamsProjeto }, async ({ params }, _req, res) => {
    res.json(await service.obter(params.slug));
  }),
);

projetosRouter.patch(
  "/:slug",
  exigirBloqueio,
  handler({ params: ParamsProjeto, body: AtualizarProjetoEntrada }, async ({ params, body }, _req, res) => {
    res.json(await service.atualizar(params.slug, body));
  }),
);

projetosRouter.delete(
  "/:slug",
  exigirBloqueio,
  handler({ params: ParamsProjeto }, async ({ params }, _req, res) => {
    await service.excluir(params.slug);
    res.status(204).end();
  }),
);

projetosRouter.get(
  "/:slug/revista",
  handler({ params: ParamsProjeto }, async ({ params }, _req, res) => {
    res.json(await service.exportarRevista(params.slug));
  }),
);

projetosRouter.patch(
  "/:slug/pagina",
  exigirBloqueio,
  handler({ params: ParamsProjeto, body: PaginaPatch }, async ({ params, body }, _req, res) => {
    res.json(await service.atualizarPagina(params.slug, body));
  }),
);

// ---------- anos

projetosRouter.post(
  "/:slug/anos",
  exigirBloqueio,
  handler({ params: ParamsProjeto, body: CriarAnoEntrada }, async ({ params, body }, _req, res) => {
    res.status(201).json(await service.criarAno(params.slug, body));
  }),
);

projetosRouter.patch(
  "/:slug/anos/:ano",
  exigirBloqueio,
  handler({ params: ParamsAno, body: AtualizarAnoEntrada }, async ({ params, body }, _req, res) => {
    res.json(await service.atualizarAno(params.slug, params.ano, body));
  }),
);

projetosRouter.delete(
  "/:slug/anos/:ano",
  exigirBloqueio,
  handler({ params: ParamsAno }, async ({ params }, _req, res) => {
    await service.excluirAno(params.slug, params.ano);
    res.status(204).end();
  }),
);

// ---------- descritores

projetosRouter.post(
  "/:slug/anos/:ano/descritores",
  exigirBloqueio,
  handler({ params: ParamsAno, body: CriarDescritorEntrada }, async ({ params, body }, _req, res) => {
    res.status(201).json(await service.criarDescritor(params.slug, params.ano, body));
  }),
);

projetosRouter.patch(
  descritor,
  exigirBloqueio,
  handler(
    { params: ParamsDescritor, body: AtualizarDescritorEntrada },
    async ({ params, body }, _req, res) => {
      res.json(await service.atualizarDescritor(params.slug, params.ano, params.codigo, body));
    },
  ),
);

projetosRouter.delete(
  descritor,
  exigirBloqueio,
  handler({ params: ParamsDescritor }, async ({ params }, _req, res) => {
    await service.excluirDescritor(params.slug, params.ano, params.codigo);
    res.status(204).end();
  }),
);

projetosRouter.put(
  `${descritor}/escala/:padrao`,
  exigirBloqueio,
  handler({ params: ParamsEscala, body: LinhasPadrao }, async ({ params, body }, _req, res) => {
    const { slug, ano, codigo, padrao } = params;
    res.json(await service.salvarEscala(slug, ano, codigo, padrao, body));
  }),
);
