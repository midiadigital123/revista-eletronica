import mongoose from "mongoose";
import supertest from "supertest";
import { describe, expect, it } from "vitest";
import { ITEM_MAX_BYTES } from "../src/contrato/schemas.js";
import { agenteLogado, usarApp } from "./helpers.js";

const ctx = usarApp();

// Só o cabeçalho importa para a API; o resto é preenchimento.
const PDF = Buffer.concat([Buffer.from("%PDF-1.4\n"), Buffer.alloc(32, 7)]);
// Assinaturas mínimas de PNG e JPEG (a API só confere os bytes mágicos).
const PNG = Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), Buffer.alloc(32, 9)]);
const JPG = Buffer.concat([Buffer.from([0xff, 0xd8, 0xff, 0xe0]), Buffer.alloc(32, 5)]);
const URL = "/api/projetos/sp/itens";
const LP = "/api/projetos/sp/cadernos/lingua-portuguesa";

const binario = (res: supertest.Response, cb: (e: Error | null, b: Buffer) => void) => {
  const partes: Buffer[] = [];
  res.on("data", (p: Buffer) => partes.push(p));
  res.on("end", () => cb(null, Buffer.concat(partes)));
};

/** Editor logado com o projeto "sp" (5ef) criado e bloqueado para ele. */
async function editor() {
  const logado = await agenteLogado(ctx.app);
  await logado.agente
    .post("/api/projetos")
    .send({ slug: "sp", nome: "SP", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio", anos: ["5ef"] } })
    .expect(201);
  return logado.agente;
}

const enviar = (agente: supertest.Agent, conteudo: Buffer, contentType = "application/pdf") =>
  agente.post(URL).attach("arquivo", conteudo, { filename: "item 1.pdf", contentType });

/** Cria um descritor cujas linhas apontam para os itens dados. */
const criarDescritor = (agente: supertest.Agent, itens: object[]) =>
  agente
    .post(`${LP}/anos/5ef/descritores`)
    .send({
      codigo: "D01",
      topic: "Leitura",
      bncc: { practices: "P", knowledge: "K", skills: [] },
      scale: {
        "padrao-1": [],
        "padrao-2": itens.map((item, i) => ({ level: 150 + i, content: "b", item })),
        "padrao-3": [],
        "padrao-4": [],
      },
    })
    .expect(201);

const baixar = (agente: supertest.Agent, caminho: string) =>
  agente.get(caminho).buffer(true).parse(binario).expect(200);

const contarArquivos = () => mongoose.connection.db!.collection("imagens.files").countDocuments();

describe("itens em PDF", () => {
  it("upload → 201 com ItemPdf; GET devolve os mesmos bytes como PDF", async () => {
    const agente = await editor();
    const r = await enviar(agente, PDF).expect(201);
    expect(r.body).toEqual({ id: expect.stringMatching(/^[a-f0-9]{24}$/), nome: "item 1.pdf", tamanho: PDF.length, tipo: "pdf" });

    const g = await agente.get(`${URL}/${r.body.id}`).buffer(true).parse(binario).expect(200);
    expect(g.headers["content-type"]).toBe("application/pdf");
    expect(Buffer.compare(g.body as Buffer, PDF)).toBe(0);
  });

  it("recusa conteúdo ou tipo que não é PDF, arquivo ausente (400) e > 5 MB (413)", async () => {
    const agente = await editor();
    await enviar(agente, Buffer.from("nao sou pdf")).expect(400);
    await enviar(agente, PDF, "image/png").expect(400);
    await agente.post(URL).field("x", "1").expect(400);
    await enviar(agente, Buffer.concat([PDF, Buffer.alloc(ITEM_MAX_BYTES)])).expect(413);
    expect(await contarArquivos()).toBe(0);
  });

  it("sem bloqueio → 423; projeto inexistente → 404; GET id inválido/inexistente → 404; sem sessão → 401", async () => {
    await editor();
    const { agente } = await agenteLogado(ctx.app);
    await enviar(agente, PDF).expect(423);
    await agente
      .post("/api/projetos/nao-existe/itens")
      .attach("arquivo", PDF, { filename: "a.pdf", contentType: "application/pdf" })
      .expect(404);
    await agente.get(`${URL}/xyz`).expect(404);
    await agente.get(`${URL}/${"a".repeat(24)}`).expect(404);
    await agente.get(`/api/projetos/nao-existe/itens/${"a".repeat(24)}`).expect(404);
    await supertest(ctx.app).get(`${URL}/${"a".repeat(24)}`).expect(401);
  });

  it("item da linha é persistido, vai para o preview/pacote e é mantido na cópia do projeto", async () => {
    const agente = await editor();
    const item = (await enviar(agente, PDF).expect(201)).body as { id: string };
    const linha = { level: 150, content: "b", item };
    await agente
      .post(`${LP}/anos/5ef/descritores`)
      .send({
        codigo: "D01",
        topic: "Leitura",
        bncc: { practices: "P", knowledge: "K", skills: [] },
        scale: { "padrao-1": [], "padrao-2": [linha, { level: 160, content: "c", item }], "padrao-3": [], "padrao-4": [] },
      })
      .expect(201);
    const p = await agente.get("/api/projetos/sp").expect(200);
    expect(p.body.cadernos[0].anos[0].descritores[0].scale["padrao-2"]).toContainEqual(linha);

    const caminho = `lingua-portuguesa/arquivos/itens/${item.id}.pdf`;
    const g = await agente.get(`/api/projetos/sp/preview/${caminho}`).buffer(true).parse(binario).expect(200);
    expect(g.headers["content-type"]).toBe("application/pdf");
    expect(Buffer.compare(g.body as Buffer, PDF)).toBe(0);

    const z = await agente.get("/api/projetos/sp/pacote.zip").buffer(true).parse(binario).expect(200);
    // Nome aparece 2x por entrada (cabeçalho local + diretório central): uma entrada só, sem duplicar.
    expect((z.body as Buffer).toString("latin1").split(caminho).length - 1).toBe(2);

    await agente
      .post("/api/projetos")
      .send({ slug: "copia", nome: "Cópia", disciplinas: ["lingua-portuguesa"], origem: { tipo: "copiar", de: "sp" } })
      .expect(201);
    const c = await agente.get("/api/projetos/copia").expect(200);
    expect(c.body.cadernos[0].anos[0].descritores[0].scale["padrao-2"]).toContainEqual(linha);
  });
});

describe("itens em PNG e JPG", () => {
  it.each([
    ["png", "image/png", PNG],
    ["jpg", "image/jpeg", JPG],
  ] as const)("%s sobe com tipo e volta com o mesmo Content-Type e bytes", async (tipo, mime, bytes) => {
    const agente = await editor();
    const r = await enviar(agente, bytes, mime).expect(201);
    expect(r.body).toEqual({ id: expect.stringMatching(/^[a-f0-9]{24}$/), nome: "item 1.pdf", tamanho: bytes.length, tipo });

    const g = await baixar(agente, `${URL}/${r.body.id}`);
    expect(g.headers["content-type"]).toBe(mime);
    expect(Buffer.compare(g.body as Buffer, bytes)).toBe(0);
  });

  it("recusa mime fora da lista, mime que não bate com os bytes e bytes inválidos (400)", async () => {
    const agente = await editor();
    await enviar(agente, JPG, "image/webp").expect(400);
    await enviar(agente, PDF, "image/jpeg").expect(400);
    await enviar(agente, PNG, "image/jpeg").expect(400);
    await enviar(agente, Buffer.alloc(40, 1), "image/png").expect(400);
    expect(await contarArquivos()).toBe(0);
  });

  it("item PNG vai para o preview e o pacote como .png; PDF antigo sem tipo continua .pdf", async () => {
    const agente = await editor();
    const png = (await enviar(agente, PNG, "image/png").expect(201)).body as { id: string };
    const { tipo: _tipo, ...antigo } = (await enviar(agente, PDF).expect(201)).body as { id: string; tipo: string };
    await criarDescritor(agente, [png, antigo]);

    const base = "lingua-portuguesa/arquivos/itens";
    const g = await baixar(agente, `/api/projetos/sp/preview/${base}/${png.id}.png`);
    expect(g.headers["content-type"]).toBe("image/png");
    expect(Buffer.compare(g.body as Buffer, PNG)).toBe(0);
    const p = await baixar(agente, `/api/projetos/sp/preview/${base}/${antigo.id}.pdf`);
    expect(p.headers["content-type"]).toBe("application/pdf");

    const z = ((await baixar(agente, "/api/projetos/sp/pacote.zip")).body as Buffer).toString("latin1");
    expect(z).toContain(`${base}/${png.id}.png`);
    expect(z).toContain(`${base}/${antigo.id}.pdf`);
    expect(z).not.toContain(`${png.id}.pdf`);
  });

  it("GET de item antigo (GridFS sem mime nos metadados) responde como PDF", async () => {
    const agente = await editor();
    const { id } = (await enviar(agente, PDF).expect(201)).body as { id: string };
    await mongoose.connection.db!
      .collection("imagens.files")
      .updateOne({ _id: new mongoose.Types.ObjectId(id) }, { $unset: { metadata: "" } });
    const g = await baixar(agente, `${URL}/${id}`);
    expect(g.headers["content-type"]).toBe("application/pdf");
  });
});
