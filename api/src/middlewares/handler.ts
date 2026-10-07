import type { NextFunction, Request, RequestHandler, Response } from "express";
import type { z } from "zod";

interface Esquemas {
  params?: z.ZodType;
  query?: z.ZodType;
  body?: z.ZodType;
}

type Saida<S, K extends keyof Esquemas> = S extends Record<K, infer T extends z.ZodType>
  ? z.output<T>
  : undefined;

export interface Entrada<S extends Esquemas> {
  params: Saida<S, "params">;
  query: Saida<S, "query">;
  body: Saida<S, "body">;
}

/**
 * Cria um handler Express que valida params/query/body com Zod antes de chamar
 * `fn` com os dados já tipados. ZodError segue para o errorHandler (→ 400).
 *
 *   router.patch("/:slug", handler({ params: ParamsProjeto, body: AtualizarProjetoEntrada },
 *     async ({ params, body }, req, res) => { ... }));
 */
export function handler<S extends Esquemas>(
  esquemas: S,
  fn: (entrada: Entrada<S>, req: Request, res: Response) => Promise<void> | void,
): RequestHandler {
  return async (req: Request, res: Response, next: NextFunction) => {
    try {
      const entrada = {
        params: esquemas.params?.parse(req.params),
        query: esquemas.query?.parse(req.query),
        body: esquemas.body?.parse(req.body ?? {}),
      } as Entrada<S>;
      await fn(entrada, req, res);
    } catch (erro) {
      next(erro);
    }
  };
}
