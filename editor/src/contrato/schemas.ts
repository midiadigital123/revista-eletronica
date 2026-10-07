// GERADO por scripts/sync-contrato.mjs — edite em /contrato, não aqui.
/**
 * Contrato entre API e editor: constantes, schemas de entrada/saída e regras
 * de domínio. Fonte única em /contrato; cópias geradas em api/src/contrato e
 * editor/src/contrato por `node scripts/sync-contrato.mjs` (não edite as cópias).
 * Documentação das rotas: docs/contrato.md.
 */
import { z } from "zod";
import { CAMPOS_PAGINA } from "./campos-pagina.js";

// ==========================================
// CONSTANTES
// ==========================================

/** Etapas sugeridas por padrão (projeto vazio, atalhos da UI). Qualquer `<n>ef`/`<n>em` é aceita. */
export const ANOS_PADRAO = ["5ef", "9ef", "3em"] as const;
/** Todas as etapas válidas, em ordem: 1ef…9ef, 1em…3em. */
export const ETAPAS = [
  ...Array.from({ length: 9 }, (_, i) => `${i + 1}ef`),
  ...Array.from({ length: 3 }, (_, i) => `${i + 1}em`),
];
/** Formato da chave de etapa: número + ef/em (ex.: 2ef, 3em). A faixa do EM (1–3) é checada em `Ano`. */
export const ANO_REGEX = /^[1-9](ef|em)$/;
export const PADROES = ["padrao-1", "padrao-2", "padrao-3", "padrao-4"] as const;
/** Padrões cujo início é marcado por um corte (o padrão 4 vai até scaleRange.max). */
export const PADROES_COM_CORTE = ["padrao-1", "padrao-2", "padrao-3"] as const;

export const FAIXA_PADRAO = { min: 0, max: 500 } as const;
export const CORTES_PADRAO = {
  "padrao-1": 125,
  "padrao-2": 250,
  "padrao-3": 375,
} as const;

/** Conteúdo de linha da escala sem item associado (convenção da revista). */
export const CONTEUDO_VAZIO = "---";

export const IMAGEM_MIMES = ["image/png", "image/jpeg", "image/webp"] as const;
export const IMAGEM_MAX_BYTES = 5 * 1024 * 1024;

export const HEADER_SESSAO_EDICAO = "X-Sessao-Edicao";
export const BLOQUEIO_TTL_MS = 2 * 60 * 1000;
export const BLOQUEIO_HEARTBEAT_MS = 30 * 1000;
export const BLOQUEIO_INATIVIDADE_MS = 15 * 60 * 1000;

// ==========================================
// PRIMITIVOS
// ==========================================

const texto = (max: number) => z.string().trim().max(max);
/** Lista de textos: itens vazios após trim são descartados. */
const listaTextos = (max: number) =>
  z.array(texto(max)).transform((itens) => itens.filter(Boolean));

export const Ano = z
  .string()
  .regex(ANO_REGEX, { error: "Use número + ef/em (ex.: 2ef, 3em)" })
  .refine((a) => !a.endsWith("em") || Number(a[0]) <= 3, {
    error: "No Ensino Médio use 1em, 2em ou 3em",
  });
export const Padrao = z.enum(PADROES);
export const Codigo = z
  .string()
  .regex(/^D\d{2}$/, { error: "Use D seguido de 2 dígitos (ex.: D07)" });
export const Slug = z
  .string()
  .max(60)
  .regex(/^[a-z0-9]+(-[a-z0-9]+)*$/, {
    error: "Use letras minúsculas, números e hífen (ex.: sp-2026)",
  });
export const Email = z.email().trim().toLowerCase();
export const Senha = z.string().min(8, { error: "Mínimo de 8 caracteres" }).max(200);
export const Perfil = z.enum(["admin", "editor"]);
export const ObjectIdTexto = z.string().regex(/^[a-f0-9]{24}$/);

/** Partes de uma chave de etapa ("5ef" → 5, "ef"); null se fora do formato. */
function etapa(ano: string): { n: number; nivel: "ef" | "em" } | null {
  return ANO_REGEX.test(ano) ? { n: Number(ano.slice(0, -2)), nivel: ano.slice(-2) as "ef" | "em" } : null;
}

