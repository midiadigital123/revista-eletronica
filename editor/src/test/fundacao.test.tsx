import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ApiError } from "../api/client";
import { authApi } from "../auth/api";
import { bloquearPorOutro, mockDb, resetarMockDb, SENHA_MOCK } from "../mocks/db";
import { projetosApi } from "../projetos/api";
import { renderizarRota } from "./renderizar";

describe("fundação do editor", () => {
  it("login e listagem de projetos pelos mocks", async () => {
    await authApi.entrar({ email: "ana@exemplo.org", senha: SENHA_MOCK });
    const projetos = await projetosApi.listar();
    expect(projetos.map((p) => p.slug)).toEqual(["exemplo"]);
  });

  it("escrita sem bloqueio responde 423 com quem está editando", async () => {
    resetarMockDb({ logadoComo: "000000000000000000000002" });
    bloquearPorOutro("exemplo");
    const erro = await projetosApi.atualizar("exemplo", { nome: "X" }).catch((e: unknown) => e);
    expect(erro).toBeInstanceOf(ApiError);
    expect((erro as ApiError).status).toBe(423);
    expect((erro as ApiError).bloqueio?.nome).toBe("Bia");
  });

  it("com bloqueio, edita a escala e devolve linhas ordenadas", async () => {
    resetarMockDb({ logadoComo: "000000000000000000000002" });
    await projetosApi.adquirirBloqueio("exemplo");
    const linhas = await projetosApi.salvarEscala("exemplo", "5ef", "D01", "padrao-3", [
      { level: 250, content: "" },
      { level: 300, content: "x" },
    ]);
    expect(linhas).toEqual([
      { level: 300, content: "x" },
      { level: 250, content: "---" },
    ]);
    expect(mockDb.projetos.get("exemplo")!.anos[0]!.descritores[0]!.scale["padrao-3"]).toEqual(linhas);
  });

  it("roteador: sem sessão vai para /login; logado fica em /projetos", async () => {
    resetarMockDb({ logadoComo: null });
    const anonimo = renderizarRota("/projetos");
    await waitFor(() => expect(anonimo.router.state.location.pathname).toBe("/login"));
    anonimo.unmount();

    resetarMockDb({ logadoComo: "000000000000000000000001" });
    const logado = renderizarRota("/projetos");
    expect(await screen.findByRole("navigation")).toBeInTheDocument();
    expect(logado.router.state.location.pathname).toBe("/projetos");
  });
});
