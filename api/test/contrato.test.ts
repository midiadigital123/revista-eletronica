import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { anosDaRevista, revistaDosAnos } from "../src/contrato/revista.js";
import {
  cadernosDasDisciplinas,
  AtualizarProjetoEntrada,
  CORES_PADRAO,
  CORTES_PADRAO,
  Cores,
  CriarProjetoEntrada,
  Escala,
  linhasVaziasDoPasso,
  mesmasCores,
  niveisDoPasso,
  Revista,
  rotuloCaderno,
  rotuloDisciplina,
  compararAnos,
  problemasDoAno,
  rotuloAno,
  rotuloAnoLongo,
} from "../src/contrato/schemas.js";

const fixture = JSON.parse(
  readFileSync(new URL("./fixtures/revista.json", import.meta.url), "utf8"),
);
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
      expect.arrayContaining([
        "cortes.padrao-2",
        "cortes.padrao-3",
        "descritores.D01.scale.padrao-3.0.level",
      ]),
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
    expect(["3em", "9ef", "1em", "2ef", "5ef"].sort(compararAnos)).toEqual([
      "2ef",
      "5ef",
      "9ef",
      "1em",
      "3em",
    ]);
  });
});

describe("contrato: disciplinas e cadernos", () => {
  const base = { slug: "go", nome: "Goiás", disciplinas: ["matematica"] };

  it("CriarProjetoEntrada aceita as 3 origens", () => {
    expect(CriarProjetoEntrada.parse({ ...base, origem: { tipo: "vazio" } }).origem).toEqual({
      tipo: "vazio",
      anos: ["5ef", "9ef", "3em"],
    });
    expect(
      CriarProjetoEntrada.safeParse({ ...base, origem: { tipo: "copiar", de: "sp" } }).success,
    ).toBe(true);
    const importar = CriarProjetoEntrada.safeParse({
      ...base,
      origem: { tipo: "importar", cadernos: { matematica: fixture } },
    });
    expect(importar.success).toBe(true);
  });

  it("CriarProjetoEntrada recusa disciplina vazia/desconhecida e caderno desconhecido", () => {
    const vazio = { tipo: "vazio" };
    expect(CriarProjetoEntrada.safeParse({ ...base, disciplinas: [], origem: vazio }).success).toBe(
      false,
    );
    expect(
      CriarProjetoEntrada.safeParse({ ...base, disciplinas: ["fisica"], origem: vazio }).success,
    ).toBe(false);
    expect(
      CriarProjetoEntrada.safeParse({
        ...base,
        origem: { tipo: "importar", cadernos: { fisica: fixture } },
      }).success,
    ).toBe(false);
    expect(
      CriarProjetoEntrada.safeParse({ ...base, origem: { tipo: "importar", revista: fixture } })
        .success,
    ).toBe(false);
  });

  it("cadernosDasDisciplinas segue a ordem de CADERNOS, sem repetir", () => {
    expect(cadernosDasDisciplinas(["matematica", "lingua-portuguesa", "matematica"])).toEqual([
      "lingua-portuguesa",
      "matematica",
    ]);
  });

  it("rótulos", () => {
    expect(rotuloDisciplina("matematica")).toBe("Matemática");
    expect(rotuloCaderno("matematica")).toBe("Matemática");
    expect(rotuloCaderno("lingua-portuguesa")).toBe("Língua Portuguesa");
  });
});

describe("contrato: passo", () => {
  it("niveisDoPasso: 0–500 de 25 em 25 dá 20 níveis (0…475)", () => {
    const n = niveisDoPasso({ min: 0, max: 500 }, 25);
    expect(n).toHaveLength(20);
    expect(n[0]).toBe(0);
    expect(n.at(-1)).toBe(475);
  });
  it("linhasVaziasDoPasso distribui pelos cortes e não duplica nível existente", () => {
    const ano = {
      scaleRange: { min: 0, max: 500 },
      cortes: { "padrao-1": 150, "padrao-2": 200, "padrao-3": 250 },
      passo: 25,
    };
    const escala = Escala.parse({ "padrao-3": [{ level: 150, content: "manual" }] }); // 150 em outro padrão
    const r = linhasVaziasDoPasso(ano, escala);
    expect(r["padrao-1"].map((l) => l.level)).toEqual([125, 100, 75, 50, 25, 0]);
    expect(r["padrao-2"].map((l) => l.level)).toEqual([175]); // 150 já existe
    expect(r["padrao-3"].map((l) => l.level)).toEqual([225, 200, 150]);
    expect(r["padrao-4"]).toHaveLength(10);
    expect(r["padrao-4"][0]).toEqual({ level: 475, fim: 500, content: "---" });
  });
  it("problemasDoAno recusa passo que gera mais de 200 linhas", () => {
    const p = problemasDoAno({
      ano: "2ef",
      scaleRange: { min: 0, max: 1000 },
      cortes: { "padrao-1": 350, "padrao-2": 400, "padrao-3": 500 },
      passo: 1,
      descritores: [],
    });
    expect(p).toContainEqual(expect.objectContaining({ campo: "passo" }));
  });
  it("problemasDoAno recusa mais de 200 linhas num padrão", () => {
    const linhas = Array.from({ length: 201 }, (_, i) => ({ level: i, content: "x" }));
    const vazio = { "padrao-1": [], "padrao-2": [], "padrao-3": [], "padrao-4": [] };
    const p = problemasDoAno({
      ano: "5ef",
      scaleRange: { min: 0, max: 500 },
      cortes: { "padrao-1": 100, "padrao-2": 200, "padrao-3": 300 },
      descritores: [
        {
          codigo: "D01",
          topic: "",
          description: "",
          prerequisites: [],
          bncc: { practices: "", knowledge: "", skills: [] },
          scale: { ...vazio, "padrao-1": linhas },
        },
      ],
    } as never);
    expect(p).toContainEqual({
      campo: "descritores.D01.scale.padrao-1",
      erro: "No máximo 200 linhas por padrão",
    });
  });
  it("revista: passo vai e volta no JSON; sem passo continua válido", () => {
    const anos = anosDaRevista(
      Revista.parse({ "5ef": { scaleRange: { min: 0, max: 500 }, passo: 25 } }),
    );
    expect(anos[0]!.passo).toBe(25);
    expect(revistaDosAnos(anos, {})["5ef"]).toMatchObject({ passo: 25 });
    expect(
      anosDaRevista(Revista.parse({ "5ef": { scaleRange: { min: 0, max: 500 } } }))[0],
    ).not.toHaveProperty("passo");
  });
  it("cores: aceita #rrggbb, recusa nome, abreviação e injeção de CSS", () => {
    const ok = { ...CORES_PADRAO, "padrao-1": "#0A3d2F" };
    expect(Cores.safeParse(ok).success).toBe(true);
    for (const ruim of ["red", "#fff", "red;}</style>"])
      expect(Cores.safeParse({ ...CORES_PADRAO, "padrao-2": ruim }).success).toBe(false);
  });
  it("AtualizarProjetoEntrada aceita { cores: null } (restaura o padrão)", () => {
    expect(AtualizarProjetoEntrada.parse({ cores: null })).toEqual({ cores: null });
  });
  it("mesmasCores: null equivale ao padrão e ignora maiúsculas", () => {
    expect(mesmasCores(null, CORES_PADRAO)).toBe(true);
    expect(mesmasCores({ ...CORES_PADRAO, "padrao-1": "#F72628" }, null)).toBe(true);
    expect(mesmasCores({ ...CORES_PADRAO, "padrao-1": "#000000" }, null)).toBe(false);
  });
});
