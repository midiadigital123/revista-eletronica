import { readFileSync } from "node:fs";
import { describe, expect, it, vi } from "vitest";
import { HEADER_SESSAO_EDICAO } from "../src/contrato/schemas.js";
import { agenteLogado, usarApp } from "./helpers.js";

// copiarImagens é do A5b; aqui só importa que a página copiada chegue ao projeto novo.
vi.mock("../src/modules/imagens/service.js", async (original) => ({
  ...(await original<typeof import("../src/modules/imagens/service.js")>()),
  copiarImagens: vi.fn(async (pagina: Record<string, unknown>) => ({ ...pagina })),
}));

const ctx = usarApp();

const fixture: unknown = JSON.parse(
  readFileSync(new URL("./fixtures/revista.json", import.meta.url), "utf8"),
);

const lerSaida = (nome: string) =>
  JSON.parse(readFileSync(new URL(`../../saida/${nome}.json`, import.meta.url), "utf8"));
const saidaLp = lerSaida("lingua-portuguesa");
const saidaMt = lerSaida("matematica");

type Agente = Awaited<ReturnType<typeof agenteLogado>>["agente"];

/** Editor logado com um projeto "sp" (5ef e 9ef) já criado e bloqueado para ele. */
async function comProjeto(anos: string[] = ["5ef", "9ef"]) {
  const logado = await agenteLogado(ctx.app);
  await logado.agente
    .post("/api/projetos")
    .send({ slug: "sp", nome: "São Paulo", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio", anos } })
    .expect(201);
  return logado;
}

const LP = "/api/projetos/sp/cadernos/lingua-portuguesa";
const D01 = `${LP}/anos/5ef/descritores/D01`;

async function comDescritor() {
  const logado = await comProjeto();
  await logado.agente
    .post(`${LP}/anos/5ef/descritores`)
    .send({
      codigo: "D01",
      topic: "Leitura",
      bncc: { practices: "P", knowledge: "K", skills: ["EF01"] },
      scale: { "padrao-1": [{ level: 50, content: "a" }], "padrao-2": [], "padrao-3": [], "padrao-4": [] },
    })
    .expect(201);
  return logado;
}

const erro400 = (campo: string) => ({ erro: expect.any(String), campo, detalhes: expect.any(Array) });

describe("projetos", () => {
  it("POST vazio cria 5ef/9ef/3em com faixa e cortes padrão, já bloqueado para o criador", async () => {
    const { agente, usuario } = await agenteLogado(ctx.app);
    const r = await agente
      .post("/api/projetos")
      .send({ slug: "sp-2026", nome: "SP", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio" } })
      .expect(201);
    expect(r.body.cadernos).toEqual([
      {
        id: "lingua-portuguesa",
        anos: ["5ef", "9ef", "3em"].map((ano) => ({
          ano,
          scaleRange: { min: 0, max: 500 },
          cortes: { "padrao-1": 125, "padrao-2": 250, "padrao-3": 375 },
          descritores: [],
        })),
      },
    ]);
    expect(r.body).toMatchObject({ slug: "sp-2026", nome: "SP", pagina: {} });
    expect(r.body.bloqueio).toMatchObject({ usuarioId: usuario.id, nome: usuario.nome });
    // Já pode escrever sem POST /bloqueio.
    await agente.patch("/api/projetos/sp-2026").send({ nome: "SP 2" }).expect(200);
  });

  it("POST: 409 slug ocupado, 400 schema, 400 sem X-Sessao-Edicao", async () => {
    const { agente } = await comProjeto();
    const dup = await agente
      .post("/api/projetos")
      .send({ slug: "sp", nome: "Outro", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio" } })
      .expect(409);
    expect(dup.body).toEqual({ erro: "Já existe um projeto com esse identificador", campo: "slug" });
    const inv = await agente
      .post("/api/projetos")
      .send({ slug: "SP!", nome: "x", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio" } })
      .expect(400);
    expect(inv.body).toMatchObject(erro400("slug"));
    await agente
      .post("/api/projetos")
      .set(HEADER_SESSAO_EDICAO, "")
      .send({ slug: "rj", nome: "RJ", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio" } })
      .expect(400);
  });

  it("POST vazio com Alfabetização gera os 2 cadernos; disciplinas na ordem de CADERNOS, sem repetir", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const r = await agente
      .post("/api/projetos")
      .send({ slug: "alfa", nome: "Alfa", disciplinas: ["alfabetizacao"], origem: { tipo: "vazio", anos: ["2ef"] } })
      .expect(201);
    expect(r.body.cadernos.map((c: { id: string }) => c.id)).toEqual(["alfabetizacao-lp", "alfabetizacao-mat"]);
    expect(r.body.cadernos[1].anos.map((a: { ano: string }) => a.ano)).toEqual(["2ef"]);
    const todas = await agente
      .post("/api/projetos")
      .send({
        slug: "todas",
        nome: "Todas",
        disciplinas: ["alfabetizacao", "matematica", "lingua-portuguesa", "matematica"],
        origem: { tipo: "vazio" },
      })
      .expect(201);
    expect(todas.body.cadernos.map((c: { id: string }) => c.id)).toEqual([
      "lingua-portuguesa",
      "matematica",
      "alfabetizacao-lp",
      "alfabetizacao-mat",
    ]);
    const lista = await agente.get("/api/projetos").expect(200);
    expect(lista.body[0]).toMatchObject({
      slug: "alfa",
      cadernos: [
        { id: "alfabetizacao-lp", anos: ["2ef"] },
        { id: "alfabetizacao-mat", anos: ["2ef"] },
      ],
    });
    const sem = await agente
      .post("/api/projetos")
      .send({ slug: "nada", nome: "Nada", disciplinas: [], origem: { tipo: "vazio" } })
      .expect(400);
    expect(sem.body.campo).toBe("disciplinas");
  });

  it("importar a fixture e exportar de volta (GET /cadernos/:caderno/revista) devolve a mesma revista", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const r = await agente
      .post("/api/projetos")
      .send({
        slug: "fx",
        nome: "Fixture",
        disciplinas: ["lingua-portuguesa"],
        origem: { tipo: "importar", cadernos: { "lingua-portuguesa": fixture } },
      })
      .expect(201);
    const [lp] = r.body.cadernos;
    expect(lp.anos.map((a: { ano: string }) => a.ano)).toEqual(["5ef", "9ef", "3em"]);
    expect(lp.anos[0].descritores).toHaveLength(40);
    const exportada = await agente.get("/api/projetos/fx/cadernos/lingua-portuguesa/revista").expect(200);
    expect(exportada.body).toEqual(fixture);
    await agente.get("/api/projetos/fx/cadernos/matematica/revista").expect(404);
    await agente.get("/api/projetos/fx/cadernos/fisica/revista").expect(400);
  });

  it("importar saida/*.json (sem pagina) como cadernos de Alfabetização", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const r = await agente
      .post("/api/projetos")
      .send({
        slug: "alfa",
        nome: "Alfa",
        disciplinas: ["alfabetizacao"],
        origem: { tipo: "importar", cadernos: { "alfabetizacao-lp": saidaLp, "alfabetizacao-mat": saidaMt } },
      })
      .expect(201);
    expect(r.body.pagina).toEqual({});
    expect(
      r.body.cadernos.map((c: { id: string; anos: { ano: string; descritores: unknown[] }[] }) => [
        c.id,
        c.anos.map((a) => `${a.ano}:${a.descritores.length}`),
      ]),
    ).toEqual([
      ["alfabetizacao-lp", ["2ef:8", "5ef:15"]],
      ["alfabetizacao-mat", ["2ef:33", "5ef:28"]],
    ]);
    const mt = await agente.get("/api/projetos/alfa/cadernos/alfabetizacao-mat/revista").expect(200);
    expect(mt.body["2ef"].D01).toEqual(saidaMt["2ef"].D01);
  });

  it("importar: falta a revista de um caderno marcado → 400 com o campo do caderno", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const r = await agente
      .post("/api/projetos")
      .send({
        slug: "alfa",
        nome: "Alfa",
        disciplinas: ["alfabetizacao"],
        origem: { tipo: "importar", cadernos: { "alfabetizacao-lp": saidaLp } },
      })
      .expect(400);
    expect(r.body).toMatchObject({ campo: "origem.cadernos.alfabetizacao-mat" });
    await agente.get("/api/projetos/alfa").expect(404);
  });

  it("importar: regra de domínio violada → 400 com campo prefixado pelo ano", async () => {
    const { agente } = await agenteLogado(ctx.app);
    const revista = {
      "5ef": {
        scaleRange: { min: 0, max: 100 },
        cortes: { "padrao-1": 50, "padrao-2": 40, "padrao-3": 90 },
        D01: { scale: { "padrao-1": [{ level: 200, content: "x" }], "padrao-2": [], "padrao-3": [], "padrao-4": [] } },
      },
    };
    const r = await agente
      .post("/api/projetos")
      .send({
        slug: "x",
        nome: "X",
        disciplinas: ["matematica"],
        origem: { tipo: "importar", cadernos: { matematica: revista } },
      })
      .expect(400);
    expect(r.body.campo).toBe("matematica.5ef.cortes.padrao-2");
    expect(r.body.detalhes.map((d: { campo: string }) => d.campo)).toContain(
      "matematica.5ef.descritores.D01.scale.padrao-1.0.level",
    );
  });

  it("copiar duplica página e cadernos das disciplinas marcadas; origem inexistente → 404", async () => {
    const { agente } = await comDescritor();
    await agente.patch("/api/projetos/sp/pagina").send({ heroTitulo: "Título" }).expect(200);
    const r = await agente
      .post("/api/projetos")
      .send({ slug: "copia", nome: "Cópia", disciplinas: ["lingua-portuguesa"], origem: { tipo: "copiar", de: "sp" } })
      .expect(201);
    const fonte = await agente.get("/api/projetos/sp").expect(200);
    expect(r.body.pagina).toEqual({ heroTitulo: "Título" });
    expect(r.body.cadernos).toEqual(fonte.body.cadernos);
    await agente
      .post("/api/projetos")
      .send({ slug: "c2", nome: "C2", disciplinas: ["lingua-portuguesa"], origem: { tipo: "copiar", de: "nada" } })
      .expect(404);
  });

  it("copiar só copia os cadernos marcados; caderno ausente na origem → 400", async () => {
    const { agente } = await agenteLogado(ctx.app);
    await agente
      .post("/api/projetos")
      .send({ slug: "base", nome: "Base", disciplinas: ["lingua-portuguesa", "alfabetizacao"], origem: { tipo: "vazio" } })
      .expect(201);
    const r = await agente
      .post("/api/projetos")
      .send({ slug: "so-alfa", nome: "Só Alfa", disciplinas: ["alfabetizacao"], origem: { tipo: "copiar", de: "base" } })
      .expect(201);
    expect(r.body.cadernos.map((c: { id: string }) => c.id)).toEqual(["alfabetizacao-lp", "alfabetizacao-mat"]);
    const falta = await agente
      .post("/api/projetos")
      .send({ slug: "mt", nome: "MT", disciplinas: ["matematica"], origem: { tipo: "copiar", de: "base" } })
      .expect(400);
    expect(falta.body).toEqual({ erro: "O projeto de origem não tem Matemática", campo: "disciplinas" });
  });

  it("GET / lista resumos por nome; GET /:slug 404 se não existe", async () => {
    const { agente } = await comProjeto();
    await agente
      .post("/api/projetos")
      .send({ slug: "ac", nome: "Acre", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio", anos: ["3em"] } })
      .expect(201);
    const r = await agente.get("/api/projetos").expect(200);
    expect(r.body.map((p: { nome: string }) => p.nome)).toEqual(["Acre", "São Paulo"]);
    expect(r.body[1]).toMatchObject({
      slug: "sp",
      cadernos: [{ id: "lingua-portuguesa", anos: ["5ef", "9ef"] }],
      bloqueio: expect.any(Object) });
    await agente.get("/api/projetos/nada").expect(404);
  });

  it("PATCH renomeia slug e nome (o bloqueio continua); 409 se o slug está ocupado", async () => {
    const { agente } = await comProjeto();
    await agente
      .post("/api/projetos")
      .send({ slug: "rj", nome: "RJ", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio" } })
      .expect(201);
    const conf = await agente.patch("/api/projetos/sp").send({ slug: "rj" }).expect(409);
    expect(conf.body.campo).toBe("slug");
    const r = await agente.patch("/api/projetos/sp").send({ slug: "sao-paulo", nome: "SP" }).expect(200);
    expect(r.body).toMatchObject({ slug: "sao-paulo", nome: "SP" });
    await agente.get("/api/projetos/sp").expect(404);
    await agente.patch("/api/projetos/sao-paulo").send({ nome: "SP 2" }).expect(200);
    await agente.patch("/api/projetos/sao-paulo").send({}).expect(400);
  });

  it("DELETE exclui (logicamente) e libera o slug", async () => {
    const { agente } = await comProjeto();
    await agente.delete("/api/projetos/sp").expect(204);
    await agente.get("/api/projetos/sp").expect(404);
    expect((await agente.get("/api/projetos").expect(200)).body).toEqual([]);
    await agente
      .post("/api/projetos")
      .send({ slug: "sp", nome: "De novo", disciplinas: ["lingua-portuguesa"], origem: { tipo: "vazio" } })
      .expect(201);
  });
});

describe("página", () => {
  it("PATCH define textos; null, \"\" e [] removem; chave desconhecida → 400", async () => {
    const { agente } = await comProjeto();
    const r = await agente
      .patch("/api/projetos/sp/pagina")
      .send({ heroTitulo: " Título ", introParagrafos: ["a", "", "b"] })
      .expect(200);
    expect(r.body).toEqual({ heroTitulo: "Título", introParagrafos: ["a", "b"] });
    expect((await agente.patch("/api/projetos/sp/pagina").send({ heroTitulo: null }).expect(200)).body).toEqual({
      introParagrafos: ["a", "b"],
    });
    expect((await agente.patch("/api/projetos/sp/pagina").send({ introParagrafos: [] }).expect(200)).body).toEqual({});
    await agente.patch("/api/projetos/sp/pagina").send({ heroTitulo: "x" }).expect(200);
    expect((await agente.patch("/api/projetos/sp/pagina").send({ heroTitulo: "" }).expect(200)).body).toEqual({});
    await agente.patch("/api/projetos/sp/pagina").send({ heroImagem: "x" }).expect(400);
    await agente.patch("/api/projetos/sp/pagina").send({ outra: "x" }).expect(400);
  });
});

describe("anos", () => {
  it("POST cria (201 AnoProjeto); 409 duplicado; 400 cortes fora da faixa", async () => {
    const { agente } = await comProjeto();
    const r = await agente
      .post(`${LP}/anos`)
      .send({ ano: "3em", scaleRange: { min: 100, max: 600 }, cortes: { "padrao-1": 200, "padrao-2": 300, "padrao-3": 400 } })
      .expect(201);
    expect(r.body).toEqual({
      ano: "3em",
      scaleRange: { min: 100, max: 600 },
      cortes: { "padrao-1": 200, "padrao-2": 300, "padrao-3": 400 },
      descritores: [],
    });
    const dup = await agente.post(`${LP}/anos`).send({ ano: "5ef" }).expect(409);
    expect(dup.body.campo).toBe("ano");
    await agente.delete(`${LP}/anos/3em`).expect(204);
    const inv = await agente
      .post(`${LP}/anos`)
      .send({ ano: "3em", scaleRange: { min: 0, max: 100 } })
      .expect(400);
    expect(inv.body).toMatchObject(erro400("cortes.padrao-1"));
  });

  it("PATCH altera faixa e cortes; reduzir a faixa deixando nível de fora → 400 com o descritor", async () => {
    const { agente } = await comDescritor();
    const r = await agente
      .patch(`${LP}/anos/5ef`)
      .send({ cortes: { "padrao-1": 100, "padrao-2": 200, "padrao-3": 300 } })
      .expect(200);
    expect(r.body).toMatchObject({ ano: "5ef", cortes: { "padrao-1": 100 }, descritores: [{ codigo: "D01" }] });
    const red = await agente
      .patch(`${LP}/anos/5ef`)
      .send({ scaleRange: { min: 60, max: 500 } })
      .expect(400);
    expect(red.body.detalhes).toContainEqual({
      campo: "descritores.D01.scale.padrao-1.0.level",
      erro: expect.any(String),
    });
    await agente.patch(`${LP}/anos/3em`).send({ cortes: { "padrao-1": 1, "padrao-2": 2, "padrao-3": 3 } }).expect(404);
    await agente.patch(`${LP}/anos/5ef`).send({ scaleRange: { min: 5, max: 5 } }).expect(400);
  });

  it("POST aceita qualquer etapa <n>ef/<n>em e ordena EF → EM; formato inválido → 400", async () => {
    const { agente } = await comProjeto(["5ef", "9ef", "3em"]);
    await agente.post(`${LP}/anos`).send({ ano: "2ef" }).expect(201);
    const r = await agente.get("/api/projetos/sp").expect(200);
    expect(r.body.cadernos[0].anos.map((a: { ano: string }) => a.ano)).toEqual(["2ef", "5ef", "9ef", "3em"]);
    for (const ano of ["10ef", "4em", "xyz"]) {
      const inv = await agente.post(`${LP}/anos`).send({ ano }).expect(400);
      expect(inv.body).toMatchObject(erro400("ano"));
    }
  });

  it("DELETE remove; 404 se não existe; 400 se for o último", async () => {
    const { agente } = await comProjeto();
    await agente.delete(`${LP}/anos/9ef`).expect(204);
    await agente.delete(`${LP}/anos/9ef`).expect(404);
    await agente.delete("/api/projetos/sp/cadernos/matematica/anos/5ef").expect(404);
    const r = await agente.delete(`${LP}/anos/5ef`).expect(400);
    expect(r.body.erro).toBe("O caderno precisa ter ao menos um ano");
  });
});

describe("descritores", () => {
  it("POST cria com defaults (201 Descritor); 409 código repetido; 400 nível fora; 404 ano", async () => {
    const { agente } = await comDescritor();
    const r = await agente.post(`${LP}/anos/5ef/descritores`).send({ codigo: "D02" }).expect(201);
    expect(r.body).toEqual({
      codigo: "D02",
      topic: "",
      description: "",
      prerequisites: [],
      bncc: { practices: "", knowledge: "", skills: [] },
      scale: { "padrao-1": [], "padrao-2": [], "padrao-3": [], "padrao-4": [] },
    });
    const dup = await agente.post(`${LP}/anos/5ef/descritores`).send({ codigo: "D01" }).expect(409);
    expect(dup.body.campo).toBe("codigo");
    await agente
      .post(`${LP}/anos/5ef/descritores`)
      .send({ codigo: "D03", scale: { "padrao-1": [{ level: 900, content: "x" }], "padrao-2": [], "padrao-3": [], "padrao-4": [] } })
      .expect(400);
    await agente.post(`${LP}/anos/3em/descritores`).send({ codigo: "D01" }).expect(404);
    await agente.post(`${LP}/anos/5ef/descritores`).send({ codigo: "X1" }).expect(400);
  });

  it("PATCH renomeia e mescla bncc parcial; 409 código ocupado; 404 inexistente", async () => {
    const { agente } = await comDescritor();
    await agente.post(`${LP}/anos/5ef/descritores`).send({ codigo: "D02" }).expect(201);
    const r = await agente
      .patch(D01)
      .send({ codigo: "D05", prerequisites: ["x", ""], bncc: { knowledge: "K2" } })
      .expect(200);
    expect(r.body).toMatchObject({
      codigo: "D05",
      topic: "Leitura",
      prerequisites: ["x"],
      bncc: { practices: "P", knowledge: "K2", skills: ["EF01"] },
    });
    const conf = await agente.patch(`${LP}/anos/5ef/descritores/D05`).send({ codigo: "D02" }).expect(409);
    expect(conf.body.campo).toBe("codigo");
    await agente.patch(D01).send({ topic: "x" }).expect(404);
    const ano = await agente.get("/api/projetos/sp").expect(200);
    expect(ano.body.cadernos[0].anos[0].descritores.map((d: { codigo: string }) => d.codigo)).toEqual(["D02", "D05"]);
  });

  it("DELETE remove; 404 se não existe", async () => {
    const { agente } = await comDescritor();
    await agente.delete(D01).expect(204);
    await agente.delete(D01).expect(404);
  });

  it("PUT escala substitui o padrão, ordena por nível e troca content vazio por ---", async () => {
    const { agente } = await comDescritor();
    const r = await agente
      .put(`${D01}/escala/padrao-2`)
      .send([
        { level: 150, content: "b" },
        { level: 200, content: "" },
      ])
      .expect(200);
    expect(r.body).toEqual([
      { level: 200, content: "---" },
      { level: 150, content: "b" },
    ]);
    const p = await agente.get("/api/projetos/sp").expect(200);
    expect(p.body.cadernos[0].anos[0].descritores[0].scale["padrao-2"]).toEqual(r.body);
    await agente.put(`${D01}/escala/padrao-5`).send([]).expect(404);
    await agente.put(`${LP}/anos/5ef/descritores/D09/escala/padrao-1`).send([]).expect(404);
    const fora = await agente.put(`${D01}/escala/padrao-1`).send([{ level: -1, content: "x" }]).expect(400);
    expect(fora.body.campo).toBe("descritores.D01.scale.padrao-1.0.level");
  });
});

describe("bloqueio nas rotas de escrita", () => {
  const escritas: [string, string, object?][] = [
    ["patch", "/api/projetos/sp", { nome: "x" }],
    ["delete", "/api/projetos/sp"],
    ["patch", "/api/projetos/sp/pagina", { heroTitulo: "x" }],
    ["post", `${LP}/anos`, { ano: "3em" }],
    ["patch", `${LP}/anos/5ef`, { scaleRange: { min: 0, max: 600 } }],
    ["delete", `${LP}/anos/9ef`],
    ["post", `${LP}/anos/5ef/descritores`, { codigo: "D02" }],
    ["patch", D01, { topic: "x" }],
    ["delete", D01],
    ["put", `${D01}/escala/padrao-1`, []],
  ];

  const enviar = (agente: Agente, metodo: string, url: string, corpo?: object, aba?: string) => {
    const req =
      metodo === "post" ? agente.post(url)
      : metodo === "patch" ? agente.patch(url)
      : metodo === "put" ? agente.put(url)
      : agente.delete(url);
    if (aba) req.set(HEADER_SESSAO_EDICAO, aba);
    return corpo ? req.send(corpo) : req;
  };

  it.each(escritas)("%s %s → 423 para outro usuário e para outra aba do mesmo usuário", async (metodo, url, corpo) => {
    const dono = await comDescritor();
    const outro = await agenteLogado(ctx.app);
    const r = await enviar(outro.agente, metodo, url, corpo).expect(423);
    expect(r.body.bloqueio).toMatchObject({ nome: dono.usuario.nome });
    await enviar(dono.agente, metodo, url, corpo, "outra-aba").expect(423);
  });

  it("sem bloqueio de ninguém → 423 com bloqueio null", async () => {
    const { agente } = await comProjeto();
    await agente.delete("/api/projetos/sp/bloqueio").expect(204);
    const r = await agente.patch("/api/projetos/sp").send({ nome: "x" }).expect(423);
    expect(r.body.bloqueio).toBeNull();
  });
});
