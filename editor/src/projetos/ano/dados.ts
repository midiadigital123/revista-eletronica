import { useParams } from "react-router";
import {
  Ano,
  Caderno,
  compararAnos,
  rotuloAno,
  rotuloCaderno,
  type AnoProjeto,
  type Descritor,
  type Padrao,
  type Projeto,
} from "../../contrato/schemas";
import { useProjeto } from "../consultas";
import { useEdicao } from "../edicao";

/** Utilidades das telas de ano: caminhos, atualização do cache e erros. */

export const caminhoProjeto = (slug: string) => `/projetos/${encodeURIComponent(slug)}`;
export const caminhoAno = (slug: string, caderno: Caderno, ano: Ano) =>
  `${caminhoProjeto(slug)}/${caderno}/ano/${ano}`;
export const caminhoDescritor = (slug: string, caderno: Caderno, ano: Ano, codigo: string) =>
  `${caminhoAno(slug, caderno, ano)}/${codigo}`;

/** "5º EF · Matemática": nas descrições de salvamento (chave das falhas e dos não salvos). */
export const rotuloAnoCaderno = (caderno: Caderno, ano: Ano) =>
  `${rotuloAno(ano)} · ${rotuloCaderno(caderno)}`;

export const rotuloPadrao = (padrao: Padrao) => `Padrão 0${padrao.slice(-1)}`;

const porCodigo = (a: Descritor, b: Descritor) => a.codigo.localeCompare(b.codigo);

/** Projeto com os anos do caderno trocados por `f` (mantém a ordem das etapas: EF antes de EM, depois pelo número). */
export const trocarAnos = (
  p: Projeto,
  caderno: Caderno,
  f: (anos: AnoProjeto[]) => AnoProjeto[],
): Projeto => ({
  ...p,
  cadernos: p.cadernos.map((c) =>
    c.id === caderno ? { ...c, anos: f(c.anos).sort((a, b) => compararAnos(a.ano, b.ano)) } : c,
  ),
});

export const trocarAno = (
  p: Projeto,
  caderno: Caderno,
  ano: Ano,
  f: (a: AnoProjeto) => AnoProjeto,
): Projeto => trocarAnos(p, caderno, (anos) => anos.map((a) => (a.ano === ano ? f(a) : a)));

/** Descritores do ano trocados por `f` (mantém a ordem por código). */
export const trocarDescritores = (
  p: Projeto,
  caderno: Caderno,
  ano: Ano,
  f: (ds: Descritor[]) => Descritor[],
): Projeto =>
  trocarAno(p, caderno, ano, (a) => ({ ...a, descritores: f(a.descritores).sort(porCodigo) }));

/** Troca o descritor `codigo` pelo resultado de `f` (que recebe a versão atual do cache). */
export const trocarDescritor = (
  p: Projeto,
  caderno: Caderno,
  ano: Ano,
  codigo: string,
  f: (d: Descritor) => Descritor,
): Projeto =>
  trocarDescritores(p, caderno, ano, (ds) => ds.map((d) => (d.codigo === codigo ? f(d) : d)));

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

/**
 * Projeto, caderno e ano (da URL) e os dados no cache. `cadernoProjeto`/`anoProjeto`
 * são undefined se não existirem no projeto.
 */
export function useAnoAtual() {
  const { slug } = useEdicao();
  const params = useParams();
  const consulta = useProjeto(slug);
  const caderno = Caderno.safeParse(params.caderno).data;
  const ano = Ano.safeParse(params.ano).data;
  const cadernoProjeto = consulta.data?.cadernos.find((c) => c.id === caderno);
  const anoProjeto = cadernoProjeto?.anos.find((a) => a.ano === ano);
  return {
    slug,
    consulta,
    projeto: consulta.data,
    caderno,
    cadernoProjeto,
    ano,
    anoProjeto,
    codigo: params.codigo,
  };
}
