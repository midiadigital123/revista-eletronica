import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { anosDaRevista, revistaDosAnos } from "../src/contrato/revista.js";
import {
  cadernosDasDisciplinas,
  CORTES_PADRAO,
  CriarProjetoEntrada,
  Revista,
  rotuloCaderno,
  rotuloDisciplina,
  compararAnos,
  problemasDoAno,
  rotuloAno,
  rotuloAnoLongo,
} from "../src/contrato/schemas.js";

const fixture = JSON.parse(readFileSync(new URL("./fixtures/revista.json", import.meta.url), "utf8"));
const descritoresOriginal = JSON.parse(
  readFileSync(new URL("../../descritores.json", import.meta.url), "utf8"),
);

describe("contrato: formato da revista", () => {
  it("fixture → anos → revista preserva os dados", () => {
    const revista = Revista.parse(fixture);
    const anos = anosDaRevista(revista);
    expect(anos.map((a) => a.ano)).toEqual(["5ef", "9ef", "3em"]);
    expect(anos[0]!.descritores).toHaveLength(40);
    expect(revistaDosAnos(anos, revista.pagina ?? {})).toEqual(revista);
  });

  it("aceita o descritores.json original (sem cortes) usando os cortes padrão", () => {
    const anos = anosDaRevista(Revista.parse(descritoresOriginal));
    expect(anos[0]!.cortes).toEqual(CORTES_PADRAO);
    expect(anos.flatMap(problemasDoAno)).toEqual([]);
  });

  it("recusa código de descritor inválido", () => {
    const r = Revista.safeParse({ "5ef": { scaleRange: { min: 0, max: 500 }, D1: {} } });
    expect(r.success).toBe(false);
  });

  it("aponta cortes fora de ordem e nível fora da faixa", () => {
    const [ano] = anosDaRevista(Revista.parse(fixture));
    const problemas = problemasDoAno({
      ...ano!,
      cortes: { "padrao-1": 125, "padrao-2": 100, "padrao-3": 375 },
      scaleRange: { min: 0, max: 280 },
    });
    expect(problemas.map((p) => p.campo)).toEqual(
      expect.arrayContaining(["cortes.padrao-2", "cortes.padrao-3", "descritores.D01.scale.padrao-3.0.level"]),
    );
  });
});

describe("contrato: etapas (anos)", () => {
  const anoMinimo = { scaleRange: { min: 0, max: 500 } };

  it("aceita etapa fora da lista padrão e anosDaRevista a devolve em ordem", () => {
    const r = Revista.safeParse({ "3em": anoMinimo, "2ef": anoMinimo });
    expect(r.success).toBe(true);
    expect(anosDaRevista(r.data!).map((a) => a.ano)).toEqual(["2ef", "3em"]);
  });

  it("recusa chave de etapa inválida apontando a chave", () => {
    const r = Revista.safeParse({ "5ef": anoMinimo, abc: anoMinimo });
    expect(r.success).toBe(false);
    expect(r.error!.issues.map((i) => i.path)).toContainEqual(["abc"]);
    expect(Revista.safeParse({ "4em": anoMinimo }).success).toBe(false);
    expect(Revista.safeParse({ pagina: {} }).success).toBe(false);
  });

  it("rotuloAno / rotuloAnoLongo", () => {
    expect(rotuloAno("5ef")).toBe("5º EF");
    expect(rotuloAno("3em")).toBe("3ª EM");
    expect(rotuloAno("xyz")).toBe("xyz");
    expect(rotuloAnoLongo("2ef")).toBe("2º Ano do Ensino Fundamental");
    expect(rotuloAnoLongo("1em")).toBe("1ª Série do Ensino Médio");
    expect(rotuloAnoLongo("xyz")).toBe("xyz");
  });

  it("compararAnos: EF antes de EM, depois número", () => {
    expect(["3em", "9ef", "1em", "2ef", "5ef"].sort(compararAnos)).toEqual(["2ef", "5ef", "9ef", "1em", "3em"]);
  });
});

describe("contrato: disciplinas e cadernos", () => {
  const base = { slug: "go", nome: "Goiás", disciplinas: ["alfabetizacao"] };

  it("CriarProjetoEntrada aceita as 3 origens", () => {
    expect(CriarProjetoEntrada.parse({ ...base, origem: { tipo: "vazio" } }).origem).toEqual({
      tipo: "vazio",
      anos: ["5ef", "9ef", "3em"],
    });
    expect(CriarProjetoEntrada.safeParse({ ...base, origem: { tipo: "copiar", de: "sp" } }).success).toBe(true);
    const importar = CriarProjetoEntrada.safeParse({
      ...base,
      origem: { tipo: "importar", cadernos: { "alfabetizacao-lp": fixture } },
    });
    expect(importar.success).toBe(true);
  });

  it("CriarProjetoEntrada recusa disciplina vazia/desconhecida e caderno desconhecido", () => {
    const vazio = { tipo: "vazio" };
    expect(CriarProjetoEntrada.safeParse({ ...base, disciplinas: [], origem: vazio }).success).toBe(false);
    expect(CriarProjetoEntrada.safeParse({ ...base, disciplinas: ["fisica"], origem: vazio }).success).toBe(false);
    expect(
      CriarProjetoEntrada.safeParse({ ...base, origem: { tipo: "importar", cadernos: { fisica: fixture } } })
        .success,
    ).toBe(false);
    expect(CriarProjetoEntrada.safeParse({ ...base, origem: { tipo: "importar", revista: fixture } }).success).toBe(
      false,
    );
  });

  it("cadernosDasDisciplinas segue a ordem de CADERNOS, sem repetir", () => {
    expect(cadernosDasDisciplinas(["alfabetizacao", "lingua-portuguesa", "alfabetizacao"])).toEqual([
      "lingua-portuguesa",
      "alfabetizacao-lp",
      "alfabetizacao-mat",
    ]);
  });

  it("rótulos", () => {
    expect(rotuloDisciplina("alfabetizacao")).toBe("Alfabetização");
    expect(rotuloCaderno("alfabetizacao-mat")).toBe("Alfabetização · Matemática");
    expect(rotuloCaderno("lingua-portuguesa")).toBe("Língua Portuguesa");
  });
});
