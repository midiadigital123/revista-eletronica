import { Schema, model, type HydratedDocument } from "mongoose";
import type { Perfil, Usuario } from "../../contrato/schemas.js";

export interface UsuarioDb {
  email: string;
  nome: string;
  senhaHash: string;
  perfil: Perfil;
  ativo: boolean;
  criadoEm: Date;
  atualizadoEm: Date;
}

const usuarioSchema = new Schema<UsuarioDb>(
  {
    email: { type: String, required: true, unique: true, lowercase: true, trim: true },
    nome: { type: String, required: true, trim: true },
    senhaHash: { type: String, required: true, select: false },
    perfil: { type: String, enum: ["admin", "editor"], required: true },
    ativo: { type: Boolean, default: true },
  },
  { timestamps: { createdAt: "criadoEm", updatedAt: "atualizadoEm" } },
);

export type UsuarioDoc = HydratedDocument<UsuarioDb>;
export const UsuarioModel = model<UsuarioDb>("Usuario", usuarioSchema, "usuarios");

export const paraUsuario = (u: UsuarioDoc): Usuario => ({
  id: u.id,
  email: u.email,
  nome: u.nome,
  perfil: u.perfil,
  ativo: u.ativo,
});
