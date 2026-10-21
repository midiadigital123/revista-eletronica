import supertest from "supertest";
import { describe, expect, it } from "vitest";
import { lerConfig } from "../src/config.js";
import { criarLogger } from "../src/logger.js";
import { UsuarioModel } from "../src/modules/usuarios/model.js";
import { conferirSenha } from "../src/modules/usuarios/senha.js";
import { excluirUsuario } from "../src/modules/usuarios/service.js";
import { garantirAdmin } from "../src/seed.js";
import { agenteLogado, criarUsuario, usarApp } from "./helpers.js";

const ctx = usarApp();

const novo = { email: "Nova@Teste.org", nome: "Nova Pessoa", senha: "senha-nova-1", perfil: "editor" };

describe("usuários: acesso", () => {
  it("401 sem sessão e 403 para editor", async () => {
    await supertest(ctx.app).get("/api/usuarios").expect(401);
    const { agente } = await agenteLogado(ctx.app, "editor");
    const r = await agente.get("/api/usuarios").expect(403);
    expect(r.body).toEqual({ erro: expect.any(String) });
    await agente.post("/api/usuarios").send(novo).expect(403);
  });
});

describe("usuários: CRUD", () => {
  it("lista em ordem de nome sem senhaHash", async () => {
    const { agente, usuario } = await agenteLogado(ctx.app, "admin");
    await criarUsuario("editor", { nome: "Zélia" });
    await criarUsuario("editor", { nome: "Álvaro" });
    await criarUsuario("editor", { nome: "beatriz" });
    const r = await agente.get("/api/usuarios").expect(200);
    const nomes = (r.body as { nome: string }[]).map((u) => u.nome);
    expect(nomes).toEqual(["Álvaro", "beatriz", usuario.nome, "Zélia"]);
    for (const u of r.body) expect(Object.keys(u).sort()).toEqual(["ativo", "email", "id", "nome", "perfil"]);
  });

  it("cria (201), atualiza, troca a senha e exclui (204)", async () => {
    const { agente } = await agenteLogado(ctx.app, "admin");
    const criado = await agente.post("/api/usuarios").send(novo).expect(201);
    expect(criado.body).toEqual({ id: expect.any(String), email: "nova@teste.org", nome: "Nova Pessoa", perfil: "editor", ativo: true });
    const id = criado.body.id as string;

    const r = await agente.patch(`/api/usuarios/${id}`).send({ nome: "Nova Editada", perfil: "admin", senha: "outra-senha-2" }).expect(200);
    expect(r.body).toMatchObject({ nome: "Nova Editada", perfil: "admin" });
    expect(r.body).not.toHaveProperty("senhaHash");
    const doBanco = await UsuarioModel.findById(id).select("+senhaHash").orFail();
    expect(await conferirSenha("outra-senha-2", doBanco.senhaHash)).toBe(true);
    await supertest(ctx.app).post("/api/auth/login").send({ email: novo.email, senha: "outra-senha-2" }).expect(200);

    await agente.delete(`/api/usuarios/${id}`).expect(204);
    expect(await UsuarioModel.findById(id)).toBeNull();
  });

  it("e-mail duplicado → 409", async () => {
    const { agente, usuario } = await agenteLogado(ctx.app, "admin");
    const r = await agente.post("/api/usuarios").send({ ...novo, email: usuario.email.toUpperCase() }).expect(409);
    expect(r.body).toEqual({ erro: "E-mail já cadastrado", campo: "email" });
  });

  it("validação: campo desconhecido, corpo vazio e id inválido → 400", async () => {
    const { agente, usuario } = await agenteLogado(ctx.app, "admin");
    await agente.post("/api/usuarios").send({ ...novo, extra: 1 }).expect(400);
    await agente.patch(`/api/usuarios/${usuario.id}`).send({}).expect(400);
    await agente.patch("/api/usuarios/nao-e-id").send({ nome: "X" }).expect(400);
  });

  it("id inexistente → 404", async () => {
    const { agente } = await agenteLogado(ctx.app, "admin");
    const inexistente = "0".repeat(24);
    await agente.patch(`/api/usuarios/${inexistente}`).send({ nome: "X" }).expect(404, { erro: "Usuário não encontrado" });
    await agente.delete(`/api/usuarios/${inexistente}`).expect(404);
  });
});

