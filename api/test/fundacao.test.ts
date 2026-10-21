import supertest from "supertest";
import { describe, expect, it } from "vitest";
import { ProjetoModel } from "../src/modules/projetos/model.js";
import { agenteLogado, usarApp } from "./helpers.js";

const ctx = usarApp();

async function criarProjetoNoBanco(slug = "sp") {
  return ProjetoModel.create({
    slug,
    nome: "SP",
    cadernos: [
      {
        id: "lingua-portuguesa",
        anos: [{ ano: "5ef", scaleRange: { min: 0, max: 500 }, cortes: { "padrao-1": 125, "padrao-2": 250, "padrao-3": 375 } }],
      },
    ],
  });
}

describe("fundação", () => {
  it("rota protegida responde 401 sem sessão no formato do contrato", async () => {
    const r = await supertest(ctx.app).get("/api/auth/me").expect(401);
    expect(r.body).toMatchObject({ erro: expect.any(String) });
  });

  it("login abre sessão e /me devolve o usuário", async () => {
    const { agente, usuario } = await agenteLogado(ctx.app, "admin");
    const r = await agente.get("/api/auth/me").expect(200);
    expect(r.body).toEqual({ id: usuario.id, email: usuario.email, nome: usuario.nome, perfil: "admin", ativo: true });
  });

  it("GET /api/pagina/campos lista os campos do contrato", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const r = await agente.get("/api/pagina/campos").expect(200);
    expect(r.body.map((c: { chave: string }) => c.chave)).toContain("heroTitulo");
  });

  it("bloqueio: adquirir, disputar (423), renovar e liberar", async () => {
    await criarProjetoNoBanco();
    const ana = await agenteLogado(ctx.app);
    const bia = await agenteLogado(ctx.app);
    await ana.agente.post("/api/projetos/sp/bloqueio").expect(201);
    const negado = await bia.agente.post("/api/projetos/sp/bloqueio").expect(423);
    expect(negado.body.bloqueio.nome).toBe(ana.usuario.nome);
    await ana.agente.put("/api/projetos/sp/bloqueio").expect(200);
    await bia.agente.put("/api/projetos/sp/bloqueio").expect(423);
    await ana.agente.delete("/api/projetos/sp/bloqueio").expect(204);
    await bia.agente.post("/api/projetos/sp/bloqueio").expect(201);
  });

  it("rota inexistente responde 404 JSON (e 401 sem sessão)", async () => {
    await supertest(ctx.app).get("/api/nada").expect(401);
    const { agente } = await agenteLogado(ctx.app);
    await agente.get("/api/nada").expect(404, { erro: "Rota não encontrada" });
  });

  it("usuário desativado perde o acesso na próxima requisição", async () => {
    const { agente, usuario } = await agenteLogado(ctx.app);
    await agente.get("/api/auth/me").expect(200);
    await usuario.updateOne({ ativo: false });
    await agente.get("/api/pagina/campos").expect(401);
  });
});
