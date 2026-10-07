import { Router, type RequestHandler } from "express";
import multer from "multer";
import { buscarCampo } from "../../contrato/campos-pagina.js";
import { IMAGEM_MAX_BYTES, IMAGEM_MIMES, ParamsImagem } from "../../contrato/schemas.js";
import { naoEncontrado, requisicaoInvalida } from "../../errors.js";
import { exigirBloqueio } from "../../middlewares/exigirBloqueio.js";
import { handler } from "../../middlewares/handler.js";
import type { ImagemArmazenada } from "../projetos/model.js";
import {
  definirCampoPagina,
  obterProjeto,
  paraPagina,
  removerCampoPagina,
} from "../projetos/repository.js";
import { abrirLeitura, ehImagem, removerImagens, salvarImagem } from "./service.js";

/**
 * Montado em /api/projetos/:slug/pagina/:chave/imagem. DONO: A5b.
 * Rotas (docs/contrato.md): GET (stream), PUT 🔒 (multipart "arquivo"), DELETE 🔒.
 */
export const imagensRouter = Router({ mergeParams: true });

type Mime = ImagemArmazenada["mime"];

const ehMimeAceito = (mime: string): mime is Mime =>
  (IMAGEM_MIMES as readonly string[]).includes(mime);

/** Tipo real pelos bytes mágicos (o mime declarado pelo navegador não é confiável). */
function mimeDoConteudo(b: Buffer): Mime | null {
  if (b.subarray(0, 4).equals(Buffer.from([0x89, 0x50, 0x4e, 0x47]))) return "image/png";
  if (b.subarray(0, 3).equals(Buffer.from([0xff, 0xd8, 0xff]))) return "image/jpeg";
  if (b.toString("latin1", 0, 4) === "RIFF" && b.toString("latin1", 8, 12) === "WEBP")
    return "image/webp";
  return null;
}

/** 404 antes de ler o corpo se a chave não é um campo de imagem. */
const exigirCampoImagem: RequestHandler = (req, _res, next) => {
  const { chave } = ParamsImagem.parse(req.params);
  next(buscarCampo(chave)?.tipo === "imagem" ? undefined : naoEncontrado("Campo de imagem"));
};

const receberArquivo = multer({
  storage: multer.memoryStorage(),
  limits: { fileSize: IMAGEM_MAX_BYTES, files: 1 },
}).single("arquivo");

imagensRouter.get(
  "/",
  handler({ params: ParamsImagem }, async ({ params }, _req, res) => {
    const imagem = (await obterProjeto(params.slug)).pagina[params.chave];
    if (!ehImagem(imagem)) throw naoEncontrado("Imagem");
    const leitura = abrirLeitura(imagem.arquivoId);
    res.type(imagem.mime).set("Cache-Control", "no-cache");
    // Erro antes do primeiro byte vira resposta JSON; depois disso só resta cortar a conexão.
    await new Promise<void>((resolve, reject) => {
      leitura.on("error", (erro) => {
        if (res.headersSent) return res.destroy(erro);
        for (const h of ["Content-Type", "Cache-Control"]) res.removeHeader(h);
        reject(erro);
      });
      res.on("close", () => {
        leitura.destroy();
        resolve();
      });
      leitura.pipe(res);
    });
  }),
);

// Bloqueio conferido depois do upload: um envio lento não pode vencer o TTL entre a checagem e a gravação.
imagensRouter.put(
  "/",
  exigirCampoImagem,
  receberArquivo,
  exigirBloqueio,
  handler({ params: ParamsImagem }, async ({ params }, req, res) => {
    const arquivo = req.file;
    if (!arquivo) throw requisicaoInvalida("Envie a imagem no campo arquivo", { campo: "arquivo" });
    if (!ehMimeAceito(arquivo.mimetype))
      throw requisicaoInvalida("Use PNG, JPEG ou WebP", { campo: "arquivo" });
    if (mimeDoConteudo(arquivo.buffer) !== arquivo.mimetype)
      throw requisicaoInvalida("O conteúdo do arquivo não é uma imagem do tipo informado", {
        campo: "arquivo",
      });

    const projeto = await obterProjeto(params.slug);
    const anterior = projeto.pagina[params.chave];
    const nova = await salvarImagem({
      chave: params.chave,
      mime: arquivo.mimetype,
      conteudo: arquivo.buffer,
    });
    definirCampoPagina(projeto, params.chave, nova);
    try {
      await projeto.save();
    } catch (erro) {
      await removerImagens([nova.arquivoId]);
      throw erro;
    }
    if (ehImagem(anterior)) await removerImagens([anterior.arquivoId]);
    res.json(paraPagina(projeto));
  }),
);

imagensRouter.delete(
  "/",
  exigirBloqueio,
  handler({ params: ParamsImagem }, async ({ params }, _req, res) => {
    const projeto = await obterProjeto(params.slug);
    const anterior = projeto.pagina[params.chave];
    if (ehImagem(anterior)) {
      removerCampoPagina(projeto, params.chave);
      await projeto.save();
      await removerImagens([anterior.arquivoId]);
    }
    res.json(paraPagina(projeto));
  }),
);
