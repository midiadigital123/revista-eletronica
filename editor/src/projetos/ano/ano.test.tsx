import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import { chaves } from "../../api/chaves";
import { queryClient } from "../../api/queryClient";
import { rotuloAno, type Ano, type Projeto } from "../../contrato/schemas";
import { mockDb, resetarMockDb } from "../../mocks/db";
import { projetosApi } from "../api";
import { renderizarAno } from "./test/ProvedorEdicaoTeste";

const ANA = "000000000000000000000002";
const cadernoMock = () => mockDb.projetos.get("exemplo")!.cadernos[0]!;
const anoMock = (ano: Ano) => cadernoMock().anos.find((a) => a.ano === ano);
const codigos = (ano: Ano) => anoMock(ano)?.descritores.map((d) => d.codigo);

beforeEach(async () => {
  resetarMockDb({ logadoComo: ANA });
  await projetosApi.adquirirBloqueio("exemplo");
});

describe("anos", () => {
  it("cria um ano que falta e navega para a aba nova", async () => {
    cadernoMock().anos = cadernoMock().anos.filter((a) => a.ano !== "3em");
    const user = userEvent.setup();
    const { router } = renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef");

    await user.click(await screen.findByRole("button", { name: /^\+ Ano/ }));
    const dialogo = screen.getByRole("dialog", { name: /^Novo ano/ });
    expect(within(dialogo).queryByRole("button", { name: "5º EF" })).not.toBeInTheDocument();
    await user.click(within(dialogo).getByRole("button", { name: "3ª EM" }));

    expect(await screen.findByRole("heading", { name: "3ª EM" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/projetos/exemplo/lingua-portuguesa/ano/3em");
    expect(anoMock("3em")).toMatchObject({
      scaleRange: { min: 0, max: 500 },
      cortes: { "padrao-1": 125, "padrao-2": 250, "padrao-3": 375 },
      descritores: [],
    });
    // Sem atalhos restantes, o botão continua ativo: o formulário cria qualquer etapa.
    expect(screen.getByRole("button", { name: /^\+ Ano/ })).toBeEnabled();
  });

  it("cria qualquer etapa pelo formulário e a aba entra na ordem EF/EM", async () => {
    const user = userEvent.setup();
    const { router } = renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef");

    await user.click(await screen.findByRole("button", { name: /^\+ Ano/ }));
    const dialogo = screen.getByRole("dialog", { name: /^Novo ano/ });
    await user.type(within(dialogo).getByLabelText("Número"), "2");
    await user.selectOptions(within(dialogo).getByLabelText("Segmento"), "ef");
    expect(within(dialogo).getByText("Será criado: 2º EF")).toBeInTheDocument();
    await user.click(within(dialogo).getByRole("button", { name: "Criar" }));

    expect(await screen.findByRole("heading", { name: "2º EF" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/projetos/exemplo/lingua-portuguesa/ano/2ef");
    // As abas do ProjetoLayout seguem caderno.anos do cache, na mesma ordem.
    const abas = queryClient
      .getQueryData<Projeto>(chaves.projeto("exemplo"))!
      .cadernos[0]!.anos.map((a) => rotuloAno(a.ano));
    expect(abas).toEqual(["2º EF", "5º EF", "9º EF", "3ª EM"]);
    expect(
      cadernoMock()
        .anos.map((a) => a.ano)
        .slice(0, 2),
    ).toEqual(["2ef", "5ef"]);
  });

  it("formulário mostra erro inline para EM acima de 3 e para etapa existente", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef");

    await user.click(await screen.findByRole("button", { name: /^\+ Ano/ }));
    const dialogo = screen.getByRole("dialog", { name: /^Novo ano/ });
    const numero = within(dialogo).getByLabelText("Número");
    await user.type(numero, "4");
    await user.selectOptions(within(dialogo).getByLabelText("Segmento"), "em");
    await user.click(within(dialogo).getByRole("button", { name: "Criar" }));
    expect(within(dialogo).getByRole("alert")).toHaveTextContent(
      "No Ensino Médio use 1em, 2em ou 3em",
    );
    expect(numero).toHaveAccessibleDescription("No Ensino Médio use 1em, 2em ou 3em");

    await user.clear(numero);
    await user.type(numero, "5");
    await user.selectOptions(within(dialogo).getByLabelText("Segmento"), "ef");
    await user.click(within(dialogo).getByRole("button", { name: "Criar" }));
    expect(within(dialogo).getByRole("alert")).toHaveTextContent(
      "Esta etapa já existe neste caderno",
    );
    expect(anoMock("4em")).toBeUndefined();
    expect(screen.getByRole("dialog", { name: /^Novo ano/ })).toBeInTheDocument();
  });

  it("corte inválido mostra o erro sem enviar; corte válido salva", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef");
    const corte = await screen.findByLabelText("Corte 02 → 03");

    await user.clear(corte);
    await user.type(corte, "100");
    await user.tab();
    expect(await screen.findByText("Os cortes devem crescer entre 0 e 500")).toBeInTheDocument();
    expect(corte).toHaveAttribute("aria-invalid", "true");
    expect(anoMock("5ef")!.cortes["padrao-2"]).toBe(250);

    await user.clear(corte);
    await user.type(corte, "260");
    await user.tab();
    await waitFor(() => expect(anoMock("5ef")!.cortes["padrao-2"]).toBe(260));
    expect(screen.queryByText("Os cortes devem crescer entre 0 e 500")).not.toBeInTheDocument();
  });

  it("erro 400 da API lista os níveis que ficariam fora da faixa", async () => {
    anoMock("5ef")!.descritores[0]!.scale["padrao-4"] = [{ level: 450, content: "x" }];
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef");
    const max = await screen.findByLabelText("Máximo");
    await user.clear(max);
    await user.type(max, "400");
    await user.tab();
    expect(
      await screen.findByText(/Não foi possível salvar a faixa e os cortes/),
    ).toBeInTheDocument();
    expect(screen.getByText("D01, Padrão 04: Nível fora da escala (0–400)")).toBeInTheDocument();
    expect(anoMock("5ef")!.scaleRange.max).toBe(500);
  });

  it("exclui o ano e volta para a aba Página", async () => {
    const user = userEvent.setup();
    const { router } = renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/9ef");
    await user.click(await screen.findByRole("button", { name: "Excluir ano" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Excluir" }));

    expect(await screen.findByRole("heading", { name: "Página do projeto" })).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/projetos/exemplo");
    expect(anoMock("9ef")).toBeUndefined();
  });

  it("não deixa excluir o único ano", async () => {
    cadernoMock().anos = cadernoMock().anos.filter((a) => a.ano === "5ef");
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef");
    expect(await screen.findByRole("button", { name: "Excluir ano" })).toBeDisabled();
  });
});

describe("descritores", () => {
  it("busca por código, tópico ou descrição", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef");
    const lista = await screen.findByRole("navigation", { name: "Descritores do 5º EF" });
    expect(within(lista).getAllByRole("link")).toHaveLength(40);

    await user.type(screen.getByLabelText("Buscar descritor"), "variacao linguistica");
    const links = within(lista).getAllByRole("link");
    expect(links.length).toBeGreaterThan(0);
    expect(links.length).toBeLessThan(40);
  });

  it("cria com o próximo código livre e abre o descritor", async () => {
    const user = userEvent.setup();
    const { router } = renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/9ef");
    await user.click(await screen.findByRole("button", { name: "+ Descritor" }));

    expect(await screen.findByLabelText("Código")).toHaveValue("D03");
    expect(router.state.location.pathname).toBe("/projetos/exemplo/lingua-portuguesa/ano/9ef/D03");
    expect(codigos("9ef")).toEqual(["D01", "D02", "D03"]);
  });

  it("duplica copiando todos os campos e a escala", async () => {
    const user = userEvent.setup();
    const { router } = renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/9ef");
    await user.click(await screen.findByRole("button", { name: "Duplicar D01" }));
    const dialogo = screen.getByRole("dialog", { name: "Duplicar D01" });
    const campo = within(dialogo).getByLabelText("Novo código");
    expect(campo).toHaveValue("D03");
    await user.clear(campo);
    await user.type(campo, "D10");
    await user.click(within(dialogo).getByRole("button", { name: "Duplicar" }));

    await waitFor(() =>
      expect(router.state.location.pathname).toBe(
        "/projetos/exemplo/lingua-portuguesa/ano/9ef/D10",
      ),
    );
    const [d01, , d10] = anoMock("9ef")!.descritores;
    expect(d10).toEqual({ ...d01, codigo: "D10" });
  });

  it("duplicar com código existente mostra erro", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/9ef");
    await user.click(await screen.findByRole("button", { name: "Duplicar D01" }));
    const dialogo = screen.getByRole("dialog");
    const campo = within(dialogo).getByLabelText("Novo código");
    await user.clear(campo);
    await user.type(campo, "D02");
    await user.click(within(dialogo).getByRole("button", { name: "Duplicar" }));
    expect(within(dialogo).getByText("Esse código já existe neste ano")).toBeInTheDocument();
    expect(codigos("9ef")).toEqual(["D01", "D02"]);
  });

  it("renomeia o código e navega para a URL nova; 409 aparece no campo", async () => {
    const user = userEvent.setup();
    const { router } = renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/9ef/D02");
    const codigo = await screen.findByLabelText("Código");

    await user.clear(codigo);
    await user.type(codigo, "D01");
    await user.tab();
    expect(await screen.findByText("Esse código já existe neste ano")).toBeInTheDocument();
    expect(router.state.location.pathname).toBe("/projetos/exemplo/lingua-portuguesa/ano/9ef/D02");

    await user.clear(screen.getByLabelText("Código"));
    await user.type(screen.getByLabelText("Código"), "d07");
    await user.tab();
    await waitFor(() =>
      expect(router.state.location.pathname).toBe(
        "/projetos/exemplo/lingua-portuguesa/ano/9ef/D07",
      ),
    );
    expect(codigos("9ef")).toEqual(["D01", "D07"]);
    expect(await screen.findByLabelText("Código")).toHaveValue("D07");
  });

  it("exclui com confirmação e sai do descritor aberto", async () => {
    const user = userEvent.setup();
    const { router } = renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/9ef/D02");
    await user.click(await screen.findByRole("button", { name: "Excluir D02" }));
    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Excluir" }));

    await waitFor(() => expect(codigos("9ef")).toEqual(["D01"]));
    expect(router.state.location.pathname).toBe("/projetos/exemplo/lingua-portuguesa/ano/9ef");
    expect(screen.queryByRole("link", { name: /D02/ })).not.toBeInTheDocument();
  });
});
