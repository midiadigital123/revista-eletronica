import { z } from "zod";

const Ambiente = z.object({
  NODE_ENV: z.enum(["development", "test", "production"]).default("development"),
  PORT: z.coerce.number().int().default(3000),
  MONGO_URL: z.string().min(1),
  SESSION_SECRET: z
    .string()
    .min(32, { error: "SESSION_SECRET precisa de 32+ caracteres" })
    .refine((v) => !v.startsWith("troque"), { error: "SESSION_SECRET ainda é o valor do .env.example" }),
  ADMIN_EMAIL: z.email().optional(),
  ADMIN_SENHA: z
    .string()
    .min(8)
    .refine((v) => !v.startsWith("troque"), { error: "ADMIN_SENHA ainda é o valor do .env.example" })
    .optional(),
  LOG_LEVEL: z.enum(["fatal", "error", "warn", "info", "debug", "trace", "silent"]).default("info"),
});

export type Config = z.infer<typeof Ambiente>;

export function lerConfig(ambiente: NodeJS.ProcessEnv = process.env): Config {
  const resultado = Ambiente.safeParse(ambiente);
  if (!resultado.success) {
    const problemas = resultado.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`);
    throw new Error(`Configuração inválida:\n${problemas.join("\n")}`);
  }
  return resultado.data;
}
