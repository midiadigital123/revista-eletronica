import {
  CADERNOS,
  compararAnos,
  type CadernoProjeto,
  type BloqueioPublico,
  type Pagina,
  type Projeto,
  type ProjetoResumo,
} from "../../contrato/schemas.js";
import { naoEncontrado } from "../../errors.js";
import { ProjetoModel, type ProjetoDb, type ProjetoDoc, type ValorPagina } from "./model.js";

/** Filtro de projetos não excluídos. */
export const ativo = (slug: string) => ({ slug, excluidoEm: null });

export async function obterProjeto(slug: string): Promise<ProjetoDoc> {
  const projeto = await ProjetoModel.findOne(ativo(slug));
  if (!projeto) throw naoEncontrado("Projeto");
  return projeto;
}

export async function listarProjetos(): Promise<ProjetoDoc[]> {
  return ProjetoModel.find({ excluidoEm: null }).collation({ locale: "pt" }).sort({ nome: 1 });
}

/** Exclusão lógica: guarda o slug original e libera o slug para reuso. */
export async function excluirProjeto(projeto: ProjetoDoc, agora = new Date()): Promise<void> {
  projeto.slugOriginal = projeto.slug;
  projeto.slug = `${projeto.slug}--excluido-${agora.getTime()}`;
  projeto.excluidoEm = agora;
  projeto.bloqueio = null;
  await projeto.save();
}

// ---------- página (campo Mixed: sempre por estes helpers, que marcam a modificação)

export function definirCampoPagina(projeto: ProjetoDoc, chave: string, valor: ValorPagina): void {
  projeto.pagina = { ...projeto.pagina, [chave]: valor };
  projeto.markModified("pagina");
}

export function removerCampoPagina(projeto: ProjetoDoc, chave: string): void {
  const { [chave]: _removido, ...resto } = projeto.pagina;
  projeto.pagina = resto;
  projeto.markModified("pagina");
}

// ---------- mapeamento para o contrato

export function paraBloqueio(projeto: ProjetoDoc, agora = new Date()): BloqueioPublico | null {
  const b = projeto.bloqueio;
  if (!b || b.expiraEm <= agora) return null;
  return {
    usuarioId: b.usuarioId.toString(),
    nome: b.nome,
    desde: b.desde.toISOString(),
    expiraEm: b.expiraEm.toISOString(),
  };
}

export function paraPagina(projeto: ProjetoDoc): Pagina {
  const pagina: Pagina = {};
  for (const [chave, valor] of Object.entries(projeto.pagina ?? {})) {
    if (typeof valor === "string" || Array.isArray(valor)) pagina[chave] = valor;
    else pagina[chave] = { nome: valor.nome, mime: valor.mime, tamanho: valor.tamanho };
  }
  return pagina;
}

/**
 * Cadernos na ordem de CADERNOS; anos em ordem EF → EM (por número);
 * descritores em ordem de código. Cópia solta do documento (pode ser editada e regravada).
 */
export function paraCadernos(projeto: ProjetoDoc): CadernoProjeto[] {
  const { cadernos } = projeto.toObject<ProjetoDb>({ versionKey: false });
  return cadernos
    .sort((a, b) => CADERNOS.indexOf(a.id) - CADERNOS.indexOf(b.id))
    .map(({ id, anos }) => ({
      id,
      anos: anos
        .sort((a, b) => compararAnos(a.ano, b.ano))
        .map((ano) => ({
          ...ano,
          descritores: [...ano.descritores].sort((x, y) => x.codigo.localeCompare(y.codigo)),
        })),
    }));
}

export function paraProjeto(projeto: ProjetoDoc): Projeto {
  return {
    slug: projeto.slug,
    nome: projeto.nome,
    pagina: paraPagina(projeto),
    cadernos: paraCadernos(projeto),
    bloqueio: paraBloqueio(projeto),
    criadoEm: projeto.criadoEm.toISOString(),
    atualizadoEm: projeto.atualizadoEm.toISOString(),
  };
}

export function paraResumo(projeto: ProjetoDoc): ProjetoResumo {
  return {
    slug: projeto.slug,
    nome: projeto.nome,
    cadernos: paraCadernos(projeto).map(({ id, anos }) => ({ id, anos: anos.map((a) => a.ano) })),
    atualizadoEm: projeto.atualizadoEm.toISOString(),
    bloqueio: paraBloqueio(projeto),
  };
}
