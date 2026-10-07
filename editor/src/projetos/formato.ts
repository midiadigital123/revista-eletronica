/** Formatação e utilidades pequenas das telas de projeto. */

/** "14:05" no fuso local. */
export const horaCurta = (data: Date | string) =>
  new Date(data).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });

const relativo = new Intl.RelativeTimeFormat("pt-BR", { numeric: "auto" });
const UNIDADES: [Intl.RelativeTimeFormatUnit, number][] = [
  ["year", 365 * 24 * 3600],
  ["month", 30 * 24 * 3600],
  ["day", 24 * 3600],
  ["hour", 3600],
  ["minute", 60],
];

/** "há 5 minutos", "ontem", "agora mesmo". */
export function tempoRelativo(data: string, agora = Date.now()): string {
  const segundos = Math.round((Date.parse(data) - agora) / 1000);
  for (const [unidade, tamanho] of UNIDADES)
    if (Math.abs(segundos) >= tamanho) return relativo.format(Math.round(segundos / tamanho), unidade);
  return "agora mesmo";
}

/** Sugestão de slug a partir do nome: "São Paulo 2026" → "sao-paulo-2026". */
export const sugerirSlug = (nome: string) =>
  nome
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60)
    .replace(/-+$/, "");

/** Mensagem de erro para o usuário a partir de qualquer exceção. */
export const mensagemDeErro = (e: unknown) => (e instanceof Error ? e.message : "Algo deu errado");
