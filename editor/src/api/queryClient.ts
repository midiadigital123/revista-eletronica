import { QueryClient } from "@tanstack/react-query";
import { ApiError } from "./client";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      // Erros 4xx são definitivos (não adianta repetir); 5xx/rede tenta 2x.
      retry: (falhas, erro) => !(erro instanceof ApiError && erro.status < 500) && falhas < 2,
      refetchOnWindowFocus: false,
    },
    mutations: { retry: false },
  },
});
