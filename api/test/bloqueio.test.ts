import supertest from "supertest";
import { describe, expect, it } from "vitest";
import { HEADER_SESSAO_EDICAO } from "../src/contrato/schemas.js";
import { ProjetoModel } from "../src/modules/projetos/model.js";
import { adquirir, renovar } from "../src/modules/bloqueio/service.js";
import { agenteLogado, SENHA_TESTE, usarApp } from "./helpers.js";

const ctx = usarApp();
const URL = "/api/projetos/sp/bloqueio";

const criarProjeto = () => ProjetoModel.create({ slug: "sp", nome: "SP" });
const expirar = () =>
  ProjetoModel.updateOne({ slug: "sp" }, { $set: { "bloqueio.expiraEm": new Date(Date.now() - 1000) } });

describe("bloqueio (bordas)", () => {
  it("duas abas do mesmo usuário disputam: a segunda leva 423", async () => {
    await criarProjeto();
    const aba1 = await agenteLogado(ctx.app);
    const aba2 = supertest.agent(ctx.app).set(HEADER_SESSAO_EDICAO, "outra-aba");
    await aba2.post("/api/auth/login").send({ email: aba1.usuario.email, senha: SENHA_TESTE }).expect(200);
    await aba1.agente.post(URL).expect(201);
    await aba1.agente.post(URL).expect(201); // mesma aba readquire
    const r = await aba2.post(URL).expect(423);
    expect(r.body.bloqueio.usuarioId).toBe(aba1.usuario.id);
  });

  it("sem header X-Sessao-Edicao → 400", async () => {
    await criarProjeto();
    const { usuario } = await agenteLogado(ctx.app);
    const semAba = supertest.agent(ctx.app);
    await semAba.post("/api/auth/login").send({ email: usuario.email, senha: SENHA_TESTE }).expect(200);
    const r = await semAba.post(URL).expect(400);
    expect(r.body.campo).toBe(HEADER_SESSAO_EDICAO);
  });

  it("PUT após expirar → 423; outra pessoa adquire o expirado → 201", async () => {
    await criarProjeto();
    const ana = await agenteLogado(ctx.app);
    const bia = await agenteLogado(ctx.app);
    await ana.agente.post(URL).expect(201);
    await expirar();
    const r = await ana.agente.put(URL).expect(423);
    expect(r.body.bloqueio).toBeNull();
    await bia.agente.post(URL).expect(201);
    await ana.agente.put(URL).expect(423);
  });

  it("serviço: renovar depois do TTL falha; adquirir pelo relógio simulado", async () => {
    await criarProjeto();
    const ana = { usuarioId: "6650f0f0f0f0f0f0f0f0f0f0", nome: "Ana", sessaoEdicao: "a" };
    const bia = { usuarioId: "6650f0f0f0f0f0f0f0f0f0f1", nome: "Bia", sessaoEdicao: "b" };
    const t0 = new Date("2026-01-01T00:00:00Z");
    const depois = new Date(t0.getTime() + 3 * 60 * 1000);
    await adquirir("sp", ana, t0);
    await expect(adquirir("sp", bia, new Date(t0.getTime() + 1000))).rejects.toMatchObject({ status: 423 });
    await expect(renovar("sp", ana, depois)).rejects.toMatchObject({ status: 423 });
    expect((await adquirir("sp", bia, depois)).nome).toBe("Bia");
  });

  it("DELETE de quem não é dono não libera", async () => {
    await criarProjeto();
    const ana = await agenteLogado(ctx.app);
    const bia = await agenteLogado(ctx.app);
    await ana.agente.post(URL).expect(201);
    await bia.agente.delete(URL).expect(204);
    await bia.agente.post(URL).expect(423);
    await ana.agente.put(URL).expect(200);
  });

  it("projeto inexistente ou excluído → 404", async () => {
    const { agente } = await agenteLogado(ctx.app);
    await agente.post("/api/projetos/nada/bloqueio").expect(404);
    await agente.put("/api/projetos/nada/bloqueio").expect(404);
    await criarProjeto();
    await ProjetoModel.updateOne({ slug: "sp" }, { $set: { excluidoEm: new Date() } });
    await agente.post(URL).expect(404);
  });
});
