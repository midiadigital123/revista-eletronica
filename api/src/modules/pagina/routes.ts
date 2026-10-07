import { Router } from "express";
import { CAMPOS_PAGINA } from "../../contrato/campos-pagina.js";

/** Montado em /api/pagina */
export const paginaRouter = Router();

paginaRouter.get("/campos", (_req, res) => {
  res.json(CAMPOS_PAGINA);
});
