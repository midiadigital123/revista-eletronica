import type { Perfil } from "./contrato/schemas.js";

declare module "express-session" {
  interface SessionData {
    usuario: { id: string; nome: string; perfil: Perfil };
  }
}
