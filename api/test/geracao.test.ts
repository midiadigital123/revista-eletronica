import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import mongoose from "mongoose";
import supertest from "supertest";
import { describe, expect, it } from "vitest";
import { agenteLogado, usarApp } from "./helpers.js";

const ctx = usarApp();
const fixture: unknown = JSON.parse(
  readFileSync(new URL("./fixtures/revista.json", import.meta.url), "utf8"),
);
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==",
  "base64",
);

const binario = (res: supertest.Response, cb: (e: Error | null, b: Buffer) => void) => {
  const partes: Buffer[] = [];
  res.on("data", (p: Buffer) => partes.push(p));
  res.on("end", () => cb(null, Buffer.concat(partes)));
};

async function projetoComImagem() {
  const { agente } = await agenteLogado(ctx.app);
  await agente
    .post("/api/projetos")
    .send({
      slug: "fx",
      nome: "Fixture <&>",
      disciplinas: ["lingua-portuguesa", "matematica"],
      origem: {
        tipo: "importar",
        cadernos: { "lingua-portuguesa": fixture, matematica: fixture },
      },
    })
    .expect(201);
  await agente.post("/api/projetos/fx/bloqueio").expect(201);
  await agente
    .put("/api/projetos/fx/pagina/heroImagem/imagem")
    .attach("arquivo", PNG, { filename: "a.png", contentType: "image/png" })
    .expect(200);
  return agente;
}

const CAD = "/api/projetos/fx/preview/matematica";

const python = (...args: string[]) =>
  execFileSync("python3", ["-I", "-m", "zipfile", ...args]).toString();

