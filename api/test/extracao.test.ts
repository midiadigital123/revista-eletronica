import { spawnSync } from "node:child_process";
import { existsSync, readFileSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";
import supertest from "supertest";
import { describe, expect, it } from "vitest";
import { agenteLogado, usarApp } from "./helpers.js";

const ctx = usarApp();

const temExtrator = ["python3", "pdftotext"].every((cmd) => !spawnSync(cmd, ["-v"]).error);
// PDF real é opcional (não está no repositório), como em scripts/test_extrair_descritores.py.
const PDF = process.env.REVISTA_PDF ?? join(homedir(), "Documentos/SAEGO_2025_RE_Alfa_2EF_5EF Web.pdf");

const enviar = (agente: supertest.Agent, conteudo: Buffer, nome = "revista.pdf") =>
  agente.post("/api/extracao").attach("arquivo", conteudo, { filename: nome, contentType: "application/pdf" });

describe("extração de PDF", () => {
  it("sem login → 401", async () => {
    await enviar(supertest.agent(ctx.app), Buffer.from("%PDF-1.4")).expect(401);
  });

  it("sem arquivo ou arquivo que não é PDF → 400", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const sem = await agente.post("/api/extracao").expect(400);
    expect(sem.body.campo).toBe("arquivo");
    const r = await enviar(agente, Buffer.from("não sou um pdf")).expect(400);
    expect(r.body).toEqual({ erro: "O arquivo não é um PDF", campo: "arquivo" });
  });

  it.skipIf(!temExtrator)("PDF corrompido → 422 com a mensagem do extrator", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const r = await enviar(agente, Buffer.from("%PDF-1.4\nlixo")).expect(422);
    expect(r.body.erro).toMatch(/^Não foi possível ler o PDF: /);
  });

  it.skipIf(!temExtrator || !existsSync(PDF))("PDF da revista → revistas por disciplina e avisos", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const r = await enviar(agente, readFileSync(PDF)).expect(200);
    expect(Object.keys(r.body.disciplinas)).toEqual(["lingua-portuguesa", "matematica"]);
    expect(Object.keys(r.body.disciplinas.matematica)).toEqual(["2ef", "5ef"]);
    expect(r.body.disciplinas["lingua-portuguesa"]["2ef"].cortes).toEqual({
      "padrao-1": 350,
      "padrao-2": 400,
      "padrao-3": 500,
    });
    expect(r.body.avisos).toContainEqual(expect.stringContaining("matematica 2ef D06"));
  });
});
