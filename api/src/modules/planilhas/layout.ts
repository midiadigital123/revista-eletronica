import type { Bncc, Caderno } from "../../contrato/schemas.js";

/** Colunas fixas por caderno, copiadas dos modelos do núcleo de impressão. */
export interface LayoutCaderno {
  /** Cabeçalhos antes das colunas de nível. */
  inicio: string[];
  /** Cabeçalhos depois das colunas de nível (BNCC). */
  fim: string[];
  /** Texto das células de nível sem conteúdo. */
  vazio: "–" | "...";
  /** Larguras: início, nível, fim. */
  larguras: { inicio: number[]; nivel: number; fim: number[] };
}

export const LAYOUTS: Record<Caderno, LayoutCaderno> = {
  "lingua-portuguesa": {
    inicio: ["Etapa", "Descritor", "Descrição da habilidade", "Pre requisito"],
    fim: ["Praticas de linguagem:", "Objeto de conhecimento:", "Habilidades relacionadas", "Habilidade correspondente"],
    vazio: "–",
    larguras: { inicio: [8, 12, 50, 30], nivel: 28, fim: [30, 30, 30, 40] },
  },
  matematica: {
    inicio: ["Etapa", "Cód. Descritor", "Descritor", "Pre requisito"],
    fim: ["Eixo cognitivo (Saeb):", "Unidade temática:", "Habilidades relacionadas:", "Habilidade correspondente:"],
    vazio: "...",
    larguras: { inicio: [8, 14, 50, 30], nivel: 28, fim: [30, 30, 30, 40] },
  },
};

/** Rótulos dos padrões na aba "Escala". */
export const ROTULOS_PADRAO = ["Padrão 01", "Padrão 02", "Padrão 03", "Padrão 04"] as const;

export const COR_NIVEL = "FFFFFF00";

export const SUFIXO_CADERNO: Record<Caderno, string> = { "lingua-portuguesa": "LP", matematica: "MT" };

/** Valores BNCC na ordem das duas primeiras colunas finais (as outras duas vêm das habilidades). */
export const bnccDoDescritor = (b: Bncc): [string, string] => [b.practices, b.knowledge];
