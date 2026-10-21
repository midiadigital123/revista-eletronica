import { createContext, useContext } from "react";
import type { BloqueioPublico, Projeto } from "../contrato/schemas";

/**
 * Contrato entre a casca do projeto (A6a, implementa o provedor) e as telas que
 * editam (A6a página; A6b ano/descritores/escala, consomem com useEdicao()).
 */

export type ModoEdicao = "carregando" | "edicao" | "leitura";

export interface EstadoSalvamento {
  status: "ocioso" | "salvando" | "salvo" | "erro";
  salvoEm?: Date;
  erro?: string;
}

export interface OperacaoSalvamento<T> {
  /** Texto curto para o usuário, ex.: "Descrição do D03". */
  descricao: string;
  /** Valor sendo salvo; se a escrita se perder (423), aparece para o usuário copiar. */
  valor?: string;
  executar: () => Promise<T>;
  /**
   * Aplica a resposta ao projeto em cache (setQueryData). Sem `aplicar`, o
   * provedor invalida o projeto (refetch) — use só em operações estruturais
   * (criar/excluir/renomear). Edições de campo SEMPRE passam `aplicar`, para
   * não refazer o fetch a cada autosave.
   */
  aplicar?: (projeto: Projeto, resposta: T) => Projeto;
}

export interface Edicao {
  slug: string;
  modo: ModoEdicao;
  /** Quem detém o bloqueio quando modo === "leitura" (null se ninguém). */
  bloqueio: BloqueioPublico | null;
  salvamento: EstadoSalvamento;
  /**
   * Executa uma escrita na fila serial do projeto (uma por vez, em ordem).
   * Sucesso: aplica `aplicar` no cache de chaves.projeto(slug) ou invalida.
   * Erro 423: troca para modo leitura e guarda a operação nos não salvos.
   * Sempre rejeita com o ApiError original para o formulário mostrar o erro.
   *
   * Regra para os formulários: inicializam do cache uma vez (key = entidade,
   * ex.: `${ano}-${codigo}`) e não se resetam quando o cache muda depois.
   */
  salvar<T>(operacao: OperacaoSalvamento<T>): Promise<T>;
}

export const EdicaoContext = createContext<Edicao | null>(null);

export function useEdicao(): Edicao {
  const edicao = useContext(EdicaoContext);
  if (!edicao) throw new Error("useEdicao precisa estar dentro do provedor de edição do projeto");
  return edicao;
}
