import { HEADER_SESSAO_EDICAO, type BloqueioPublico, type ErroApi } from "../contrato/schemas";
import { sessaoEdicao } from "./sessaoEdicao";

/** Erro HTTP da API no formato ErroApi do contrato. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly corpo: ErroApi,
  ) {
    super(corpo.erro);
    this.name = "ApiError";
  }
  get campo(): string | undefined {
    return this.corpo.campo;
  }
  get bloqueio(): BloqueioPublico | null | undefined {
    return this.corpo.bloqueio;
  }
}

export const ehErroApi = (e: unknown, status?: number): e is ApiError =>
  e instanceof ApiError && (status === undefined || e.status === status);

interface Opcoes {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  /** Objeto (vira JSON) ou FormData (upload). */
  body?: unknown;
  signal?: AbortSignal;
  /** Mantém a requisição viva ao fechar a aba (liberar bloqueio no pagehide). */
  keepalive?: boolean;
}

/** Chamada à API: cookies de sessão, header de edição e erros tipados. 204 → undefined. */
export async function api<T>(caminho: string, opcoes: Opcoes = {}): Promise<T> {
  const { method = "GET", body, signal, keepalive } = opcoes;
  const headers: Record<string, string> = { [HEADER_SESSAO_EDICAO]: sessaoEdicao() };
  let corpo: BodyInit | undefined;
  if (body instanceof FormData) corpo = body;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    corpo = JSON.stringify(body);
  }

  const resposta = await fetch(`/api${caminho}`, {
    method,
    headers,
    body: corpo,
    credentials: "include",
    signal,
    keepalive,
  });

  if (resposta.status === 204) return undefined as T;
  const dados: unknown = resposta.headers.get("content-type")?.includes("json")
    ? await resposta.json()
    : undefined;
  if (!resposta.ok)
    throw new ApiError(
      resposta.status,
      (dados as ErroApi) ?? {
        // 413 sem JSON vem do proxy (nginx), antes de chegar à API.
        erro:
          resposta.status === 413
            ? "O arquivo é grande demais para o servidor."
            : `Erro ${resposta.status}`,
      },
    );
  return dados as T;
}

/** URL absoluta de um recurso da API (preview, zip, imagens). */
export const urlApi = (caminho: string) => `/api${caminho}`;
