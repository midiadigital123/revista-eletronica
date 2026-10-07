import { Router } from "express";
import { requireAuth } from "../middlewares/auth.js";
import { authRouter } from "./auth/routes.js";
import { bloqueioRouter } from "./bloqueio/routes.js";
import { extracaoRouter } from "./extracao/routes.js";
import { geracaoRouter } from "./geracao/routes.js";
import { imagensRouter } from "./imagens/routes.js";
import { paginaRouter } from "./pagina/routes.js";
import { projetosRouter } from "./projetos/routes.js";
import { usuariosRouter } from "./usuarios/routes.js";

/**
 * Ponto único de registro das rotas. Cada módulo tem um dono (ver plano);
 * os donos editam o próprio routes.ts, não este arquivo.
 * Tudo depois de /auth exige login (requireAuth aplicado uma vez, aqui).
 * Rotas mais específicas de /projetos/:slug vêm antes do router genérico.
 */
export const apiRouter = Router();

apiRouter.use("/auth", authRouter);
apiRouter.use(requireAuth);
apiRouter.use("/usuarios", usuariosRouter);
apiRouter.use("/pagina", paginaRouter);
apiRouter.use("/extracao", extracaoRouter);
apiRouter.use("/projetos/:slug/bloqueio", bloqueioRouter);
apiRouter.use("/projetos/:slug/pagina/:chave/imagem", imagensRouter);
apiRouter.use("/projetos/:slug", geracaoRouter);
apiRouter.use("/projetos", projetosRouter);
