import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import type { Padrao } from "../../contrato/schemas";
import { mockDb, resetarMockDb } from "../../mocks/db";
import { projetosApi } from "../api";
import { renderizarAno } from "./test/ProvedorEdicaoTeste";

const ANA = "000000000000000000000002";
const d01 = () =>
  mockDb.projetos.get("exemplo")!.cadernos[0]!.anos.find((a) => a.ano === "5ef")!.descritores[0]!;
const niveis = (p: Padrao) => d01().scale[p].map((l) => l.level);
const bloco = (rotulo: string) => screen.getByRole("region", { name: rotulo });

beforeEach(async () => {
  resetarMockDb({ logadoComo: ANA });
  await projetosApi.adquirirBloqueio("exemplo");
});

describe("formulário do descritor", () => {
  it("salva campo de texto no blur", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const descricao = await screen.findByLabelText("Descrição");
    await user.clear(descricao);
    await user.type(descricao, "Nova descrição");
    await user.tab();
    await waitFor(() => expect(d01().description).toBe("Nova descrição"));

    const praticas = screen.getByLabelText("Práticas de linguagem");
    await user.clear(praticas);
    await user.type(praticas, "Oralidade");
    await user.tab();
    await waitFor(() => expect(d01().bncc.practices).toBe("Oralidade"));
    expect(d01().bncc.knowledge).toBe("Estratégia de leitura");
  });

  it("tópico oferece os tópicos do ano num datalist", async () => {
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const topico = await screen.findByLabelText("Tópico");
    const lista = document.getElementById(topico.getAttribute("list")!)!;
    expect(lista.querySelectorAll("option")).toHaveLength(6);
  });

  it("adiciona e remove pré-requisitos salvando a lista inteira", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const antes = [...d01().prerequisites];

    await user.click(await screen.findByRole("button", { name: "Adicionar pré-requisito" }));
    await user.type(screen.getByLabelText(`Pré-requisito ${antes.length + 1}`), "Novo item");
    await user.tab();
    await waitFor(() => expect(d01().prerequisites).toEqual([...antes, "Novo item"]));

    await user.click(screen.getByRole("button", { name: "Remover pré-requisito 1" }));
    await waitFor(() => expect(d01().prerequisites).toEqual([...antes.slice(1), "Novo item"]));
  });
});

describe("editor da escala", () => {
  it("mostra os padrões do 04 ao 01, intervalos, avisos e o placeholder 'sem item'", async () => {
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const titulos = (await screen.findAllByRole("heading", { level: 4 })).map((h) => h.textContent);
    expect(titulos).toEqual(["Padrão 04", "Padrão 03", "Padrão 02", "Padrão 01"]);
    expect(within(bloco("Padrão 04")).getByText("375 ≤ nível ≤ 500")).toBeInTheDocument();
    expect(within(bloco("Padrão 01")).getByText("0 ≤ nível < 125")).toBeInTheDocument();

    // D01: Padrão 04 tem uma linha no nível 325, que pelos cortes é do Padrão 03.
    expect(within(bloco("Padrão 04")).getByRole("status")).toHaveTextContent(
      "Nível 325 pertence ao Padrão 03",
    );
    expect(screen.getByLabelText("Conteúdo da linha 1 do Padrão 04")).toHaveValue("");
    expect(screen.getByLabelText("Conteúdo da linha 1 do Padrão 04")).toHaveAttribute(
      "placeholder",
      "sem item",
    );

    for (const p of ["Padrão 04", "Padrão 03", "Padrão 02"])
      expect(within(bloco(p)).getAllByRole("note")).toHaveLength(1);
    expect(within(bloco("Padrão 01")).queryByRole("note")).not.toBeInTheDocument();
    const linhasP3 = within(bloco("Padrão 03")).getAllByRole("listitem");
    expect(within(linhasP3.at(-1)!).getByRole("note")).toHaveTextContent("não aparece na revista");
  });

  it("adiciona linha no início do intervalo e salva o padrão inteiro", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    await user.click(await screen.findByRole("button", { name: "Adicionar linha ao Padrão 04" }));
    await waitFor(() =>
      expect(d01().scale["padrao-4"]).toEqual([
        { level: 375, content: "---" },
        { level: 325, content: "---" },
      ]),
    );
  });

  it("remove linha", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    await user.click(await screen.findByRole("button", { name: "Remover linha 2 do Padrão 01" }));
    await waitFor(() => expect(niveis("padrao-1")).toEqual([100]));
    expect(screen.queryByLabelText("Nível da linha 2 do Padrão 01")).not.toBeInTheDocument();
  });

  it("reordena as linhas por nível decrescente depois de salvar", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const nivel = await screen.findByLabelText("Nível da linha 1 do Padrão 03");
    await user.clear(nivel);
    await user.type(nivel, "260");
    await user.tab();

    await waitFor(() => expect(niveis("padrao-3")).toEqual([275, 260, 250]));
    await waitFor(() =>
      expect(screen.getByLabelText("Nível da linha 1 do Padrão 03")).toHaveValue(275),
    );
    expect(screen.getByLabelText("Nível da linha 2 do Padrão 03")).toHaveValue(260);
  });

  it("nível fora da escala: erro 400 no campo, nada salvo", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const nivel = await screen.findByLabelText("Nível da linha 1 do Padrão 04");
    await user.clear(nivel);
    await user.type(nivel, "600");
    await user.tab();

    expect(await within(bloco("Padrão 04")).findByRole("alert")).toHaveTextContent(
      "Nível fora da escala (0–500)",
    );
    expect(nivel).toHaveAttribute("aria-invalid", "true");
    expect(niveis("padrao-4")).toEqual([325]);
  });

  it("salva o conteúdo; vazio vira '---' na API", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const conteudo = await screen.findByLabelText("Conteúdo da linha 1 do Padrão 03");
    await user.clear(conteudo);
    await user.tab();
    await waitFor(() => expect(d01().scale["padrao-3"][0]).toEqual({ level: 300, content: "---" }));
  });
});

describe("modo leitura", () => {
  it("desabilita todos os campos e ações de edição", async () => {
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01", "leitura");
    expect(await screen.findByLabelText("Código")).toBeDisabled();
    for (const rotulo of [
      "Corte 01 → 02",
      "Máximo",
      "Descrição",
      "Tópico",
      "Pré-requisito 1",
      "Nível da linha 1 do Padrão 04",
      "Conteúdo da linha 1 do Padrão 04",
    ])
      expect(screen.getByLabelText(rotulo)).toBeDisabled();
    for (const nome of [
      "+ Ano em Língua Portuguesa",
      "Excluir ano",
      "+ Descritor",
      "Duplicar D01",
      "Excluir D01",
      "Adicionar linha ao Padrão 04",
      "Remover linha 1 do Padrão 04",
      "Adicionar pré-requisito",
    ])
      expect(screen.getByRole("button", { name: nome })).toBeDisabled();
    expect(screen.getByLabelText("Buscar descritor")).toBeEnabled();
  });
});
