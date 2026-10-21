import { once } from "node:events";
import http from "node:http";
import type { AddressInfo } from "node:net";
import mongoose from "mongoose";
import supertest from "supertest";
import { describe, expect, it } from "vitest";
import { HEADER_SESSAO_EDICAO, IMAGEM_MAX_BYTES } from "../src/contrato/schemas.js";
import { ProjetoModel } from "../src/modules/projetos/model.js";
import {
  abrirLeitura,
  copiarImagens,
  ehImagem,
  salvarImagem,
} from "../src/modules/imagens/service.js";
import { agenteLogado, criarUsuario, SENHA_TESTE, usarApp } from "./helpers.js";

const ctx = usarApp();

const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);
// Só os bytes mágicos importam para a API; o resto é preenchimento.
const JPEG = Buffer.concat([Buffer.from([0xff, 0xd8, 0xff, 0xe0]), Buffer.alloc(32, 7)]);
const URL = "/api/projetos/sp/pagina/heroImagem/imagem";

async function editor() {
  await ProjetoModel.create({ slug: "sp", nome: "SP" });
  const ed = await agenteLogado(ctx.app);
  await ed.agente.post("/api/projetos/sp/bloqueio").expect(201);
  return ed.agente;
}

const contarArquivos = () => mongoose.connection.db!.collection("imagens.files").countDocuments();

async function lerTudo(stream: NodeJS.ReadableStream) {
  const partes: Buffer[] = [];
  for await (const parte of stream) partes.push(Buffer.from(parte as Buffer));
  return Buffer.concat(partes);
}