/** Rótulo curto da etapa: "5º EF", "3ª EM". Chave fora do formato volta como veio. */
export function rotuloAno(ano: string): string {
  const e = etapa(ano);
  if (!e) return ano;
  return e.nivel === "ef" ? `${e.n}º EF` : `${e.n}ª EM`;
}

/** Rótulo longo: "5º Ano do Ensino Fundamental", "3ª Série do Ensino Médio". */
export function rotuloAnoLongo(ano: string): string {
  const e = etapa(ano);
  if (!e) return ano;
  return e.nivel === "ef" ? `${e.n}º Ano do Ensino Fundamental` : `${e.n}ª Série do Ensino Médio`;
}

/** Ordem das etapas: EF antes de EM, depois pelo número; fora do formato, no fim por texto. */
export function compararAnos(a: string, b: string): number {
  const ea = etapa(a);
  const eb = etapa(b);
  if (ea && eb) return ea.nivel.localeCompare(eb.nivel) || ea.n - eb.n;
  if (ea || eb) return ea ? -1 : 1;
  return a.localeCompare(b);
}

// ==========================================
// ESCALA, ANO, DESCRITOR
// ==========================================

export const ScaleRange = z
  .strictObject({ min: z.int(), max: z.int() })
  .refine((f) => f.min < f.max, {
    error: "O mínimo deve ser menor que o máximo",
    path: ["max"],
  });

export const Cortes = z.strictObject({
  "padrao-1": z.int(),
  "padrao-2": z.int(),
  "padrao-3": z.int(),
});

export const LinhaEscala = z.strictObject({
  level: z.number(),
  content: texto(5000).transform((c) => c || CONTEUDO_VAZIO),
});

/** Linhas de um padrão; sempre devolvidas em ordem decrescente de nível. */
export const LinhasPadrao = z
  .array(LinhaEscala)
  .max(50)
  .transform((linhas) => [...linhas].sort((a, b) => b.level - a.level));

/** Escala de um descritor; padrões ausentes valem lista vazia. */
export const Escala = z.strictObject({
  "padrao-1": LinhasPadrao.default(() => []),
  "padrao-2": LinhasPadrao.default(() => []),
  "padrao-3": LinhasPadrao.default(() => []),
  "padrao-4": LinhasPadrao.default(() => []),
});

export const Bncc = z.strictObject({
  practices: texto(2000),
  knowledge: texto(2000),
  skills: listaTextos(500),
});

const escalaVazia = () => ({ "padrao-1": [], "padrao-2": [], "padrao-3": [], "padrao-4": [] });

/** Campos de um descritor (sem o código). Defaults permitem criar vazio. */
export const DescritorCampos = z.strictObject({
  topic: texto(300).default(""),
  description: texto(5000).default(""),
  prerequisites: listaTextos(1000).default(() => []),
  bncc: Bncc.default(() => ({ practices: "", knowledge: "", skills: [] })),
  scale: Escala.default(escalaVazia),
});

export const Descritor = DescritorCampos.extend({ codigo: Codigo });

export const AnoProjeto = z.strictObject({
  ano: Ano,
  scaleRange: ScaleRange,
  cortes: Cortes,
  descritores: z.array(Descritor),
});

// ==========================================
// REGRAS QUE DEPENDEM DE CONTEXTO
// (a API responde 400 com elas; o editor valida inline com elas)
// ==========================================

export interface Problema {
  /** Caminho do campo, ex.: "cortes.padrao-2" ou "descritores.D03.scale.padrao-1.0.level". */
  campo: string;
  erro: string;
}

interface Faixa {
  min: number;
  max: number;
}

export function problemasDosCortes(cortes: Cortes, faixa: Faixa): Problema[] {
  const problemas: Problema[] = [];
  let anterior = faixa.min;
  for (const p of PADROES_COM_CORTE) {
    if (cortes[p] <= anterior || cortes[p] >= faixa.max)
      problemas.push({
        campo: `cortes.${p}`,
        erro: `Os cortes devem crescer entre ${faixa.min} e ${faixa.max}`,
      });
    anterior = cortes[p];
  }
  return problemas;
}