describe("usuários: regras", () => {
  it("não rebaixa, desativa nem exclui o último admin ativo", async () => {
    const { agente, usuario: eu } = await agenteLogado(ctx.app, "admin");
    await agente.patch(`/api/usuarios/${eu.id}`).send({ perfil: "editor" }).expect(400);
    await agente.patch(`/api/usuarios/${eu.id}`).send({ ativo: false }).expect(400);

    // Outro admin inativo não conta como "admin ativo".
    const inativo = await criarUsuario("admin");
    await inativo.updateOne({ ativo: false });
    await agente.patch(`/api/usuarios/${eu.id}`).send({ perfil: "editor" }).expect(400);

    // Com outro admin ativo, pode rebaixar.
    const outro = await criarUsuario("admin");
    await agente.patch(`/api/usuarios/${outro.id}`).send({ perfil: "editor" }).expect(200);
    await agente.patch(`/api/usuarios/${outro.id}`).send({ perfil: "admin" }).expect(200);
    await agente.patch(`/api/usuarios/${eu.id}`).send({ ativo: false }).expect(200);
  });

  it("não exclui o último admin ativo (regra no service; via HTTP cai na regra da própria conta)", async () => {
    const admin = await criarUsuario("admin");
    const editor = await criarUsuario("editor");
    await expect(excluirUsuario(admin.id, editor.id)).rejects.toMatchObject({ status: 400 });
    expect(await UsuarioModel.exists({ _id: admin._id })).toBeTruthy();
  });

  it("ninguém exclui a própria conta", async () => {
    const { agente, usuario } = await agenteLogado(ctx.app, "admin");
    await criarUsuario("admin");
    await agente.delete(`/api/usuarios/${usuario.id}`).expect(400);
  });
});

describe("seed garantirAdmin", () => {
  const config = (senha: string) =>
    lerConfig({
      NODE_ENV: "test",
      MONGO_URL: "mongodb://nao-usado",
      SESSION_SECRET: "x".repeat(32),
      ADMIN_EMAIL: "Admin@Teste.org",
      ADMIN_SENHA: senha,
    });

  it("cria o admin e, repetido, não altera nada (nem a senha)", async () => {
    const c1 = config("senha-inicial");
    await garantirAdmin(c1, criarLogger(c1));
    const criado = await UsuarioModel.findOne({ email: "admin@teste.org" }).select("+senhaHash").orFail();
    expect(criado).toMatchObject({ nome: "Administrador", perfil: "admin", ativo: true });

    const c2 = config("senha-diferente");
    await garantirAdmin(c2, criarLogger(c2));
    const depois = await UsuarioModel.findOne({ email: "admin@teste.org" }).select("+senhaHash").orFail();
    expect(depois.senhaHash).toBe(criado.senhaHash);
    expect(depois.atualizadoEm).toEqual(criado.atualizadoEm);
    expect(await UsuarioModel.countDocuments()).toBe(1);
    await supertest(ctx.app).post("/api/auth/login").send({ email: "admin@teste.org", senha: "senha-inicial" }).expect(200);
  });

  it("sem ADMIN_EMAIL/ADMIN_SENHA não cria ninguém", async () => {
    const c = lerConfig({ NODE_ENV: "test", MONGO_URL: "mongodb://x", SESSION_SECRET: "x".repeat(32) });
    await garantirAdmin(c, criarLogger(c));
    expect(await UsuarioModel.countDocuments()).toBe(0);
  });
});

describe("regra do último admin sob concorrência (D-019)", () => {
  it("dois admins se rebaixando ao mesmo tempo: um consegue, o outro recebe 400", async () => {
    const ana = await agenteLogado(ctx.app, "admin");
    const bia = await agenteLogado(ctx.app, "admin");
    const [r1, r2] = await Promise.all([
      ana.agente.patch(`/api/usuarios/${bia.usuario.id}`).send({ perfil: "editor" }),
      bia.agente.patch(`/api/usuarios/${ana.usuario.id}`).send({ perfil: "editor" }),
    ]);
    expect([r1.status, r2.status].sort()).toEqual([200, 400]);
    expect(await UsuarioModel.countDocuments({ perfil: "admin", ativo: true })).toBe(1);
  });
});
