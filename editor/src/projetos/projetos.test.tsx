import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { chaves } from "../api/chaves";
import { queryClient } from "../api/queryClient";
import { BLOQUEIO_HEARTBEAT_MS, BLOQUEIO_INATIVIDADE_MS, type Projeto } from "../contrato/schemas";
import { bloquearPorOutro, mockDb, resetarMockDb } from "../mocks/db";
import extracaoFixture from "../mocks/extracao.json";
import { servidorMock } from "../mocks/server";
import { renderizarRota } from "../test/renderizar";

const ANA = "000000000000000000000002";

beforeEach(() => resetarMockDb({ logadoComo: ANA }));
afterEach(() => {
  vi.useRealTimers();
  servidorMock.events.removeAllListeners();
});

/** Corpos enviados a POST /api/projetos durante o teste. */
function capturarCriacao() {
  const corpos: unknown[] = [];
  servidorMock.events.on("request:start", ({ request }) => {
    if (request.method === "POST" && new URL(request.url).pathname === "/api/projetos")
      void request
        .clone()
        .json()
        .then((c) => corpos.push(c));
  });
  return corpos;
}

const pdf = () => new File(["%PDF-1.7"], "revista.pdf", { type: "application/pdf" });

/** Abre o projeto e espera o modo edição (bloqueio adquirido). */
async function abrirEditando(caminho = "/projetos/exemplo") {
  const r = renderizarRota(caminho);
  expect(await screen.findByText("Editando")).toBeInTheDocument();
  return r;
}

