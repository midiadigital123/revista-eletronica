import type { Logger } from "pino";
import type { Config } from "./config.js";
import { UsuarioModel } from "./modules/usuarios/model.js";
import { gerarHash } from "./modules/usuarios/senha.js";

/**
 * Garante o primeiro admin a partir de ADMIN_EMAIL/ADMIN_SENHA.
 * Idempotente: upsert com $setOnInsert não toca em usuário que já existe (nem na senha).
 */
export async function garantirAdmin(config: Config, log: Logger): Promise<void> {
  const { ADMIN_EMAIL, ADMIN_SENHA } = config;
  if (!ADMIN_EMAIL || !ADMIN_SENHA) {
    log.info("ADMIN_EMAIL/ADMIN_SENHA ausentes: nenhum admin inicial criado");
    return;
  }
  const email = ADMIN_EMAIL.trim().toLowerCase();
  const agora = new Date();
  const resultado = await UsuarioModel.updateOne(
    { email },
    {
      $setOnInsert: {
        email,
        nome: "Administrador",
        senhaHash: await gerarHash(ADMIN_SENHA),
        perfil: "admin",
        ativo: true,
        criadoEm: agora,
        atualizadoEm: agora,
      },
    },
    // timestamps: false — senão o Mongoose põe atualizadoEm em $set e altera quem já existe.
    { upsert: true, timestamps: false },
  );
  if (resultado.upsertedCount > 0) log.info({ email }, "Admin inicial criado");
  else log.info({ email }, "Admin inicial já existe; nada alterado");
}
