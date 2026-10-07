import { ZipArchive } from "archiver";
import { Router, type NextFunction, type Response } from "express";
import { naoEncontrado } from "../../errors.js";
import { montarPacote } from "./service.js";

/**
 * Montado em /api/projetos/:slug (já atrás de requireAuth). DONO: A7.
 * Leitura livre (não exige bloqueio). Ver docs/contrato.md, "Geração da revista".
 */
export const geracaoRouter = Router({ mergeParams: true, strict: true });

const slugDe = (params: Record<string, unknown>) => String(params.slug);

/** Sem a barra final os caminhos relativos (styles.css, arquivos/…) quebrariam. */
geracaoRouter.get("/preview", (req, res) => {
  res.redirect(302, `/api/projetos/${encodeURIComponent(slugDe(req.params))}/preview/`);
});

// Helmet: a CSP padrão (script-src 'self') basta; script.js é externo e o bloco
// application/json não executa. Nenhuma CSP específica é necessária aqui.
async function servir(slug: string, caminho: string, res: Response, next: NextFunction) {
  const arquivo = (await montarPacote(slug)).find((a) => a.caminho === caminho);
  if (!arquivo) throw naoEncontrado("Arquivo");
  const conteudo = arquivo.abrir();
  res.set({ "Content-Type": arquivo.tipo, "Cache-Control": "no-store" });
  if (Buffer.isBuffer(conteudo)) {
    res.send(conteudo);
    return;
  }
  conteudo.on("error", (erro) => {
    if (res.headersSent) return res.destroy(erro);
    for (const h of ["Content-Type", "Cache-Control"]) res.removeHeader(h);
    next(erro);
  });
  res.on("close", () => conteudo.destroy());
  conteudo.pipe(res);
}

geracaoRouter.get("/preview/", (req, res, next) =>
  servir(slugDe(req.params), "index.html", res, next),
);

geracaoRouter.get("/preview/*arquivo", (req, res, next) => {
  const partes = (req.params as unknown as { arquivo: string[] }).arquivo;
  return servir(slugDe(req.params), partes.join("/"), res, next);
});

geracaoRouter.get("/pacote.zip", async (req, res, next) => {
  const slug = slugDe(req.params);
  const arquivos = await montarPacote(slug);
  const zip = new ZipArchive();
  zip.on("error", (erro) => {
    if (res.headersSent) res.destroy(erro);
    else {
      for (const h of ["Content-Type", "Content-Disposition"]) res.removeHeader(h);
      next(erro);
    }
  });
  res.on("close", () => zip.destroy());
  res.set({
    "Content-Type": "application/zip",
    "Content-Disposition": `attachment; filename="${slug}.zip"`,
  });
  zip.pipe(res);
  for (const a of arquivos) zip.append(a.abrir(), { name: a.caminho });
  await zip.finalize();
});
