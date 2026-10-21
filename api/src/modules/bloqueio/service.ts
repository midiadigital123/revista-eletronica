import { Types } from "mongoose";
import { BLOQUEIO_TTL_MS, type BloqueioPublico } from "../../contrato/schemas.js";
import { bloqueado, naoEncontrado } from "../../errors.js";
import { ProjetoModel } from "../projetos/model.js";
import { ativo, paraBloqueio } from "../projetos/repository.js";

export interface Editor {
  usuarioId: string;
  nome: string;
  sessaoEdicao: string;
}

const expira = (agora: Date) => new Date(agora.getTime() + BLOQUEIO_TTL_MS);

/** Bloqueio novo para este editor (usado também ao criar projeto: o criador já edita). */
export const novoBloqueio = (editor: Editor, agora = new Date()) => ({
  usuarioId: new Types.ObjectId(editor.usuarioId),
  nome: editor.nome,
  sessaoEdicao: editor.sessaoEdicao,
  desde: agora,
  expiraEm: expira(agora),
});

/** Filtro: bloqueio deste editor (usuário + aba), ainda válido. */
const doEditor = (editor: Editor, agora: Date) => ({
  "bloqueio.usuarioId": new Types.ObjectId(editor.usuarioId),
  "bloqueio.sessaoEdicao": editor.sessaoEdicao,
  "bloqueio.expiraEm": { $gt: agora },
});

async function bloqueioAtual(slug: string, agora: Date): Promise<BloqueioPublico | null> {
  const projeto = await ProjetoModel.findOne(ativo(slug));
  if (!projeto) throw naoEncontrado("Projeto");
  return paraBloqueio(projeto, agora);
}

/** Adquire se livre, expirado ou já deste editor. Atômico: um único findOneAndUpdate condicional. */
export async function adquirir(slug: string, editor: Editor, agora = new Date()) {
  const projeto = await ProjetoModel.findOneAndUpdate(
    {
      ...ativo(slug),
      $or: [{ bloqueio: null }, { "bloqueio.expiraEm": { $lte: agora } }, doEditor(editor, agora)],
    },
    { $set: { bloqueio: novoBloqueio(editor, agora) } },
    { returnDocument: "after", timestamps: false },
  );
  if (!projeto) throw bloqueado(await bloqueioAtual(slug, agora));
  return paraBloqueio(projeto, agora)!;
}

/** Só renova o bloqueio que ainda é deste editor; nunca readquire. */
export async function renovar(slug: string, editor: Editor, agora = new Date()) {
  const projeto = await ProjetoModel.findOneAndUpdate(
    { ...ativo(slug), ...doEditor(editor, agora) },
    { $set: { "bloqueio.expiraEm": expira(agora) } },
    { returnDocument: "after", timestamps: false },
  );
  if (!projeto) throw bloqueado(await bloqueioAtual(slug, agora));
  return paraBloqueio(projeto, agora)!;
}

/** Libera se for deste editor. Idempotente. */
export async function liberar(slug: string, editor: Editor, agora = new Date()): Promise<void> {
  await ProjetoModel.updateOne(
    { ...ativo(slug), ...doEditor(editor, agora) },
    { $set: { bloqueio: null } },
    { timestamps: false },
  );
}

/** Garante que o editor detém o bloqueio; senão 423 (ou 404 se o projeto não existe). */
export async function exigir(slug: string, editor: Editor, agora = new Date()): Promise<void> {
  const existe = await ProjetoModel.exists({ ...ativo(slug), ...doEditor(editor, agora) });
  if (!existe) throw bloqueado(await bloqueioAtual(slug, agora));
}