describe("imagens da página", () => {
  it("upload PNG, GET devolve os mesmos bytes; JPEG substitui e remove o antigo", async () => {
    const agente = await editor();
    const r = await agente
      .put(URL)
      .attach("arquivo", PNG, { filename: "a.png", contentType: "image/png" })
      .expect(200);
    expect(r.body.heroImagem).toEqual({
      nome: "heroImagem.png",
      mime: "image/png",
      tamanho: PNG.length,
    });

    const g = await agente
      .get(URL)
      .buffer(true)
      .parse((res, cb) => {
        const partes: Buffer[] = [];
        res.on("data", (p: Buffer) => partes.push(p));
        res.on("end", () => cb(null, Buffer.concat(partes)));
      })
      .expect(200);
    expect(g.headers["content-type"]).toBe("image/png");
    expect(g.headers["cache-control"]).toBe("no-cache");
    expect(Buffer.compare(g.body as Buffer, PNG)).toBe(0);

    const j = await agente
      .put(URL)
      .attach("arquivo", JPEG, { filename: "a.jpg", contentType: "image/jpeg" })
      .expect(200);
    expect(j.body.heroImagem).toMatchObject({ nome: "heroImagem.jpg", mime: "image/jpeg" });
    expect(await contarArquivos()).toBe(1);
  });

  it("recusa SVG, PNG falso, arquivo ausente (400) e > 5 MB (413)", async () => {
    const agente = await editor();
    const svg = Buffer.from('<svg xmlns="http://www.w3.org/2000/svg"/>');
    await agente
      .put(URL)
      .attach("arquivo", svg, { filename: "a.svg", contentType: "image/svg+xml" })
      .expect(400);
    await agente
      .put(URL)
      .attach("arquivo", JPEG, { filename: "a.png", contentType: "image/png" })
      .expect(400);
    await agente.put(URL).field("x", "1").expect(400);
    const grande = Buffer.concat([PNG, Buffer.alloc(IMAGEM_MAX_BYTES)]);
    await agente
      .put(URL)
      .attach("arquivo", grande, { filename: "g.png", contentType: "image/png" })
      .expect(413);
    expect(await contarArquivos()).toBe(0);
  });

  it("chave que não é imagem → 404; GET sem imagem → 404", async () => {
    const agente = await editor();
    await agente
      .put("/api/projetos/sp/pagina/heroTitulo/imagem")
      .attach("arquivo", PNG, { filename: "a.png", contentType: "image/png" })
      .expect(404);
    await agente.get(URL).expect(404);
  });

  it("sem bloqueio → 423", async () => {
    await ProjetoModel.create({ slug: "sp", nome: "SP" });
    const { agente } = await agenteLogado(ctx.app);
    await agente
      .put(URL)
      .attach("arquivo", PNG, { filename: "a.png", contentType: "image/png" })
      .expect(423);
    await agente.delete(URL).expect(423);
  });

  it("bloqueio que vence durante o upload → 423 e nada é gravado", async () => {
    // Upload em duas partes por http cru: o bloqueio vence entre elas.
    const usuario = await criarUsuario();
    const login = await supertest(ctx.app)
      .post("/api/auth/login")
      .send({ email: usuario.email, senha: SENHA_TESTE })
      .expect(200);
    const headers = {
      cookie: login.headers["set-cookie"]![0]!.split(";")[0]!,
      [HEADER_SESSAO_EDICAO]: "aba",
    };
    await ProjetoModel.create({ slug: "sp", nome: "SP" });
    await supertest(ctx.app).post("/api/projetos/sp/bloqueio").set(headers).expect(201);

    const servidor = ctx.app.listen(0);
    await once(servidor, "listening");
    const limite = "limite";
    const req = http.request({
      port: (servidor.address() as AddressInfo).port,
      method: "PUT",
      path: URL,
      headers: { ...headers, "content-type": `multipart/form-data; boundary=${limite}` },
    });
    const resposta = once(req, "response") as Promise<[http.IncomingMessage]>;
    req.write(
      `--${limite}\r\nContent-Disposition: form-data; name="arquivo"; filename="a.png"\r\nContent-Type: image/png\r\n\r\n`,
    );
    req.write(PNG);
    await new Promise((r) => setTimeout(r, 100)); // o servidor já começou a tratar a requisição
    await ProjetoModel.updateOne({ slug: "sp" }, { "bloqueio.expiraEm": new Date(0) });
    req.end(`\r\n--${limite}--\r\n`);
    const [res] = await resposta;
    res.resume();
    servidor.close();
    expect(res.statusCode).toBe(423);
    expect(await contarArquivos()).toBe(0);
  });

  it("GET com arquivo sumido do GridFS → 404 em JSON, sem headers de imagem", async () => {
    const agente = await editor();
    await agente
      .put(URL)
      .attach("arquivo", PNG, { filename: "a.png", contentType: "image/png" })
      .expect(200);
    await mongoose.connection.db!.collection("imagens.files").deleteMany({});
    const r = await agente.get(URL).expect(404);
    expect(r.headers["content-type"]).toMatch(/^application\/json/);
    expect(r.headers["cache-control"]).toBeUndefined();
    expect(r.body).toEqual({ erro: expect.any(String) });
  });

  it("DELETE remove o arquivo e é idempotente", async () => {
    const agente = await editor();
    await agente
      .put(URL)
      .attach("arquivo", PNG, { filename: "a.png", contentType: "image/png" })
      .expect(200);
    const r = await agente.delete(URL).expect(200);
    expect(r.body.heroImagem).toBeUndefined();
    expect(await contarArquivos()).toBe(0);
    await agente.delete(URL).expect(200);
  });

  it("copiarImagens duplica (ids diferentes, mesmo conteúdo) e mantém textos", async () => {
    const original = await salvarImagem({ chave: "heroImagem", mime: "image/png", conteudo: PNG });
    const copia = await copiarImagens({ heroImagem: original, heroTitulo: "Oi" });
    expect(copia.heroTitulo).toBe("Oi");
    const nova = copia.heroImagem;
    if (!ehImagem(nova)) throw new Error("esperava imagem");
    expect(nova.arquivoId.equals(original.arquivoId)).toBe(false);
    expect(nova).toMatchObject({
      nome: original.nome,
      mime: original.mime,
      tamanho: original.tamanho,
    });
    expect(Buffer.compare(await lerTudo(abrirLeitura(nova.arquivoId)), PNG)).toBe(0);
    expect(await contarArquivos()).toBe(2);
  });

  it("abrirLeitura de id inexistente emite 404", async () => {
    await expect(lerTudo(abrirLeitura(new mongoose.Types.ObjectId()))).rejects.toMatchObject({
      status: 404,
    });
  });
});
