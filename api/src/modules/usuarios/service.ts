import mongoose, { type ClientSession } from "mongoose";
import type {
  AtualizarUsuarioEntrada,
  CriarUsuarioEntrada,
  Usuario,
} from "../../contrato/schemas.js";
import { conflito, naoEncontrado, requisicaoInvalida } from "../../errors.js";
import { UsuarioModel, paraUsuario, type UsuarioDoc } from "./model.js";
import { gerarHash } from "./senha.js";

const ultimoAdmin = () => requisicaoInvalida("É preciso manter ao menos um administrador ativo");

async function buscar(id: string, session?: ClientSession): Promise<UsuarioDoc> {
  const usuario = await UsuarioModel.findById(id).session(session ?? null);
  if (!usuario) throw naoEncontrado("Usuário");
  return usuario;
}

/**
 * Executa `alterar` numa transação que garante ≥ 1 admin ativo ao final.
 *
 * Transação sozinha não basta: com snapshot isolation, dois admins rebaixando
 * um ao outro ao mesmo tempo leem "há outro admin", gravam documentos
 * diferentes e ambos confirmam (write skew). Por isso toda alteração desse tipo
 * grava também o mesmo documento-trava: a segunda transação conflita, o driver
 * a repete e ela passa a enxergar o estado já alterado.
 *
 * `alterar` deve carregar, modificar e gravar DENTRO do callback (com a session):
 * numa repetição, documentos carregados fora dela teriam o estado restaurado
 * pelo Mongoose e o save() não gravaria nada.
 */
async function comAdminGarantido<T>(alterar: (session: ClientSession) => Promise<T>): Promise<T> {
  return mongoose.connection.transaction(async (session) => {
    await mongoose.connection
      .collection<{ _id: string; versao: number }>("travas")
      .updateOne({ _id: "admins-ativos" }, { $inc: { versao: 1 } }, { upsert: true, session });
    const resultado = await alterar(session);
    const restantes = await UsuarioModel.countDocuments({ perfil: "admin", ativo: true }).session(session);
    if (restantes === 0) throw ultimoAdmin();
    return resultado;
  });
}

export async function listarUsuarios(): Promise<Usuario[]> {
  const usuarios = await UsuarioModel.find().sort({ nome: 1 }).collation({ locale: "pt" });
  return usuarios.map(paraUsuario);
}

export async function criarUsuario(dados: CriarUsuarioEntrada): Promise<Usuario> {
  if (await UsuarioModel.exists({ email: dados.email }))
    throw conflito("E-mail já cadastrado", "email");
  const { senha, ...resto } = dados;
  const usuario = await UsuarioModel.create({ ...resto, senhaHash: await gerarHash(senha) });
  return paraUsuario(usuario);
}

export async function atualizarUsuario(
  id: string,
  dados: AtualizarUsuarioEntrada,
): Promise<Usuario> {
  const { senha, ...resto } = dados;
  const senhaHash = senha ? await gerarHash(senha) : undefined;
  const aplicar = async (session?: ClientSession) => {
    const usuario = await buscar(id, session);
    usuario.set(resto);
    if (senhaHash) usuario.senhaHash = senhaHash;
    await usuario.save({ session });
    return usuario;
  };
  // Rebaixar ou desativar pode deixar o sistema sem admin ativo.
  const podeAfetarAdmins = dados.perfil === "editor" || dados.ativo === false;
  return paraUsuario(podeAfetarAdmins ? await comAdminGarantido(aplicar) : await aplicar());
}

export async function excluirUsuario(id: string, idDaSessao: string): Promise<void> {
  if (id === idDaSessao) throw requisicaoInvalida("Você não pode excluir a própria conta");
  await comAdminGarantido(async (session) => {
    const usuario = await buscar(id, session);
    await usuario.deleteOne({ session });
  });
}
