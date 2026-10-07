import supertest from "supertest";
import { describe, expect, it } from "vitest";
import { SENHA_TESTE, agenteLogado, criarUsuario, usarApp } from "./helpers.js";

const ctx = usarApp();

const cookieSessao = (r: supertest.Response) =>
  ([] as string[]).concat(r.headers["set-cookie"] ?? []).find((c) => c.startsWith("revista.sid="));

describe("auth", () => {
  it("login certo devolve o usuário sem senhaHash", async () => {
    const usuario = await criarUsuario("editor");
    const r = await supertest(ctx.app)
      .post("/api/auth/login")
      .send({ email: usuario.email, senha: SENHA_TESTE })
      .expect(200);
    expect(r.body).toEqual({
      id: usuario.id,
      email: usuario.email,
      nome: usuario.nome,
      perfil: "editor",
      ativo: true,
    });
  });

  it("senha errada, e-mail desconhecido e usuário inativo → 401", async () => {
    const usuario = await criarUsuario("editor");
    const api = supertest(ctx.app);
    await api
      .post("/api/auth/login")
      .send({ email: usuario.email, senha: "errada-123" })
      .expect(401);
    await api
      .post("/api/auth/login")
      .send({ email: "ninguem@teste.org", senha: SENHA_TESTE })
      .expect(401);
    await usuario.updateOne({ ativo: false });
    const r = await api
      .post("/api/auth/login")
      .send({ email: usuario.email, senha: SENHA_TESTE })
      .expect(401);
    expect(r.body).toEqual({ erro: expect.any(String) });
  });

  it("11ª senha errada seguida → 429, mesmo com a senha certa", async () => {
    const usuario = await criarUsuario("editor");
    const api = supertest(ctx.app);
    for (let i = 0; i < 10; i++)
      await api
        .post("/api/auth/login")
        .send({ email: usuario.email, senha: "errada-123" })
        .expect(401);
    await api
      .post("/api/auth/login")
      .send({ email: usuario.email, senha: SENHA_TESTE })
      .expect(429);
  });

  it("login regenera a sessão (cookie muda)", async () => {
    const usuario = await criarUsuario("editor");
    const agente = supertest.agent(ctx.app);
    const credenciais = { email: usuario.email, senha: SENHA_TESTE };
    const primeiro = cookieSessao(
      await agente.post("/api/auth/login").send(credenciais).expect(200),
    );
    const segundo = cookieSessao(
      await agente.post("/api/auth/login").send(credenciais).expect(200),
    );
    expect(primeiro).toBeDefined();
    expect(segundo).toBeDefined();
    expect(segundo).not.toBe(primeiro);
  });

  it("logout responde 204 e encerra a sessão", async () => {
    const { agente } = await agenteLogado(ctx.app);
    await agente.post("/api/auth/logout").expect(204);
    await agente.get("/api/auth/me").expect(401);
  });
});