export function problemasDasLinhas(
  linhas: readonly { level: number }[],
  faixa: Faixa,
  prefixo: string,
): Problema[] {
  return linhas.flatMap((l, i) =>
    l.level < faixa.min || l.level > faixa.max
      ? [{ campo: `${prefixo}.${i}.level`, erro: `Nível fora da escala (${faixa.min}–${faixa.max})` }]
      : [],
  );
}

/** Valida um ano inteiro: cortes na faixa, códigos únicos e todos os níveis na faixa. */
export function problemasDoAno(ano: AnoProjeto): Problema[] {
  const problemas = problemasDosCortes(ano.cortes, ano.scaleRange);
  const vistos = new Set<string>();
  for (const d of ano.descritores) {
    if (vistos.has(d.codigo))
      problemas.push({ campo: `descritores.${d.codigo}`, erro: "Código repetido no ano" });
    vistos.add(d.codigo);
    for (const p of PADROES)
      problemas.push(
        ...problemasDasLinhas(d.scale[p], ano.scaleRange, `descritores.${d.codigo}.scale.${p}`),
      );
  }
  return problemas;
}

/**
 * Padrão ao qual um nível pertence segundo os cortes. Só gera aviso no editor:
 * a revista aceita níveis fora do intervalo do próprio padrão.
 */
export function padraoDoNivel(level: number, cortes: Cortes): Padrao {
  if (level >= cortes["padrao-3"]) return "padrao-4";
  if (level >= cortes["padrao-2"]) return "padrao-3";
  if (level >= cortes["padrao-1"]) return "padrao-2";
  return "padrao-1";
}

// ==========================================
// PÁGINA
// ==========================================

export const ImagemPagina = z.strictObject({
  nome: z.string(),
  mime: z.enum(IMAGEM_MIMES),
  tamanho: z.int(),
});

/** Nome do arquivo de uma imagem de página (no zip e no preview: `arquivos/<nome>`). */
export const nomeArquivoImagem = (chave: string, mime: (typeof IMAGEM_MIMES)[number]) =>
  `${chave}.${mime === "image/jpeg" ? "jpg" : mime.split("/")[1]}`;

/** Página como a API devolve: textos + metadados das imagens enviadas. */
export const Pagina = z.record(
  z.string(),
  z.union([z.string(), z.array(z.string()), ImagemPagina]),
);

type CampoPatch = z.ZodOptional<z.ZodNullable<z.ZodType<string | string[], string | string[]>>>;
type CampoTexto = z.ZodOptional<z.ZodType<string | string[], string | string[]>>;

/**
 * PATCH da página: só campos de texto/parágrafos (imagens vão por upload);
 * `null`, "" ou [] voltam ao padrão do template. Gerado de CAMPOS_PAGINA.
 */
export const PaginaPatch = z.strictObject(
  Object.fromEntries(
    CAMPOS_PAGINA.flatMap((c): [string, CampoPatch][] => {
      const max = "max" in c ? c.max : 2000;
      if (c.tipo === "texto") return [[c.chave, texto(max).nullable().optional()]];
      if (c.tipo === "paragrafos") return [[c.chave, listaTextos(max).nullable().optional()]];
      return [];
    }),
  ),
);

/** Textos da página no formato da revista (sem null): importar/exportar e template. */
export const PaginaTextos = z.strictObject(
  Object.fromEntries(
    CAMPOS_PAGINA.flatMap((c): [string, CampoTexto][] => {
      const max = "max" in c ? c.max : 2000;
      if (c.tipo === "texto") return [[c.chave, texto(max).optional()]];
      if (c.tipo === "paragrafos") return [[c.chave, listaTextos(max).optional()]];
      return [];
    }),
  ),
);

// ==========================================
// FORMATO DA REVISTA
// Importar/exportar e o bloco #dados-revista do template.
// É o descritores.json original + `cortes` + `pagina` (só textos).
// ==========================================

