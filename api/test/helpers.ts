import { MongoMemoryReplSet } from "mongodb-memory-server";
import mongoose from "mongoose";
import supertest from "supertest";
import { afterAll, afterEach, beforeAll } from "vitest";
import { criarApp } from "../src/app.js";
import { lerConfig } from "../src/config.js";
import { HEADER_SESSAO_EDICAO, type Perfil } from "../src/contrato/schemas.js";
import { criarLogger } from "../src/logger.js";
import { UsuarioModel } from "../src/modules/usuarios/model.js";
import { gerarHash } from "../src/modules/usuarios/senha.js";
import type { Express } from "express";

export const SENHA_TESTE = "senha-de-teste";

/**
 * Sobe um MongoDB em memória (replica set de 1 nó, para suportar transações)
 * e o app para o arquivo de teste atual.
 * Uso: `const ctx = usarApp();` no topo do arquivo; depois `ctx.app`.
 * Limpa as coleções após cada teste.
 */
export function usarApp() {
  const ctx = {} as { app: Express; mongo: MongoMemoryReplSet };
  beforeAll(async () => {
    ctx.mongo = await MongoMemoryReplSet.create({ replSet: { count: 1, storageEngine: "wiredTiger" } });
    await mongoose.connect(ctx.mongo.getUri());
    const config = lerConfig({
      NODE_ENV: "test",
      MONGO_URL: ctx.mongo.getUri(),
      SESSION_SECRET: "x".repeat(32),
    });
    ctx.app = criarApp(config, criarLogger(config));
  });
  afterEach(async () => {
    const colecoes = await mongoose.connection.db!.collections();
    await Promise.all(colecoes.map((c) => c.deleteMany({})));
  });
  afterAll(async () => {
    await mongoose.disconnect();
    await ctx.mongo?.stop();
  });
  return ctx;
}

let contador = 0;

export async function criarUsuario(perfil: Perfil = "editor", dados: { email?: string; nome?: string } = {}) {
  contador += 1;
  return UsuarioModel.create({
    email: dados.email ?? `usuario${contador}@teste.org`,
    nome: dados.nome ?? `Usuário ${contador}`,
    senhaHash: await gerarHash(SENHA_TESTE),
    perfil,
  });
}

/**
 * Agente supertest com sessão logada. `sessaoEdicao` é enviada como
 * X-Sessao-Edicao em todas as requisições (simula uma aba do editor).
 */
export async function agenteLogado(
  app: Express,
  perfil: Perfil = "editor",
  sessaoEdicao = `aba-${Math.random().toString(36).slice(2)}`,
) {
  const usuario = await criarUsuario(perfil);
  const agente = supertest.agent(app).set(HEADER_SESSAO_EDICAO, sessaoEdicao);
  await agente.post("/api/auth/login").send({ email: usuario.email, senha: SENHA_TESTE }).expect(200);
  return { agente, usuario, sessaoEdicao };
}
