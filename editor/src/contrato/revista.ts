// GERADO por scripts/sync-contrato.mjs — edite em /contrato, não aqui.
/**
 * Conversão entre o formato da revista (descritores.json + cortes + pagina) e
 * a estrutura do projeto (anos[] com descritores[]). Funções puras.
 */
import {
  compararAnos,
  CORTES_PADRAO,
  DescritorCampos,
  type AnoProjeto,
  type Pagina,
  type PaginaTextos,
  type Revista,
  type RevistaAno,
} from "./schemas.js";

const CHAVES_DO_ANO = new Set(["scaleRange", "cortes"]);

/** Revista (já validada pelo schema Revista) → anos do projeto, em ordem compararAnos (EF → EM). */
export function anosDaRevista(revista: Revista): AnoProjeto[] {
  const anos = Object.keys(revista)
    .filter((k) => k !== "pagina")
    .sort(compararAnos);
  return anos.flatMap((ano) => {
    const dados = revista[ano] as RevistaAno | undefined;
    if (!dados) return [];
    const descritores = Object.entries(dados as RevistaAno)
      .filter(([chave]) => !CHAVES_DO_ANO.has(chave))
      .map(([codigo, campos]) => ({ codigo, ...DescritorCampos.parse(campos) }))
      .sort((a, b) => a.codigo.localeCompare(b.codigo));
    return [
      {
        ano,
        scaleRange: dados.scaleRange,
        cortes: dados.cortes ?? { ...CORTES_PADRAO },
        descritores,
      },
    ];
  });
}

/** Só os campos de texto/parágrafos da página (imagens não vão no JSON). */
/** Aceita a Pagina da API (com imagens) ou já só os textos. */
type PaginaQualquer = Pagina | PaginaTextos;

export function textosDaPagina(pagina: PaginaQualquer): PaginaTextos {
  return Object.fromEntries(
    Object.entries(pagina).filter(
      ([, v]) => typeof v === "string" || (Array.isArray(v) && v.length > 0),
    ),
  ) as PaginaTextos;
}

/** Anos do projeto → formato da revista (exportar JSON e bloco #dados-revista). */
export function revistaDosAnos(anos: readonly AnoProjeto[], pagina: PaginaQualquer): Revista {
  const revista: Record<string, unknown> = { pagina: textosDaPagina(pagina) };
  for (const { ano, scaleRange, cortes, descritores } of anos) {
    const dados: Record<string, unknown> = { scaleRange, cortes };
    for (const { codigo, ...campos } of [...descritores].sort((a, b) =>
      a.codigo.localeCompare(b.codigo),
    ))
      dados[codigo] = campos;
    revista[ano] = dados;
  }
  return revista as Revista;
}