/** Um ano no formato da revista: scaleRange, cortes e um campo por código de descritor. */
export type RevistaAno = {
  scaleRange: ScaleRange;
  cortes: Cortes;
} & { [codigo: string]: z.output<typeof DescritorCampos> | ScaleRange | Cortes };

export const RevistaAno: z.ZodType<RevistaAno, unknown> = z
  .record(z.string(), z.unknown())
  .transform((ano, ctx) => {
    const { scaleRange, cortes, ...descritores } = ano;
    const base = z
      .object({ scaleRange: ScaleRange, cortes: Cortes.default(() => ({ ...CORTES_PADRAO })) })
      .safeParse({ scaleRange, cortes });
    if (!base.success) {
      for (const i of base.error.issues) ctx.addIssue({ ...i, code: "custom", message: i.message });
      return z.NEVER;
    }
    const saida: Record<string, unknown> = { ...base.data };
    for (const [codigo, campos] of Object.entries(descritores)) {
      if (!Codigo.safeParse(codigo).success) {
        ctx.addIssue({ code: "custom", path: [codigo], message: "Código de descritor inválido" });
        continue;
      }
      const d = DescritorCampos.safeParse(campos);
      if (!d.success)
        for (const i of d.error.issues)
          ctx.addIssue({ code: "custom", path: [codigo, ...i.path], message: i.message });
      else saida[codigo] = d.data;
    }
    return saida as RevistaAno;
  });

/** `pagina` + uma chave por etapa (`<n>ef`/`<n>em`) com os dados do ano. */
export const Revista = z
  .object({ pagina: PaginaTextos.optional() })
  .catchall(RevistaAno)
  .superRefine((r, ctx) => {
    const anos = Object.keys(r).filter((k) => k !== "pagina");
    for (const k of anos) {
      const ano = Ano.safeParse(k);
      if (!ano.success)
        ctx.addIssue({ code: "custom", path: [k], message: `Etapa inválida: ${ano.error.issues[0]?.message}` });
    }
    if (!anos.length) ctx.addIssue({ code: "custom", message: "A revista precisa de ao menos um ano" });
  });

// ==========================================
// ENTRADAS DAS ROTAS
// ==========================================

const naoVazio = { error: "Nada para atualizar" };

export const LoginEntrada = z.strictObject({ email: Email, senha: z.string().min(1) });

export const CriarUsuarioEntrada = z.strictObject({
  email: Email,
  nome: texto(120).min(1),
  senha: Senha,
  perfil: Perfil,
});

export const AtualizarUsuarioEntrada = z
  .strictObject({
    nome: texto(120).min(1).optional(),
    perfil: Perfil.optional(),
    ativo: z.boolean().optional(),
    senha: Senha.optional(),
  })
  .refine((v) => Object.keys(v).length > 0, naoVazio);

export const OrigemProjeto = z.discriminatedUnion("tipo", [
  z.strictObject({ tipo: z.literal("vazio"), anos: z.array(Ano).min(1).default([...ANOS_PADRAO]) }),
  z.strictObject({ tipo: z.literal("importar"), revista: Revista }),
  z.strictObject({ tipo: z.literal("copiar"), de: Slug }),
]);

export const CriarProjetoEntrada = z.strictObject({
  slug: Slug,
  nome: texto(120).min(1),
  origem: OrigemProjeto,
});

export const AtualizarProjetoEntrada = z
  .strictObject({ slug: Slug.optional(), nome: texto(120).min(1).optional() })
  .refine((v) => Object.keys(v).length > 0, naoVazio);

export const CriarAnoEntrada = z.strictObject({
  ano: Ano,
  scaleRange: ScaleRange.default({ ...FAIXA_PADRAO }),
  cortes: Cortes.default({ ...CORTES_PADRAO }),
});

export const AtualizarAnoEntrada = z
  .strictObject({ scaleRange: ScaleRange.optional(), cortes: Cortes.optional() })
  .refine((v) => Object.keys(v).length > 0, naoVazio);

export const CriarDescritorEntrada = Descritor;

