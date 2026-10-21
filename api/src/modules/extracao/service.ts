import { execFile } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";
import { PDF_MAX_BYTES, ResultadoExtracao } from "../../contrato/schemas.js";
import { naoProcessavel } from "../../errors.js";

const executar = promisify(execFile);

/**
 * scripts/extrair_descritores.py: `EXTRATOR_PDF` se definido; senão
 * `<raiz do repositório>/scripts/...`, a partir de api/src/modules/extracao/ ou
 * api/dist/modules/extracao/ (no Docker, /app/scripts/; ver api/Dockerfile).
 */
const script = () =>
  process.env.EXTRATOR_PDF ??
  join(dirname(fileURLToPath(import.meta.url)), "../../../../scripts/extrair_descritores.py");

const ultimaLinha = (texto: string) => texto.trim().split("\n").at(-1)?.trim() ?? "";

/** Roda o extrator sobre o PDF e devolve as revistas por disciplina + avisos. */
export async function extrairPdf(conteudo: Buffer): Promise<ResultadoExtracao> {
  const pasta = await mkdtemp(join(tmpdir(), "extracao-"));
  try {
    const pdf = join(pasta, "revista.pdf");
    await writeFile(pdf, conteudo);
    let saida: { stdout: string; stderr: string };
    try {
      saida = await executar("python3", [script(), pdf, "--stdout"], {
        timeout: 60_000,
        maxBuffer: PDF_MAX_BYTES,
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      });
    } catch (erro) {
      const e = erro as { code?: unknown; killed?: boolean; stderr?: string };
      if (e.code === "ENOENT") throw erro; // python3 ausente: erro do servidor, não do PDF
      if (e.killed) throw naoProcessavel("A leitura do PDF demorou demais");
      throw naoProcessavel(`Não foi possível ler o PDF: ${ultimaLinha(e.stderr ?? "") || "erro no extrator"}`);
    }
    const avisos = saida.stderr
      .split("\n")
      .filter((l) => l.startsWith("aviso: "))
      .map((l) => l.slice("aviso: ".length).trim());
    let disciplinas: unknown;
    try {
      disciplinas = JSON.parse(saida.stdout);
    } catch {
      throw naoProcessavel("O extrator devolveu uma saída inválida");
    }
    const r = ResultadoExtracao.safeParse({ disciplinas, avisos });
    if (!r.success) {
      const i = r.error.issues[0];
      throw naoProcessavel(`Dados extraídos inválidos em ${i?.path.slice(1).join(".")}: ${i?.message}`);
    }
    if (!Object.keys(r.data.disciplinas).length)
      throw naoProcessavel("Nenhum descritor encontrado no PDF");
    return r.data;
  } finally {
    await rm(pasta, { recursive: true, force: true });
  }
}
