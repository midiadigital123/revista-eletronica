/** Chaves de cache do TanStack Query, compartilhadas entre módulos. */
export const chaves = {
  eu: ["auth", "eu"] as const,
  usuarios: ["usuarios"] as const,
  camposPagina: ["pagina", "campos"] as const,
  projetos: ["projetos"] as const,
  projeto: (slug: string) => ["projetos", slug] as const,
};
