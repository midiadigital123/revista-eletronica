import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { anosDaRevista, revistaDosAnos } from "../src/contrato/revista.js";
import { CORTES_PADRAO, Revista, problemasDoAno } from "../src/contrato/schemas.js";

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
