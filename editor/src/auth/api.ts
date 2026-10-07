import type { LoginEntrada, Usuario } from "../contrato/schemas";
import { api } from "../api/client";

export const authApi = {
  entrar: (credenciais: LoginEntrada) =>
    api<Usuario>("/auth/login", { method: "POST", body: credenciais }),
  sair: () => api<void>("/auth/logout", { method: "POST" }),
  eu: () => api<Usuario>("/auth/me"),
};
