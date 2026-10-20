import { PassThrough, type Readable } from "node:stream";
import ExcelJS from "exceljs";
import {
  CONTEUDO_VAZIO,
  CORES_PADRAO,
  PADROES,
  type Ano,
  type AnoProjeto,
  type Caderno,
  type CadernoProjeto,
  type Cores,
  type LinhaEscala,
} from "../../contrato/schemas.js";
import type { ArquivoPacote } from "../geracao/service.js";
import { bnccDoDescritor, COR_NIVEL, LAYOUTS, ROTULOS_PADRAO, SUFIXO_CADERNO } from "./layout.js";

type ProjetoPlanilha = { nome: string; cores: Cores | null };

const XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

/** Níveis distintos de todas as linhas do ano ∪ mínimo da faixa, crescentes; `fim` = próximo nível ou máximo. */
export function niveisDaPlanilha(ano: AnoProjeto): { level: number; fim: number }[] {
  const niveis = new Set<number>([ano.scaleRange.min]);
  for (const d of ano.descritores)
    for (const p of PADROES) for (const l of d.scale[p]) niveis.add(l.level);
  const ordenados = [...niveis].sort((a, b) => a - b);
  return ordenados.map((level, i) => ({ level, fim: ordenados[i + 1] ?? ano.scaleRange.max }));
}

/** Conteúdo das linhas de um nível sem os "---", unidos por "#"; nada → `vazio`. */
export function celulaDoNivel(linhas: LinhaEscala[], vazio: "–" | "..."): string {
  const textos = linhas.map((l) => l.content).filter((c) => c !== CONTEUDO_VAZIO);
  return textos.length ? textos.join("#") : vazio;
}

/** Itens entre parênteses no início são a habilidade correspondente; o resto, códigos relacionados. */
export function separarHabilidades(skills: string[]): {
  relacionadas: string;
  correspondente: string;
} {
  const correspondentes = skills.filter((s) => s.startsWith("("));
  return {
    relacionadas: skills.filter((s) => !s.startsWith("(")).join("\n"),
    correspondente: correspondentes.join("\n"),
  };
}

export function nomePlanilha(nomeProjeto: string, caderno: Caderno, ano: Ano): string {
  const nome = nomeProjeto.replace(/[/\\:*?"<>|]/g, "").trim();
  return `${nome} - ${SUFIXO_CADERNO[caderno]} ${ano.toUpperCase()}.xlsx`;
}

const argb = (hex: string) => `FF${hex.slice(1).toUpperCase()}`;

function abaNiveis(wb: ExcelJS.Workbook, caderno: Caderno, ano: AnoProjeto) {
  const layout = LAYOUTS[caderno];
  const niveis = niveisDaPlanilha(ano);
  const ws = wb.addWorksheet("Níveis", { views: [{ state: "frozen", ySplit: 1 }] });
  const cabecalhos = [
    ...layout.inicio,
    ...niveis.map((n) => `${n.level} a ${n.fim}`),
    ...layout.fim,
  ];
  ws.columns = cabecalhos.map((header, i) => ({
    header,
    width:
      i < 4
        ? layout.larguras.inicio[i]
        : i < 4 + niveis.length
          ? layout.larguras.nivel
          : layout.larguras.fim[i - 4 - niveis.length],
  }));
  const cabecalho = ws.getRow(1);
  cabecalho.font = { bold: true };
  niveis.forEach((_, i) => {
    cabecalho.getCell(5 + i).fill = {
      type: "pattern",
      pattern: "solid",
      fgColor: { argb: COR_NIVEL },
    };
  });
  for (const d of ano.descritores) {
    const { relacionadas, correspondente } = separarHabilidades(d.bncc.skills);
    const [praticas, conhecimento] = bnccDoDescritor(d.bncc);
    const linhas = PADROES.flatMap((p) => d.scale[p]);
    const row = ws.addRow([
      ano.ano.toUpperCase(),
      d.codigo,
      d.description,
      d.prerequisites.join("#"),
      ...niveis.map((n) =>
        celulaDoNivel(
          linhas.filter((l) => l.level === n.level),
          layout.vazio,
        ),
      ),
      praticas,
      conhecimento,
      relacionadas,
      correspondente,
    ]);
    row.alignment = { vertical: "top", wrapText: true };
    niveis.forEach((_, i) => {
      row.getCell(5 + i).fill = { type: "pattern", pattern: "solid", fgColor: { argb: COR_NIVEL } };
    });
  }
}

function abaEscala(wb: ExcelJS.Workbook, ano: AnoProjeto, cores: Cores) {
  const ws = wb.addWorksheet("Escala");
  const { min, max } = ano.scaleRange;
  const c = ano.cortes;
  ws.addRows([
    ["Etapa", ano.ano.toUpperCase()],
    ["Mínimo", min],
    ["Máximo", max],
    ["Intervalo mínimo", ano.passo ?? ""],
    [],
  ]);
  ws.addRow(["Padrão", "Início (≥)", "Fim (< / ≤ no 04)", "Cor"]).font = { bold: true };
  const limites = [min, c["padrao-1"], c["padrao-2"], c["padrao-3"], max];
  PADROES.forEach((p, i) => {
    const row = ws.addRow([ROTULOS_PADRAO[i], limites[i], limites[i + 1], cores[p]]);
    row.getCell(4).fill = { type: "pattern", pattern: "solid", fgColor: { argb: argb(cores[p]) } };
  });
  ws.columns = [{ width: 20 }, { width: 14 }, { width: 20 }, { width: 12 }];
  ws.getColumn(1).font = { bold: true };
}

export async function gerarPlanilha(
  projeto: ProjetoPlanilha,
  caderno: Caderno,
  ano: AnoProjeto,
): Promise<Buffer> {
  const wb = new ExcelJS.Workbook();
  abaNiveis(wb, caderno, ano);
  abaEscala(wb, ano, projeto.cores ?? CORES_PADRAO);
  return Buffer.from(await wb.xlsx.writeBuffer());
}

/** Uma planilha por ano; `abrir` devolve na hora um stream que recebe o arquivo quando fica pronto. */
export function planilhasDoCaderno(
  projeto: ProjetoPlanilha,
  caderno: CadernoProjeto,
): ArquivoPacote[] {
  return caderno.anos.map((ano) => ({
    caminho: nomePlanilha(projeto.nome, caderno.id, ano.ano),
    tipo: XLSX,
    abrir: (): Readable => {
      const saida = new PassThrough();
      gerarPlanilha(projeto, caderno.id, ano).then(
        (buf) => saida.end(buf),
        (erro: unknown) => saida.destroy(erro instanceof Error ? erro : new Error(String(erro))),
      );
      return saida;
    },
  }));
}