describe("lista de projetos", () => {
  it("mostra o projeto e o cadeado de quem está editando", async () => {
    bloquearPorOutro("exemplo");
    renderizarRota("/projetos");
    expect(await screen.findByRole("heading", { name: "Exemplo" })).toBeInTheDocument();
    expect(screen.getByText("Em edição por Bia")).toBeInTheDocument();
    expect(screen.getByText(/atualizado/)).toBeInTheDocument();
  });

  it("cria projeto vazio com 2 disciplinas, slug sugerido e entra editando", async () => {
    const user = userEvent.setup();
    const corpos = capturarCriacao();
    const { router } = renderizarRota("/projetos");
    await user.click(await screen.findByRole("button", { name: "Novo projeto" }));
    await user.type(screen.getByLabelText("Nome"), "São Paulo 2026");
    expect(screen.getByLabelText("Identificador (slug)")).toHaveValue("sao-paulo-2026");
    await user.click(screen.getByLabelText("Matemática"));
    await user.click(screen.getByLabelText("Língua Portuguesa"));
    await user.click(screen.getByLabelText("3ª EM"));
    expect(screen.getByLabelText("1º EF")).not.toBeChecked();
    await user.click(screen.getByLabelText("2º EF"));
    await user.click(screen.getByRole("button", { name: "Criar projeto" }));

    expect(
      await screen.findByRole("heading", { name: "São Paulo 2026", level: 1 }),
    ).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/projetos/sao-paulo-2026");
    expect(await screen.findByText("Editando")).toBeInTheDocument();
    expect(corpos).toEqual([
      {
        nome: "São Paulo 2026",
        slug: "sao-paulo-2026",
        disciplinas: ["lingua-portuguesa", "matematica"],
        origem: { tipo: "vazio", anos: ["2ef", "5ef", "9ef"] },
      },
    ]);
    const criado = mockDb.projetos.get("sao-paulo-2026")!;
    expect(criado.cadernos.map((c) => [c.id, c.anos.map((a) => a.ano)])).toEqual([
      ["lingua-portuguesa", ["2ef", "5ef", "9ef"]],
      ["matematica", ["2ef", "5ef", "9ef"]],
    ]);
    expect(criado.bloqueio?.usuarioId).toBe(ANA);
    // Uma aba por caderno (leva ao primeiro ano); os anos e o "+ Ano" aparecem só no caderno aberto.
    const secoes = screen.getByRole("navigation", { name: "Seções do projeto" });
    expect(screen.queryByRole("navigation", { name: "Anos de Matemática" })).toBeNull();
    // Preview abre direto o caderno da aba (na Página, o primeiro), nunca o índice.
    const preview = () => screen.getByRole("link", { name: "Preview" });
    expect(preview()).toHaveAttribute(
      "href",
      "/api/projetos/sao-paulo-2026/preview/lingua-portuguesa/index.html",
    );
    await user.click(within(secoes).getByRole("link", { name: "Matemática" }));
    const mat = await screen.findByRole("navigation", { name: "Anos de Matemática" });
    expect(preview()).toHaveAttribute(
      "href",
      "/api/projetos/sao-paulo-2026/preview/matematica/index.html",
    );
    expect(within(secoes).getByRole("link", { name: "Matemática" })).toHaveAttribute(
      "aria-current",
      "page",
    );
    expect(within(mat).getByRole("link", { name: "2º EF" })).toHaveAttribute(
      "href",
      "/projetos/sao-paulo-2026/matematica/ano/2ef",
    );
    expect(within(mat).getByRole("button", { name: "+ Ano em Matemática" })).toBeEnabled();
  });

  it("sem disciplina marcada não envia", async () => {
    const user = userEvent.setup();
    const corpos = capturarCriacao();
    renderizarRota("/projetos");
    await user.click(await screen.findByRole("button", { name: "Novo projeto" }));
    await user.type(screen.getByLabelText("Nome"), "Sem disciplina");
    await user.click(screen.getByRole("button", { name: "Criar projeto" }));
    expect(await screen.findByText("Escolha ao menos uma disciplina")).toBeInTheDocument();
    expect(corpos).toEqual([]);
  });

  it("Alfabetização + Importar PDF: mostra os anos lidos e cria os dois cadernos", async () => {
    const user = userEvent.setup();
    const corpos = capturarCriacao();
    const { router } = renderizarRota("/projetos");
    await user.click(await screen.findByRole("button", { name: "Novo projeto" }));
    await user.type(screen.getByLabelText("Nome"), "Alfa");
    await user.click(screen.getByLabelText("Alfabetização"));
    await user.click(screen.getByRole("radio", { name: /Importar PDF/ }));
    await user.upload(screen.getByLabelText("PDF — Alfabetização"), pdf());

    for (const ano of ["2º EF", "5º EF"]) {
      const caixa = await screen.findByLabelText(ano);
      expect(caixa).toBeChecked();
      expect(caixa).toBeDisabled();
    }
    expect(screen.queryByLabelText("9º EF")).not.toBeInTheDocument();
    expect(screen.getByText(/D07 sem escala/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Criar projeto" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/projetos/alfa"));
    const corpo = corpos[0] as {
      disciplinas: string[];
      origem: { tipo: string; cadernos: object };
    };
    expect(corpo.disciplinas).toEqual(["alfabetizacao"]);
    expect(corpo.origem.tipo).toBe("importar");
    expect(Object.keys(corpo.origem.cadernos)).toEqual(["alfabetizacao-lp", "alfabetizacao-mat"]);
    expect(
      mockDb.projetos.get("alfa")!.cadernos.map((c) => [c.id, c.anos.map((a) => a.ano)]),
    ).toEqual([
      ["alfabetizacao-lp", ["2ef", "5ef"]],
      ["alfabetizacao-mat", ["2ef", "5ef"]],
    ]);
  });

  it("PDF sem Matemática no campo de Matemática mostra erro e não envia", async () => {
    const user = userEvent.setup();
    const { disciplinas, avisos } = extracaoFixture;
    servidorMock.use(
      http.post("/api/extracao", () =>
        HttpResponse.json({
          disciplinas: { "lingua-portuguesa": disciplinas["lingua-portuguesa"] },
          avisos,
        }),
      ),
    );
    const corpos = capturarCriacao();
    renderizarRota("/projetos");
    await user.click(await screen.findByRole("button", { name: "Novo projeto" }));
    await user.type(screen.getByLabelText("Nome"), "Só LP");
    await user.click(screen.getByLabelText("Matemática"));
    await user.click(screen.getByRole("radio", { name: /Importar PDF/ }));
    await user.upload(screen.getByLabelText("PDF — Matemática"), pdf());

    expect(await screen.findByText("Este PDF não traz Matemática")).toBeInTheDocument();
    expect(screen.queryByLabelText("2º EF")).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Criar projeto" }));
    expect(await screen.findByText("Escolha um PDF válido para Matemática.")).toBeInTheDocument();
    expect(corpos).toEqual([]);
  });
});