export const AtualizarDescritorEntrada = z
  .strictObject({
    codigo: Codigo.optional(),
    topic: texto(300).optional(),
    description: texto(5000).optional(),
    prerequisites: listaTextos(1000).optional(),
    bncc: Bncc.partial().optional(),
  })
  .refine((v) => Object.keys(v).length > 0, naoVazio);

export const ParamsProjeto = z.strictObject({ slug: Slug });
export const ParamsAno = ParamsProjeto.extend({ ano: Ano });
export const ParamsDescritor = ParamsAno.extend({ codigo: Codigo });
export const ParamsPadrao = ParamsDescritor.extend({ padrao: Padrao });
export const ParamsImagem = ParamsProjeto.extend({ chave: z.string() });
export const ParamsUsuario = z.strictObject({ id: ObjectIdTexto });

// ==========================================
// SAÍDAS
// ==========================================

export const Usuario = z.strictObject({
  id: z.string(),
  email: z.string(),
  nome: z.string(),
  perfil: Perfil,
  ativo: z.boolean(),
});

export const BloqueioPublico = z.strictObject({
  usuarioId: z.string(),
  nome: z.string(),
  desde: z.iso.datetime(),
  expiraEm: z.iso.datetime(),
});

export const ProjetoResumo = z.strictObject({
  slug: Slug,
  nome: z.string(),
  anos: z.array(Ano),
  atualizadoEm: z.iso.datetime(),
  bloqueio: BloqueioPublico.nullable(),
});

export const Projeto = z.strictObject({
  slug: Slug,
  nome: z.string(),
  pagina: Pagina,
  anos: z.array(AnoProjeto),
  bloqueio: BloqueioPublico.nullable(),
  criadoEm: z.iso.datetime(),
  atualizadoEm: z.iso.datetime(),
});

export const ErroApi = z.strictObject({
  erro: z.string(),
  campo: z.string().optional(),
  detalhes: z.array(z.strictObject({ campo: z.string(), erro: z.string() })).optional(),
  bloqueio: BloqueioPublico.nullable().optional(),
});

// ==========================================
// TIPOS
// ==========================================

export type Ano = z.infer<typeof Ano>;
export type Padrao = z.infer<typeof Padrao>;
export type ScaleRange = z.infer<typeof ScaleRange>;
export type Cortes = z.infer<typeof Cortes>;
export type LinhaEscala = z.infer<typeof LinhaEscala>;
export type Escala = z.infer<typeof Escala>;
export type Bncc = z.infer<typeof Bncc>;
export type Descritor = z.infer<typeof Descritor>;
export type AnoProjeto = z.infer<typeof AnoProjeto>;
export type ImagemPagina = z.infer<typeof ImagemPagina>;
export type Pagina = z.infer<typeof Pagina>;
export type PaginaPatch = z.infer<typeof PaginaPatch>;
export type PaginaTextos = z.infer<typeof PaginaTextos>;
export type Revista = z.infer<typeof Revista>;
export type Perfil = z.infer<typeof Perfil>;
export type LoginEntrada = z.infer<typeof LoginEntrada>;
export type CriarUsuarioEntrada = z.infer<typeof CriarUsuarioEntrada>;
export type AtualizarUsuarioEntrada = z.infer<typeof AtualizarUsuarioEntrada>;
export type OrigemProjeto = z.infer<typeof OrigemProjeto>;
export type CriarProjetoEntrada = z.infer<typeof CriarProjetoEntrada>;
export type AtualizarProjetoEntrada = z.infer<typeof AtualizarProjetoEntrada>;
export type CriarAnoEntrada = z.infer<typeof CriarAnoEntrada>;
export type AtualizarAnoEntrada = z.infer<typeof AtualizarAnoEntrada>;
export type CriarDescritorEntrada = z.infer<typeof CriarDescritorEntrada>;
export type AtualizarDescritorEntrada = z.infer<typeof AtualizarDescritorEntrada>;
export type Usuario = z.infer<typeof Usuario>;
export type BloqueioPublico = z.infer<typeof BloqueioPublico>;
export type ProjetoResumo = z.infer<typeof ProjetoResumo>;
export type Projeto = z.infer<typeof Projeto>;
export type ErroApi = z.infer<typeof ErroApi>;
