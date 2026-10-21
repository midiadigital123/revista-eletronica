import type { z } from "zod";
import type { AtualizarUsuarioEntrada, CriarUsuarioEntrada, Usuario } from "../contrato/schemas";
import { api } from "../api/client";

export const usuariosApi = {
  listar: () => api<Usuario[]>("/usuarios"),
  criar: (dados: z.input<typeof CriarUsuarioEntrada>) =>
    api<Usuario>("/usuarios", { method: "POST", body: dados }),
  atualizar: (id: string, dados: z.input<typeof AtualizarUsuarioEntrada>) =>
    api<Usuario>(`/usuarios/${id}`, { method: "PATCH", body: dados }),
  excluir: (id: string) => api<void>(`/usuarios/${id}`, { method: "DELETE" }),
};
