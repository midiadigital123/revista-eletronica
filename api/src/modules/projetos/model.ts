import { Schema, model, type HydratedDocument, type Types } from "mongoose";
import { ANO_REGEX, PADROES, type AnoProjeto } from "../../contrato/schemas.js";

export interface ImagemArmazenada {
  arquivoId: Types.ObjectId;
  nome: string;
  mime: "image/png" | "image/jpeg" | "image/webp";
  tamanho: number;
}

/** Valor de um campo de página: texto, parágrafos ou imagem no GridFS. */
export type ValorPagina = string | string[] | ImagemArmazenada;

export interface BloqueioDb {
  usuarioId: Types.ObjectId;
  nome: string;
  sessaoEdicao: string;
  desde: Date;
  expiraEm: Date;
}

export interface ProjetoDb {
  slug: string;
  nome: string;
  pagina: Record<string, ValorPagina>;
  anos: AnoProjeto[];
  bloqueio: BloqueioDb | null;
  excluidoEm: Date | null;
  slugOriginal: string | null;
  criadoEm: Date;
  atualizadoEm: Date;
}

const linhaSchema = new Schema(
  { level: { type: Number, required: true }, content: { type: String, required: true } },
  { _id: false },
);

const escalaSchema = new Schema(
  Object.fromEntries(PADROES.map((p) => [p, { type: [linhaSchema], default: [] }])),
  { _id: false },
);

const descritorSchema = new Schema(
  {
    codigo: { type: String, required: true },
    topic: { type: String, default: "" },
    description: { type: String, default: "" },
    prerequisites: { type: [String], default: [] },
    bncc: {
      practices: { type: String, default: "" },
      knowledge: { type: String, default: "" },
      skills: { type: [String], default: [] },
    },
    scale: { type: escalaSchema, default: () => ({}) },
  },
  { _id: false },
);

const anoSchema = new Schema(
  {
    ano: { type: String, match: ANO_REGEX, required: true },
    scaleRange: { min: { type: Number, required: true }, max: { type: Number, required: true } },
    cortes: {
      "padrao-1": { type: Number, required: true },
      "padrao-2": { type: Number, required: true },
      "padrao-3": { type: Number, required: true },
    },
    descritores: { type: [descritorSchema], default: [] },
  },
  { _id: false },
);

const bloqueioSchema = new Schema(
  {
    usuarioId: { type: Schema.Types.ObjectId, ref: "Usuario", required: true },
    nome: { type: String, required: true },
    sessaoEdicao: { type: String, required: true },
    desde: { type: Date, required: true },
    expiraEm: { type: Date, required: true },
  },
  { _id: false },
);

const projetoSchema = new Schema<ProjetoDb>(
  {
    // Único entre todos os documentos; ao excluir, o slug é liberado (ver repository.excluir).
    slug: { type: String, required: true, unique: true },
    nome: { type: String, required: true },
    /**
     * Campos de CAMPOS_PAGINA: string (texto), string[] (paragrafos) ou
     * { arquivoId, nome, mime, tamanho } (imagem, arquivo no GridFS).
     */
    pagina: { type: Schema.Types.Mixed, default: () => ({}) },
    anos: { type: [anoSchema], default: [] },
    bloqueio: { type: bloqueioSchema, default: null },
    excluidoEm: { type: Date, default: null },
    slugOriginal: { type: String, default: null },
  },
  {
    timestamps: { createdAt: "criadoEm", updatedAt: "atualizadoEm" },
    minimize: false,
    // Edições carregam-modificam-salvam; __v impede sobrescrever escrita concorrente.
    optimisticConcurrency: true,
  },
);

projetoSchema.index({ excluidoEm: 1, nome: 1 });

export type ProjetoDoc = HydratedDocument<ProjetoDb>;
export const ProjetoModel = model<ProjetoDb>("Projeto", projetoSchema, "projetos");
