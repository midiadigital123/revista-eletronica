import { readFileSync } from "node:fs";
import ExcelJS from "exceljs";
import { describe, expect, it } from "vitest";
import {
  CORES_PADRAO,
  linhasVaziasDoPasso,
  Revista,
  type AnoProjeto,
  type LinhaEscala,
} from "../src/contrato/schemas.js";
import { anosDaRevista } from "../src/contrato/revista.js";
import {
  celulaDoNivel,
  gerarPlanilha,
  niveisDaPlanilha,
  nomePlanilha,
  planilhasDoCaderno,
  separarHabilidades,
} from "../src/modules/planilhas/service.js";

const projeto = { nome: "São Paulo", cores: null };

const ano5ef = (extra: Partial<AnoProjeto> = {}): AnoProjeto => {
  const base = {
    ano: "5ef",
    scaleRange: { min: 0, max: 500 },
    cortes: { "padrao-1": 150, "padrao-2": 200, "padrao-3": 250 },
    passo: 25,
    ...extra,
  };
  const vazia = { "padrao-1": [], "padrao-2": [], "padrao-3": [], "padrao-4": [] };
  return {
    ...base,
    descritores: [
      {
        codigo: "D01",
        topic: "Localizar",
        description: "Localizar informação",
        prerequisites: ["a", "b"],
        bncc: { practices: "Leitura", knowledge: "Texto", skills: ["EF15LP02", "(EF15LP03) Localizar."] },
        scale: linhasVaziasDoPasso(base, vazia),
      },
    ],
  };
};

const ler = async (buf: Buffer) => {
  const wb = new ExcelJS.Workbook();
  await wb.xlsx.load(buf as unknown as ArrayBuffer);
  return wb;
};
const cabecalho = (ws: ExcelJS.Worksheet) =>
  (ws.getRow(1).values as ExcelJS.CellValue[]).slice(1).map((v) => String(v).trim());

