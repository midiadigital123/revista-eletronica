import { useQuery } from "@tanstack/react-query";
import { chaves } from "../api/chaves";
import { projetosApi } from "./api";

export const useProjetos = () =>
  useQuery({
    queryKey: chaves.projetos,
    queryFn: projetosApi.listar,
    // A lista mostra quem está editando cada projeto.
    refetchInterval: 30_000,
  });

export const useProjeto = (slug: string) =>
  useQuery({ queryKey: chaves.projeto(slug), queryFn: () => projetosApi.obter(slug) });