describe("geração da revista", () => {
  it("preview: índice raiz com um link por caderno (HTML escapado)", async () => {
    const agente = await projetoComImagem();
    const r = await agente.get("/api/projetos/fx/preview").expect(302);
    expect(r.headers.location).toBe("/api/projetos/fx/preview/");
    const h = await agente.get("/api/projetos/fx/preview/").expect(200);
    expect(h.headers["content-type"]).toBe("text/html; charset=utf-8");
    expect(h.text).toContain("<title>Fixture &lt;&amp;&gt;</title>");
    expect([...h.text.matchAll(/<a href="([^"]+)">([^<]+)<\/a>/g)].map((m) => [m[1], m[2]])).toEqual([
      ["lingua-portuguesa/index.html", "Língua Portuguesa"],
      ["matematica/index.html", "Matemática"],
    ]);
  });

  it("preview: html do caderno com título e dados, estáticos e imagem", async () => {
    const agente = await projetoComImagem();
    const h = await agente.get(`${CAD}/index.html`).expect(200);
    expect(h.headers["content-type"]).toBe("text/html; charset=utf-8");
    expect(h.headers["cache-control"]).toBe("no-store");
    expect(h.text).toContain("ANÁLISE DOS RESULTADOS PARA INTERVENÇÃO PEDAGÓGICA");
    expect(h.text).toContain("arquivos/heroImagem.png");
    const dados = /<script type="application\/json" id="dados-revista">([\s\S]*?)<\/script>/.exec(
      h.text,
    );
    expect(JSON.parse(dados![1]!)).toHaveProperty("5ef.D01");

    const css = await agente.get(`${CAD}/styles.css`).expect(200);
    expect(css.headers["content-type"]).toBe("text/css; charset=utf-8");
    const js = await agente.get(`${CAD}/script.js`).expect(200);
    expect(js.headers["content-type"]).toBe("text/javascript; charset=utf-8");

    const img = await agente
      .get(`${CAD}/arquivos/heroImagem.png`)
      .buffer(true)
      .parse(binario)
      .expect(200);
    expect(img.headers["content-type"]).toBe("image/png");
    expect(Buffer.compare(img.body as Buffer, PNG)).toBe(0);
  });

  it("preview: cores do projeto (via PATCH) viram <style>; CSP permite style inline", async () => {
    const agente = await projetoComImagem();
    await agente
      .patch("/api/projetos/fx")
      .send({
        cores: {
          "padrao-1": "#14532d",
          "padrao-2": "#228b22",
          "padrao-3": "#90ee90",
          "padrao-4": "#0b6b3a",
        },
      })
      .expect(200);
    const h = await agente.get(`${CAD}/index.html`).expect(200);
    expect(h.text).toContain("--color-padrao-4-bg:rgba(11, 107, 58, 0.1);");
    const csp = String(h.headers["content-security-policy"]);
    expect(/style-src[^;]*'unsafe-inline'/.test(csp)).toBe(true);
  });

  it("preview: ícones servidos como SVG; imagem sumida do GridFS → 404 em JSON", async () => {
    const agente = await projetoComImagem();
    const svg = await agente.get(`${CAD}/assets/seta-proxima.svg`).expect(200);
    expect(svg.headers["content-type"]).toBe("image/svg+xml");

    await mongoose.connection.db!.collection("imagens.files").deleteMany({});
    const r = await agente.get(`${CAD}/arquivos/heroImagem.png`).expect(404);
    expect(r.headers["content-type"]).toMatch(/^application\/json/);
    expect(r.headers["cache-control"]).toBeUndefined();
  });

  it("404 para arquivo ou projeto inexistente; 401 sem sessão", async () => {
    const agente = await projetoComImagem();
    await agente.get("/api/projetos/fx/preview/nada.txt").expect(404);
    await agente.get("/api/projetos/fx/preview/arquivos/../../x").expect(404);
    await agente.get("/api/projetos/nao-existe/preview/").expect(404);
    await agente.get("/api/projetos/nao-existe/pacote.zip").expect(404);
    await supertest(ctx.app).get("/api/projetos/fx/preview/").expect(401);
    await supertest(ctx.app).get("/api/projetos/fx/pacote.zip").expect(401);
  });

  it("planilhas.zip tem um xlsx por caderno e etapa", async () => {
    const agente = await projetoComImagem();
    const z = await agente
      .get("/api/projetos/fx/planilhas.zip")
      .buffer(true)
      .parse(binario)
      .expect(200);
    expect(z.headers["content-type"]).toBe("application/zip");
    expect(z.headers["content-disposition"]).toBe('attachment; filename="fx-planilhas.zip"');
    const dir = mkdtempSync(join(tmpdir(), "planilhas-"));
    const arquivo = join(dir, "p.zip");
    writeFileSync(arquivo, z.body as Buffer);
    python("-t", arquivo);
    const lista = python("-l", arquivo);
    for (const c of ["lingua-portuguesa", "matematica"])
      for (const ano of ["5EF", "9EF", "3EM"])
        expect(lista).toMatch(new RegExp(`${c}/Fixture & - (LP|MT) ${ano}\\.xlsx`));
    expect(lista).not.toContain("index.html");
  });

  it("pacote.zip inclui <caderno>/planilhas/*.xlsx", async () => {
    const agente = await projetoComImagem();
    const z = await agente.get("/api/projetos/fx/pacote.zip").buffer(true).parse(binario).expect(200);
    const dir = mkdtempSync(join(tmpdir(), "pacote-xlsx-"));
    const arquivo = join(dir, "fx.zip");
    writeFileSync(arquivo, z.body as Buffer);
    const lista = python("-l", arquivo);
    expect(lista).toContain("lingua-portuguesa/planilhas/Fixture & - LP 5EF.xlsx");
    expect(lista).toContain("matematica/planilhas/Fixture & - MT 3EM.xlsx");
  });

  it("planilhas.zip exige login (401) e 404 para projeto inexistente", async () => {
    const agente = await projetoComImagem();
    await agente.get("/api/projetos/nao-existe/planilhas.zip").expect(404);
    await supertest(ctx.app).get("/api/projetos/fx/planilhas.zip").expect(401);
  });

  it("pacote.zip: índice raiz + pasta por caderno com index.html (dados), estáticos e a imagem", async () => {
    const agente = await projetoComImagem();
    const z = await agente
      .get("/api/projetos/fx/pacote.zip")
      .buffer(true)
      .parse(binario)
      .expect(200);
    expect(z.headers["content-type"]).toBe("application/zip");
    expect(z.headers["content-disposition"]).toBe('attachment; filename="fx.zip"');

    const dir = mkdtempSync(join(tmpdir(), "geracao-"));
    const arquivo = join(dir, "fx.zip");
    writeFileSync(arquivo, z.body as Buffer);
    python("-t", arquivo);
    const lista = python("-l", arquivo);
    const nomes = ["index.html", "styles.css", "script.js", "arquivos/heroImagem.png"];
    const cadernos = ["lingua-portuguesa", "matematica"];
    for (const c of cadernos)
      for (const nome of [...nomes, "assets/seta-anterior.svg", "assets/seta-proxima.svg"])
        expect(lista).toContain(`${c}/${nome}`);

    const saida = join(dir, "extraido");
    python("-e", arquivo, saida);
    expect(readFileSync(join(saida, "index.html"), "utf8")).toContain('href="matematica/index.html"');
    for (const c of cadernos) {
      const html = readFileSync(join(saida, c, "index.html"), "utf8");
      expect(html).toContain('id="dados-revista"');
      expect(html).toContain("ANÁLISE DOS RESULTADOS PARA INTERVENÇÃO PEDAGÓGICA");
      expect(html).not.toContain("localhost:3845");
      expect(Buffer.compare(readFileSync(join(saida, c, "arquivos/heroImagem.png")), PNG)).toBe(0);
    }
  });
});