describe("planilhas", () => {
  it("5º EF com passo 25: 20 colunas de nível de '0 a 25' a '475 a 500'", async () => {
    const ano = ano5ef();
    expect(niveisDaPlanilha(ano)).toHaveLength(20);
    const ws = (await ler(await gerarPlanilha(projeto, "lingua-portuguesa", ano))).getWorksheet("Níveis")!;
    const niveis = cabecalho(ws).slice(4, -4);
    expect(niveis).toHaveLength(20);
    expect(niveis[0]).toBe("0 a 25");
    expect(niveis[19]).toBe("475 a 500");
    expect(ws.getRow(2).getCell(1).value).toBe("5EF");
    expect(ws.getRow(2).getCell(4).value).toBe("a#b");
    expect(ws.views[0]).toMatchObject({ state: "frozen", ySplit: 1 });
    expect(ws.getRow(1).font?.bold).toBe(true);
    expect(ws.getRow(1).getCell(5).fill).toMatchObject({ fgColor: { argb: "FFFFFF00" } });
  });

  it("2º EF irregular: colunas '0 a 390', '390 a 446', …, '782 a 1000'", async () => {
    const revista = Revista.parse(
      JSON.parse(readFileSync(new URL("../../saida/lingua-portuguesa.json", import.meta.url), "utf8")),
    );
    const ano = anosDaRevista(revista).find((a) => a.ano === "2ef")!;
    const ws = (await ler(await gerarPlanilha(projeto, "lingua-portuguesa", ano))).getWorksheet("Níveis")!;
    const niveis = cabecalho(ws).slice(4, -4);
    expect(niveis[0]).toBe("0 a 390");
    expect(niveis[1]).toBe("390 a 446");
    expect(niveis.at(-1)).toBe("782 a 1000");
  });

  it("duas habilidades no mesmo nível viram 'a#b'; nível vazio vira '–' (LP) e '...' (MT)", async () => {
    const linhas: LinhaEscala[] = [
      { level: 0, content: "a" },
      { level: 0, content: "b" },
      { level: 0, content: "---" },
    ];
    expect(celulaDoNivel(linhas, "–")).toBe("a#b");
    expect(celulaDoNivel([{ level: 0, content: "---" }], "–")).toBe("–");
    const ano = ano5ef();
    ano.descritores[0]!.scale["padrao-1"] = [{ level: 0, fim: 25, content: "x" }, { level: 0, content: "y" }];
    const lp = (await ler(await gerarPlanilha(projeto, "lingua-portuguesa", ano))).getWorksheet("Níveis")!;
    expect(lp.getRow(2).getCell(5).value).toBe("x#y");
    expect(lp.getRow(2).getCell(6).value).toBe("–");
    const mt = (await ler(await gerarPlanilha(projeto, "matematica", ano))).getWorksheet("Níveis")!;
    expect(mt.getRow(2).getCell(6).value).toBe("...");
  });

  it("separarHabilidades divide códigos e habilidade correspondente", () => {
    expect(
      separarHabilidades(["EF15LP02, EF15LP04", "(EF15LP03) Localizar informações explícitas em textos."]),
    ).toEqual({
      relacionadas: "EF15LP02, EF15LP04",
      correspondente: "(EF15LP03) Localizar informações explícitas em textos.",
    });
  });

  it("nomePlanilha e planilhasDoCaderno", async () => {
    expect(nomePlanilha("São Paulo", "lingua-portuguesa", "5ef")).toBe("São Paulo - LP 5EF.xlsx");
    expect(nomePlanilha('A/B:"C"', "matematica", "3em")).toBe("ABC - MT 3EM.xlsx");
    const [arq] = planilhasDoCaderno(projeto, { id: "lingua-portuguesa", anos: [ano5ef()] });
    expect(arq!.caminho).toBe("São Paulo - LP 5EF.xlsx");
    const partes: Buffer[] = [];
    for await (const p of arq!.abrir() as AsyncIterable<Buffer>) partes.push(p);
    const wb = await ler(Buffer.concat(partes));
    expect(wb.getWorksheet("Níveis")).toBeDefined();
  });

  it("cabeçalhos iguais aos do modelo", async () => {
    const modelo = async (nome: string) =>
      cabecalho((await ler(readFileSync(new URL(`../../revista/modelo/${nome}`, import.meta.url)))).worksheets[0]!);
    for (const [nome, caderno] of [
      ["NÍVEIS - LP 5EF.xlsx", "lingua-portuguesa"],
      ["GO - MT_5EF.xlsx", "matematica"],
    ] as const) {
      const esperado = await modelo(nome);
      const gerado = cabecalho(
        (await ler(await gerarPlanilha(projeto, caderno, ano5ef()))).getWorksheet("Níveis")!,
      );
      expect(gerado.slice(0, 4)).toEqual(esperado.slice(0, 4));
      expect(gerado.slice(-4)).toEqual(esperado.slice(-4));
      expect(esperado.slice(4, -4).every((h) => /^\d+ a \d+$/.test(h))).toBe(true);
      expect(gerado.slice(4, -4).every((h) => /^\d+ a \d+$/.test(h))).toBe(true);
    }
  });

  it("aba Escala traz faixa, passo, cortes e cores", async () => {
    const cores = { ...CORES_PADRAO, "padrao-1": "#112233" };
    const ws = (await ler(await gerarPlanilha({ nome: "X", cores }, "lingua-portuguesa", ano5ef()))).getWorksheet("Escala")!;
    const linhas = (ws.getSheetValues() as ExcelJS.CellValue[][]).map((r) => (r ?? []).slice(1).map(String));
    expect(linhas).toContainEqual(["Etapa", "5EF"]);
    expect(linhas).toContainEqual(["Mínimo", "0"]);
    expect(linhas).toContainEqual(["Máximo", "500"]);
    expect(linhas).toContainEqual(["Intervalo mínimo", "25"]);
    expect(linhas).toContainEqual(["Padrão 01", "0", "150", "#112233"]);
    expect(linhas).toContainEqual(["Padrão 04", "250", "500", CORES_PADRAO["padrao-4"]]);
    expect(linhas).toContainEqual(["Padrão", "Início (≥)", "Fim (< / ≤ no 04)", "Cor"]);
  });
});
