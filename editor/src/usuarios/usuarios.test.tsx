import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { mockDb, resetarMockDb, SENHA_MOCK } from "../mocks/db";
import { renderizarRota } from "../test/renderizar";

const ADMIN = "000000000000000000000001";
const EDITOR = "000000000000000000000002";

describe("login e rota protegida", () => {
  it("sem sessão redireciona para /login", async () => {
    resetarMockDb({ logadoComo: null });
    const { router } = renderizarRota("/projetos");
    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/login");
  });

  it("senha errada mostra alerta; certa volta para a origem", async () => {
    resetarMockDb({ logadoComo: null });
    const u = userEvent.setup();
    const { router } = renderizarRota("/usuarios");
    await u.type(await screen.findByLabelText("E-mail"), "admin@exemplo.org");
    await u.type(screen.getByLabelText("Senha"), "errada123");
    await u.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("E-mail ou senha incorretos");

    await u.clear(screen.getByLabelText("Senha"));
    await u.type(screen.getByLabelText("Senha"), SENHA_MOCK);
    await u.click(screen.getByRole("button", { name: "Entrar" }));
    expect(await screen.findByRole("heading", { name: "Usuários" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/usuarios");
  });

  it("já logado, /login vai para /projetos; sair volta ao login", async () => {
    resetarMockDb({ logadoComo: EDITOR });
    const u = userEvent.setup();
    const { router } = renderizarRota("/login");
    expect(await screen.findByRole("heading", { name: "Projetos" })).toBeInTheDocument();
    await u.click(screen.getByRole("button", { name: "Sair" }));
    await waitFor(() => expect(router.state.location.pathname).toBe("/login"));
    expect(mockDb.sessaoUsuarioId).toBeNull();
  });
});

describe("navegação por perfil", () => {
  it("editor não vê Usuários e recebe aviso na URL direta", async () => {
    resetarMockDb({ logadoComo: EDITOR });
    renderizarRota("/usuarios");
    expect(await screen.findByText(/Acesso restrito/)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Usuários" })).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Projetos" })).toBeInTheDocument();
  });
});

describe("CRUD de usuários (admin)", () => {
  it("cria, edita e exclui", async () => {
    resetarMockDb({ logadoComo: ADMIN });
    const u = userEvent.setup();
    renderizarRota("/usuarios");
    await screen.findByRole("table");

    await u.click(screen.getByRole("button", { name: "Novo usuário" }));
    const dlg = await screen.findByRole("dialog");
    await u.type(within(dlg).getByLabelText("E-mail"), "carla@exemplo.org");
    await u.type(within(dlg).getByLabelText("Nome"), "Carla");
    await u.type(within(dlg).getByLabelText("Senha"), "senha-nova-1");
    await u.click(within(dlg).getByRole("button", { name: "Criar" }));
    expect(await screen.findByRole("rowheader", { name: "Carla" })).toBeInTheDocument();

    await u.click(screen.getByRole("button", { name: "Editar Carla" }));
    const ed = await screen.findByRole("dialog");
    await u.clear(within(ed).getByLabelText("Nome"));
    await u.type(within(ed).getByLabelText("Nome"), "Carla Dias");
    await u.click(within(ed).getByLabelText("Ativo"));
    await u.click(within(ed).getByRole("button", { name: "Salvar" }));
    expect(await screen.findByRole("rowheader", { name: "Carla Dias" })).toBeInTheDocument();
    expect(mockDb.usuarios.find((x) => x.nome === "Carla Dias")?.ativo).toBe(false);

    await u.click(screen.getByRole("button", { name: "Excluir Carla Dias" }));
    await u.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Excluir" }),
    );
    await waitFor(() =>
      expect(screen.queryByRole("rowheader", { name: "Carla Dias" })).not.toBeInTheDocument(),
    );
  });

  it("e-mail duplicado (409) aparece no campo; própria conta (400) vira aviso", async () => {
    resetarMockDb({ logadoComo: ADMIN });
    const u = userEvent.setup();
    renderizarRota("/usuarios");
    await screen.findByRole("table");

    await u.click(screen.getByRole("button", { name: "Novo usuário" }));
    const dlg = await screen.findByRole("dialog");
    await u.type(within(dlg).getByLabelText("E-mail"), "ana@exemplo.org");
    await u.type(within(dlg).getByLabelText("Nome"), "Outra Ana");
    await u.type(within(dlg).getByLabelText("Senha"), "senha-nova-1");
    await u.click(within(dlg).getByRole("button", { name: "Criar" }));
    expect(await within(dlg).findByText("E-mail já cadastrado")).toHaveAttribute("role", "alert");
    await u.click(within(dlg).getByRole("button", { name: "Cancelar" }));

    await u.click(screen.getByRole("button", { name: "Excluir Admin" }));
    await u.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Excluir" }),
    );
    expect(await screen.findByText("Você não pode excluir a própria conta")).toBeInTheDocument();
  });
});
