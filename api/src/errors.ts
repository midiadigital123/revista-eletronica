import type { BloqueioPublico, Problema } from "./contrato/schemas.js";

interface OpcoesErro {
  campo?: string;
  detalhes?: Problema[];
  bloqueio?: BloqueioPublico | null;
}

/** Erro de domínio com status HTTP; o errorHandler o converte no formato ErroApi do contrato. */
export class AppError extends Error {
  constructor(
    readonly status: number,
    readonly erro: string,
    readonly opcoes: OpcoesErro = {},
  ) {
    super(erro);
    this.name = "AppError";
  }
}

export const requisicaoInvalida = (erro: string, opcoes?: OpcoesErro) =>
  new AppError(400, erro, opcoes);

/** 400 a partir de problemas de domínio (problemasDoAno etc.). */
export const problemasInvalidos = (problemas: Problema[]) =>
  new AppError(400, problemas[0]?.erro ?? "Dados inválidos", {
    campo: problemas[0]?.campo,
    detalhes: problemas,
  });

export const naoAutenticado = () => new AppError(401, "Faça login para continuar");
export const proibido = () => new AppError(403, "Acesso restrito a administradores");
export const naoEncontrado = (oQue: string) => new AppError(404, `${oQue} não encontrado`);
export const conflito = (erro: string, campo?: string) => new AppError(409, erro, { campo });
/** 422: entrada bem formada que não deu para processar (ex.: PDF sem a seção esperada). */
export const naoProcessavel = (erro: string) => new AppError(422, erro);
export const muitoGrande = (erro = "Conteúdo grande demais") => new AppError(413, erro);
export const bloqueado = (bloqueio: BloqueioPublico | null) =>
  new AppError(
    423,
    bloqueio ? `Projeto em edição por ${bloqueio.nome}` : "Você não está editando este projeto",
    { bloqueio },
  );
