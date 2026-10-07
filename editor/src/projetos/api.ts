import type { z } from "zod";
import type {
  Ano,
  AnoProjeto,
  AtualizarAnoEntrada,
  AtualizarDescritorEntrada,
  AtualizarProjetoEntrada,
  BloqueioPublico,
  CriarAnoEntrada,
  CriarDescritorEntrada,
  CriarProjetoEntrada,
  Descritor,
  LinhaEscala,
  Padrao,
  Pagina,
  PaginaPatch,
  Projeto,
  ProjetoResumo,
  Revista,
} from "../contrato/schemas";
import type { CampoPagina } from "../contrato/campos-pagina";
import { api, urlApi } from "../api/client";

type Entrada<T extends z.ZodType> = z.input<T>;

const p = (slug: string) => `/projetos/${encodeURIComponent(slug)}`;
const pa = (slug: string, ano: Ano) => `${p(slug)}/anos/${ano}`;
const pd = (slug: string, ano: Ano, codigo: string) => `${pa(slug, ano)}/descritores/${codigo}`;

/** Todas as rotas de projeto do contrato (docs/contrato.md). */
export const projetosApi = {
  listar: () => api<ProjetoResumo[]>("/projetos"),
  obter: (slug: string) => api<Projeto>(p(slug)),
  /** Quem cria já recebe o bloqueio de edição (mesma aba). */
  criar: (dados: Entrada<typeof CriarProjetoEntrada>) =>
    api<Projeto>("/projetos", { method: "POST", body: dados }),
  atualizar: (slug: string, dados: Entrada<typeof AtualizarProjetoEntrada>) =>
    api<Projeto>(p(slug), { method: "PATCH", body: dados }),
  excluir: (slug: string) => api<void>(p(slug), { method: "DELETE" }),
  exportar: (slug: string) => api<Revista>(`${p(slug)}/revista`),

  adquirirBloqueio: (slug: string) =>
    api<BloqueioPublico>(`${p(slug)}/bloqueio`, { method: "POST" }),
  renovarBloqueio: (slug: string) =>
    api<BloqueioPublico>(`${p(slug)}/bloqueio`, { method: "PUT" }),
  liberarBloqueio: (slug: string, opcoes: { keepalive?: boolean } = {}) =>
    api<void>(`${p(slug)}/bloqueio`, { method: "DELETE", ...opcoes }),

  camposPagina: () => api<CampoPagina[]>("/pagina/campos"),
  atualizarPagina: (slug: string, patch: Entrada<typeof PaginaPatch>) =>
    api<Pagina>(`${p(slug)}/pagina`, { method: "PATCH", body: patch }),
  enviarImagem: (slug: string, chave: string, arquivo: File) => {
    const corpo = new FormData();
    corpo.append("arquivo", arquivo);
    return api<Pagina>(`${p(slug)}/pagina/${chave}/imagem`, { method: "PUT", body: corpo });
  },
  removerImagem: (slug: string, chave: string) =>
    api<Pagina>(`${p(slug)}/pagina/${chave}/imagem`, { method: "DELETE" }),

  criarAno: (slug: string, dados: Entrada<typeof CriarAnoEntrada>) =>
    api<AnoProjeto>(`${p(slug)}/anos`, { method: "POST", body: dados }),
  atualizarAno: (slug: string, ano: Ano, dados: Entrada<typeof AtualizarAnoEntrada>) =>
    api<AnoProjeto>(pa(slug, ano), { method: "PATCH", body: dados }),
  excluirAno: (slug: string, ano: Ano) => api<void>(pa(slug, ano), { method: "DELETE" }),

  criarDescritor: (slug: string, ano: Ano, dados: Entrada<typeof CriarDescritorEntrada>) =>
    api<Descritor>(`${pa(slug, ano)}/descritores`, { method: "POST", body: dados }),
  atualizarDescritor: (
    slug: string,
    ano: Ano,
    codigo: string,
    dados: Entrada<typeof AtualizarDescritorEntrada>,
  ) => api<Descritor>(pd(slug, ano, codigo), { method: "PATCH", body: dados }),
  excluirDescritor: (slug: string, ano: Ano, codigo: string) =>
    api<void>(pd(slug, ano, codigo), { method: "DELETE" }),
  salvarEscala: (slug: string, ano: Ano, codigo: string, padrao: Padrao, linhas: LinhaEscala[]) =>
    api<LinhaEscala[]>(`${pd(slug, ano, codigo)}/escala/${padrao}`, {
      method: "PUT",
      body: linhas,
    }),

  urlImagem: (slug: string, chave: string, versao?: string) =>
    urlApi(`${p(slug)}/pagina/${chave}/imagem${versao ? `?v=${encodeURIComponent(versao)}` : ""}`),
  urlPreview: (slug: string) => urlApi(`${p(slug)}/preview/`),
  urlPacote: (slug: string) => urlApi(`${p(slug)}/pacote.zip`),
};
