import { Router } from "express";
import { ipKeyGenerator, rateLimit } from "express-rate-limit";
import { LoginEntrada } from "../../contrato/schemas.js";
import { AppError } from "../../errors.js";
import { handler } from "../../middlewares/handler.js";
import { requireAuth, usuarioDaSessao } from "../../middlewares/auth.js";
import { UsuarioModel, paraUsuario } from "../usuarios/model.js";
import { conferirSenha, gerarHash } from "../usuarios/senha.js";

export const authRouter = Router();

const credenciaisInvalidas = () => new AppError(401, "E-mail ou senha incorretos");

// Hash descartável: e-mail inexistente também paga o bcrypt, então o tempo de resposta não revela quais e-mails existem.
const hashFalso = gerarHash("senha-inexistente");

// ponytail: contador em memória por instância; usar store no Mongo/Redis se a API escalar horizontalmente.
const limiteLogin = rateLimit({
  windowMs: 15 * 60 * 1000,
  limit: 10,
  skipSuccessfulRequests: true,
  keyGenerator: (req) => `${ipKeyGenerator(req.ip ?? "")}:${String(req.body?.email ?? "").toLowerCase()}`,
  handler: (_req, _res, next) => next(new AppError(429, "Muitas tentativas de login. Tente de novo em 15 minutos")),
});

authRouter.post(
  "/login",
  limiteLogin,
  handler({ body: LoginEntrada }, async ({ body }, req, res) => {
    const usuario = await UsuarioModel.findOne({ email: body.email }).select("+senhaHash");
    const senhaOk = await conferirSenha(body.senha, usuario?.senhaHash ?? (await hashFalso));
    if (!usuario || !usuario.ativo || !senhaOk) throw credenciaisInvalidas();
    // Nova sessão a cada login (evita fixação de sessão).
    await new Promise<void>((ok, falha) => req.session.regenerate((e) => (e ? falha(e) : ok())));
    req.session.usuario = { id: usuario.id, nome: usuario.nome, perfil: usuario.perfil };
    res.json(paraUsuario(usuario));
  }),
);

authRouter.post("/logout", (req, res, next) => {
  req.session.destroy((erro) => {
    if (erro) return next(erro);
    res.clearCookie("revista.sid").status(204).end();
  });
});

authRouter.get(
  "/me",
  requireAuth,
  handler({}, async (_entrada, req, res) => {
    const usuario = await UsuarioModel.findById(usuarioDaSessao(req).id);
    if (!usuario?.ativo) throw new AppError(401, "Sessão expirada");
    res.json(paraUsuario(usuario));
  }),
);
