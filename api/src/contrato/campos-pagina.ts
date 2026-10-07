// GERADO por scripts/sync-contrato.mjs — edite em /contrato, não aqui.
/**
 * Campos da página da revista que cada projeto pode personalizar.
 *
 * Para tornar um novo trecho da revista editável:
 *   1. adicione uma entrada aqui;
 *   2. use `{{pagina.<chave>}}` no template `revista/escala.hbs`
 *      (com `{{#if}}…{{else}}<padrão>{{/if}}` para manter o texto original);
 *   3. rode `node scripts/sync-contrato.mjs`.
 * API (validação) e editor (formulário) se ajustam sozinhos.
 */

export type TipoCampoPagina = "texto" | "paragrafos" | "imagem";

export interface CampoPagina {
  chave: string;
  rotulo: string;
  tipo: TipoCampoPagina;
  /** Limite de caracteres (texto) ou de cada parágrafo (paragrafos). */
  max?: number;
  ajuda?: string;
}

export const CAMPOS_PAGINA = [
  {
    chave: "heroTitulo",
    rotulo: "Título do topo",
    tipo: "texto",
    max: 200,
  },
  {
    chave: "heroImagem",
    rotulo: "Imagem do topo",
    tipo: "imagem",
    ajuda: "PNG, JPEG ou WebP, até 5 MB.",
  },
  {
    chave: "introParagrafos",
    rotulo: "Textos de introdução",
    tipo: "paragrafos",
    max: 3000,
  },
] as const satisfies readonly CampoPagina[];

export type ChaveCampoPagina = (typeof CAMPOS_PAGINA)[number]["chave"];

type CamposDoTipo<T extends TipoCampoPagina> = Extract<
  (typeof CAMPOS_PAGINA)[number],
  { tipo: T }
>["chave"];

export type ChaveTexto = CamposDoTipo<"texto">;
export type ChaveParagrafos = CamposDoTipo<"paragrafos">;
export type ChaveImagem = CamposDoTipo<"imagem">;

export const camposDoTipo = (tipo: TipoCampoPagina): CampoPagina[] =>
  CAMPOS_PAGINA.filter((c) => c.tipo === tipo);

export const buscarCampo = (chave: string): CampoPagina | undefined =>
  CAMPOS_PAGINA.find((c) => c.chave === chave);
