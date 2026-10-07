import { useParams } from "react-router";
import {
  Ano,
  ANOS,
  type AnoProjeto,
  type Descritor,
  type Padrao,
  type Projeto,
} from "../../contrato/schemas";
import { useProjeto } from "../consultas";
import { useEdicao } from "../edicao";

/** Utilidades das telas de ano: caminhos, atualização do cache e erros. */

export const caminhoProjeto = (slug: string) => `/projetos/${encodeURIComponent(slug)}`;
export const caminhoAno = (slug: string, ano: Ano) => `${caminhoProjeto(slug)}/ano/${ano}`;
export const caminhoDescritor = (slug: string, ano: Ano, codigo: string) =>
  `${caminhoAno(slug, ano)}/${codigo}`;

export const rotuloPadrao = (padrao: Padrao) => `Padrão 0${padrao.slice(-1)}`;

const ordemAno = (a: AnoProjeto) => ANOS.indexOf(a.ano);
const porCodigo = (a: Descritor, b: Descritor) => a.codigo.localeCompare(b.codigo);

/** Projeto com os anos trocados por `f` (mantém a ordem 5ef/9ef/3em). */
export const trocarAnos = (p: Projeto, f: (anos: AnoProjeto[]) => AnoProjeto[]): Projeto => ({
  ...p,
  anos: f(p.anos).sort((a, b) => ordemAno(a) - ordemAno(b)),
});

export const trocarAno = (p: Projeto, ano: Ano, f: (a: AnoProjeto) => AnoProjeto): Projeto =>
  trocarAnos(p, (anos) => anos.map((a) => (a.ano === ano ? f(a) : a)));

/** Descritores do ano trocados por `f` (mantém a ordem por código). */
export const trocarDescritores = (
  p: Projeto,
  ano: Ano,
  f: (ds: Descritor[]) => Descritor[],
): Projeto => trocarAno(p, ano, (a) => ({ ...a, descritores: f(a.descritores).sort(porCodigo) }));

/** Troca o descritor `codigo` pelo resultado de `f` (que recebe a versão atual do cache). */
export const trocarDescritor = (
  p: Projeto,
  ano: Ano,
  codigo: string,
  f: (d: Descritor) => Descritor,
): Projeto => trocarDescritores(p, ano, (ds) => ds.map((d) => (d.codigo === codigo ? f(d) : d)));

/** Primeiro código livre de D01 a D99 (undefined se todos existem). */
export function proximoCodigo(descritores: readonly Descritor[]): string | undefined {
  const usados = new Set(descritores.map((d) => d.codigo));
  for (let i = 1; i <= 99; i++) {
    const codigo = `D${String(i).padStart(2, "0")}`;
    if (!usados.has(codigo)) return codigo;
  }
  return undefined;
}

/** Mensagem de erro para o usuário (ApiError já traz `erro` como message). */
export const mensagemDeErro = (e: unknown) =>
  e instanceof Error && e.message ? e.message : "Não foi possível salvar";

/** Projeto, ano (da URL) e o ano no cache. `anoProjeto` é undefined se não existir. */
export function useAnoAtual() {
  const { slug } = useEdicao();
  const params = useParams();
  const consulta = useProjeto(slug);
  const ano = Ano.safeParse(params.ano).data;
  const anoProjeto = consulta.data?.anos.find((a) => a.ano === ano);
  return { slug, consulta, projeto: consulta.data, ano, anoProjeto, codigo: params.codigo };
}
