import { useQuery } from "@tanstack/react-query";
import { chaves } from "../api/chaves";
import { authApi } from "./api";

/** Usuário da sessão (GET /auth/me). Erro 401 = sem sessão. */
export const useUsuario = () =>
  useQuery({ queryKey: chaves.eu, queryFn: authApi.eu, retry: false, staleTime: 60_000 });
