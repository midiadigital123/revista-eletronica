import bcrypt from "bcryptjs";

const CUSTO = 12;

export const gerarHash = (senha: string) => bcrypt.hash(senha, CUSTO);
export const conferirSenha = (senha: string, hash: string) => bcrypt.compare(senha, hash);