describe("casca do projeto", () => {
  it("renomeia o slug e navega para a URL nova", async () => {
    const user = userEvent.setup();
    const { router } = await abrirEditando();
    await user.click(screen.getByRole("button", { name: "Renomear" }));
    const slug = screen.getByLabelText("Identificador (slug)");
    await user.clear(slug);
    await user.type(slug, "exemplo-novo");
    await user.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/projetos/exemplo-novo"));
    expect(mockDb.projetos.has("exemplo-novo")).toBe(true);
    expect(await screen.findByText(/Salvo às/)).toBeInTheDocument();
    expect(screen.getByText("Editando")).toBeInTheDocument();
  });

  it("exclui com confirmação e volta para a lista", async () => {
    const user = userEvent.setup();
    const { router } = await abrirEditando();
    await user.click(screen.getByRole("button", { name: "Excluir" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Excluir" }));

    await waitFor(() => expect(router.state.location.pathname).toBe("/projetos"));
    expect(mockDb.projetos.has("exemplo")).toBe(false);
  });

  it("fica em modo leitura quando outra pessoa detém o bloqueio", async () => {
    bloquearPorOutro("exemplo");
    renderizarRota("/projetos/exemplo");
    expect(await screen.findByText(/Em edição por Bia desde \d\d:\d\d/)).toBeInTheDocument();
    expect(screen.getByText("Somente leitura")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Renomear" })).toBeDisabled();
    expect(await screen.findByLabelText("Título do topo")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Tentar editar" })).toBeEnabled();
  });

  it("heartbeat com 423 passa para modo leitura", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await abrirEditando();
    bloquearPorOutro("exemplo");
    await vi.advanceTimersByTimeAsync(BLOQUEIO_HEARTBEAT_MS);
    expect(await screen.findByText(/Em edição por Bia/)).toBeInTheDocument();
    expect(screen.getByText("Somente leitura")).toBeInTheDocument();
  });

  it("sai da edição por inatividade, libera o bloqueio e permite voltar", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    await abrirEditando();
    await vi.advanceTimersByTimeAsync(BLOQUEIO_INATIVIDADE_MS);
    expect(await screen.findByText(/saiu da edição por inatividade/)).toBeInTheDocument();
    expect(mockDb.projetos.get("exemplo")!.bloqueio).toBeNull();

    screen.getByRole("button", { name: "Voltar a editar" }).click();
    expect(await screen.findByText("Editando")).toBeInTheDocument();
  });

  it("escrita perdida por 423 aparece em não salvos com Copiar", async () => {
    const user = userEvent.setup();
    await abrirEditando();
    bloquearPorOutro("exemplo");
    const titulo = await screen.findByLabelText("Título do topo");
    await user.clear(titulo);
    await user.type(titulo, "Texto perdido");
    await user.tab();

    expect(await screen.findByText(/não foram salvas/)).toBeInTheDocument();
    expect(screen.getByText("Texto perdido")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Copiar" })).toBeInTheDocument();
    expect(screen.getByText("Somente leitura")).toBeInTheDocument();
  });
});

describe("falhas por caderno", () => {
  it("mesmo código e ano em cadernos diferentes: as duas falhas são repetidas", async () => {
    const projeto = mockDb.projetos.get("exemplo")!;
    projeto.cadernos.push({ id: "matematica", anos: structuredClone(projeto.cadernos[0]!.anos) });
    const topico = (i: number) =>
      mockDb.projetos.get("exemplo")!.cadernos[i]!.anos.find((a) => a.ano === "5ef")!
        .descritores[0]!.topic;
    let falhar = 2;
    servidorMock.use(
      http.patch("/api/projetos/:slug/cadernos/:caderno/anos/:ano/descritores/:codigo", () =>
        falhar-- > 0 ? HttpResponse.json({ erro: "Falhou" }, { status: 500 }) : undefined,
      ),
    );
    const user = userEvent.setup();
    const { router } = await abrirEditando("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    for (const [caderno, texto] of [
      ["lingua-portuguesa", "Tópico LP"],
      ["matematica", "Tópico MT"],
    ] as const) {
      if (caderno === "matematica")
        await router.navigate(`/projetos/exemplo/${caderno}/ano/5ef/D01`);
      // Espera o formulário do caderno atual (o anterior foi remontado).
      await waitFor(() => expect(screen.getByLabelText("Tópico")).not.toHaveValue("Tópico LP"));
      const campo = screen.getByLabelText("Tópico");
      await user.clear(campo);
      await user.type(campo, texto);
      await user.tab();
      await waitFor(() => expect(screen.getByText("Erro: Falhou")).toBeInTheDocument());
    }
    await waitFor(() => expect(falhar).toBe(0));

    await user.click(screen.getByRole("button", { name: "tentar de novo" }));
    await waitFor(() => expect(topico(0)).toBe("Tópico LP"));
    await waitFor(() => expect(topico(1)).toBe("Tópico MT"));
  });
});

describe("aba Página", () => {
  it("salva o campo no blur e aplica no cache sem refetch do projeto", async () => {
    const user = userEvent.setup();
    await abrirEditando();
    const titulo = await screen.findByLabelText("Título do topo");
    let gets = 0;
    const contar = ({ request }: { request: Request }) => {
      if (request.method === "GET" && new URL(request.url).pathname === "/api/projetos/exemplo")
        gets++;
    };
    servidorMock.events.on("request:start", contar);

    await user.clear(titulo);
    await user.type(titulo, "Novo título");
    await user.tab();

    expect(await screen.findByText(/Salvo às/)).toBeInTheDocument();
    servidorMock.events.removeListener("request:start", contar);
    expect(mockDb.projetos.get("exemplo")!.pagina.heroTitulo).toBe("Novo título");
    expect(queryClient.getQueryData<Projeto>(chaves.projeto("exemplo"))!.pagina.heroTitulo).toBe(
      "Novo título",
    );
    expect(gets).toBe(0);
  });

  it("falha ao salvar: o próximo blur reenvia o mesmo valor", async () => {
    const user = userEvent.setup();
    await abrirEditando();
    servidorMock.use(
      http.patch(
        "/api/projetos/:slug/pagina",
        () => HttpResponse.json({ erro: "Falhou" }, { status: 500 }),
        { once: true },
      ),
    );
    const titulo = await screen.findByLabelText("Título do topo");
    await user.clear(titulo);
    await user.type(titulo, "Depois da falha");
    await user.tab();
    expect(await screen.findByText("Erro: Falhou")).toBeInTheDocument();

    await user.click(titulo);
    await user.tab();
    await waitFor(() =>
      expect(mockDb.projetos.get("exemplo")!.pagina.heroTitulo).toBe("Depois da falha"),
    );
  });

  it("duas falhas e um sucesso: continua pendente até repetir", async () => {
    const user = userEvent.setup();
    await abrirEditando();
    let falhar = 2;
    servidorMock.use(
      http.patch("/api/projetos/:slug/pagina", () =>
        falhar-- > 0 ? HttpResponse.json({ erro: "Falhou" }, { status: 500 }) : undefined,
      ),
    );
    const titulo = await screen.findByLabelText("Título do topo");
    await user.type(titulo, " A");
    await user.tab();
    expect(await screen.findByText("Erro: Falhou")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "+ parágrafo" }));
    await user.type(screen.getByLabelText("Parágrafo 1"), "Novo");
    await user.tab();
    await waitFor(() => expect(falhar).toBe(0));

    // Sucesso do título não apaga a falha dos parágrafos.
    await user.click(titulo);
    await user.tab();
    await waitFor(() => expect(mockDb.projetos.get("exemplo")!.pagina.heroTitulo).toMatch(/ A$/));
    expect(screen.queryByText(/Salvo às/)).not.toBeInTheDocument();
    expect(screen.getByText("Erro: Falhou")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "tentar de novo" }));
    expect(await screen.findByText(/Salvo às/)).toBeInTheDocument();
    expect(mockDb.projetos.get("exemplo")!.pagina.introParagrafos).toEqual(["Novo"]);
    expect(screen.queryByRole("button", { name: "tentar de novo" })).not.toBeInTheDocument();
  });

  it("restaurar padrão envia null e remove o campo", async () => {
    const user = userEvent.setup();
    await abrirEditando();
    const titulo = await screen.findByLabelText("Título do topo");
    expect(titulo).not.toHaveValue("");
    await user.click(screen.getAllByRole("button", { name: "Restaurar padrão" })[0]!);

    await waitFor(() => expect(mockDb.projetos.get("exemplo")!.pagina.heroTitulo).toBeUndefined());
    expect(titulo).toHaveValue("");
  });

  it("parágrafos: adiciona, salva no blur e remove", async () => {
    const user = userEvent.setup();
    await abrirEditando();
    await user.click(await screen.findByRole("button", { name: "+ parágrafo" }));
    await user.type(screen.getByLabelText("Parágrafo 1"), "Primeiro");
    await user.tab();
    await waitFor(() =>
      expect(mockDb.projetos.get("exemplo")!.pagina.introParagrafos).toEqual(["Primeiro"]),
    );

    await user.click(screen.getByRole("button", { name: "Remover parágrafo 1" }));
    await waitFor(() =>
      expect(mockDb.projetos.get("exemplo")!.pagina.introParagrafos).toBeUndefined(),
    );
  });

  it("envia e remove a imagem", async () => {
    // Divergência do mock (mocks/handlers.ts, PUT imagem): no jsdom, request.formData()
    // devolve o File do undici e `arquivo instanceof File` (File do jsdom) é falso.
    const user = userEvent.setup();
    await abrirEditando();
    const entrada = await screen.findByLabelText("Imagem do topo");
    await user.upload(entrada, new File(["png"], "topo.png", { type: "image/png" }));

    const img = await screen.findByRole("img", { name: "Imagem do topo atual" });
    expect(img.getAttribute("src")).toContain("/api/projetos/exemplo/pagina/heroImagem/imagem?v=");
    expect(mockDb.projetos.get("exemplo")!.pagina.heroImagem).toEqual({
      nome: "heroImagem.png",
      mime: "image/png",
      tamanho: 3,
    });

    await user.click(screen.getByRole("button", { name: "Remover imagem (usar padrão)" }));
    await waitFor(() => expect(mockDb.projetos.get("exemplo")!.pagina.heroImagem).toBeUndefined());
  });

  it("recusa imagem acima de 5 MB no cliente", async () => {
    const user = userEvent.setup();
    await abrirEditando();
    const grande = new File([new Uint8Array(5 * 1024 * 1024 + 1)], "g.png", { type: "image/png" });
    await user.upload(await screen.findByLabelText("Imagem do topo"), grande);
    expect(await screen.findByText("A imagem passa de 5 MB.")).toBeInTheDocument();
    expect(mockDb.projetos.get("exemplo")!.pagina.heroImagem).toBeUndefined();
  });
});
