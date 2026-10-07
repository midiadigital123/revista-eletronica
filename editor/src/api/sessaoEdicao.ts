import { novoId } from "@/lib/utils";

const CHAVE = "revista.sessaoEdicao";

/**
 * Identificador desta aba para o bloqueio de edição (header X-Sessao-Edicao).
 * Fica no sessionStorage: sobrevive a recarregar a página, mas cada aba tem o seu.
 */
export function sessaoEdicao(): string {
  try {
    const existente = sessionStorage.getItem(CHAVE);
    if (existente) return existente;
    const nova = novoId();
    sessionStorage.setItem(CHAVE, nova);
    return nova;
  } catch {
    return (memoria ??= novoId());
  }
}
let memoria: string | undefined;
