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

  it("adiciona linha com início e fim do intervalo e salva o padrão inteiro", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    await user.click(await screen.findByRole("button", { name: "Adicionar linha ao Padrão 04" }));
    await waitFor(() =>
      expect(d01().scale["padrao-4"]).toEqual([
        { level: 375, fim: 500, content: "---" },
        { level: 325, content: "---" },
      ]),
    );
  });

  it("remove linha", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    await user.click(await screen.findByRole("button", { name: "Remover linha 2 do Padrão 01" }));
    await waitFor(() => expect(niveis("padrao-1")).toEqual([100]));
    expect(
      screen.queryByLabelText("Nível da linha 2 do Padrão 01 — início (maior ou igual a)"),
    ).not.toBeInTheDocument();
  });

  it("reordena as linhas por nível decrescente depois de salvar", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const nivel = await screen.findByLabelText(
      "Nível da linha 1 do Padrão 03 — início (maior ou igual a)",
    );
    await user.clear(nivel);
    await user.type(nivel, "260");
    await user.tab();

    await waitFor(() => expect(niveis("padrao-3")).toEqual([275, 260, 250]));
    await waitFor(() =>
      expect(
        screen.getByLabelText("Nível da linha 1 do Padrão 03 — início (maior ou igual a)"),
      ).toHaveValue(275),
    );
    expect(
      screen.getByLabelText("Nível da linha 2 do Padrão 03 — início (maior ou igual a)"),
    ).toHaveValue(260);
  });

  it("nível fora da escala: erro 400 no campo, nada salvo", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const nivel = await screen.findByLabelText(
      "Nível da linha 1 do Padrão 04 — início (maior ou igual a)",
    );
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

  it("salva o fim da linha; vazio é omitido", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const fim = await screen.findByLabelText("Nível da linha 1 do Padrão 03 — fim (menor que)");
    await user.type(fim, "320");
    await user.tab();
    await waitFor(() =>
      expect(d01().scale["padrao-3"][0]).toEqual({
        level: 300,
        fim: 320,
        content: expect.any(String),
      }),
    );
    await user.clear(fim);
    await user.tab();
    await waitFor(() => expect(d01().scale["padrao-3"][0]).not.toHaveProperty("fim"));
  });

  it("fim menor que o início: erro 400 na linha", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    await user.type(
      await screen.findByLabelText("Nível da linha 1 do Padrão 03 — fim (menor que)"),
      "200",
    );
    await user.tab();
    expect(await within(bloco("Padrão 03")).findByRole("alert")).toHaveTextContent(
      "O fim deve ser maior que o início",
    );
    expect(d01().scale["padrao-3"][0]).not.toHaveProperty("fim");
  });

  it("anexa o PDF do item, mostra o nome e remove", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const pdf = new File(["%PDF"], "item-d01.pdf", { type: "application/pdf" });
    await user.upload(await screen.findByLabelText("PDF do item da linha 1 do Padrão 03"), pdf);

    // Divergência do mock (como no PUT imagem): no jsdom o File chega ao handler sem o nome
    // ("blob"); a API real guarda o nome enviado. O teste usa o nome que o mock gravou.
    await waitFor(() => expect(d01().scale["padrao-3"][0]!.item).toMatchObject({ tamanho: 4 }));
    const { id, nome } = d01().scale["padrao-3"][0]!.item!;
    const link = await screen.findByRole("link", { name: nome });
    expect(link).toHaveAttribute("href", `/api/projetos/exemplo/itens/${id}`);
    expect(link).toHaveAttribute("target", "_blank");

    await user.click(screen.getByRole("button", { name: "Remover PDF da linha 1 do Padrão 03" }));
    await waitFor(() => expect(d01().scale["padrao-3"][0]).not.toHaveProperty("item"));
    expect(screen.queryByRole("link", { name: nome })).not.toBeInTheDocument();
  });

  it("recusa PDF acima de 5 MB no cliente", async () => {
    const user = userEvent.setup();
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01");
    const grande = new File([new Uint8Array(5 * 1024 * 1024 + 1)], "g.pdf", {
      type: "application/pdf",
    });
    await user.upload(await screen.findByLabelText("PDF do item da linha 1 do Padrão 03"), grande);
    expect(await within(bloco("Padrão 03")).findByRole("alert")).toHaveTextContent(
      "O PDF passa de 5 MB.",
    );
    expect(d01().scale["padrao-3"][0]).not.toHaveProperty("item");
  });
});

describe("modo leitura", () => {
  it("desabilita todos os campos e ações de edição", async () => {
    renderizarAno("/projetos/exemplo/lingua-portuguesa/ano/5ef/D01", "leitura");
    expect(await screen.findByLabelText("Código")).toBeDisabled();
    for (const rotulo of [
      "Padrão 02 — início (maior ou igual a)",
      "Padrão 04 — fim (menor ou igual a)",
      "Descrição",
      "Tópico",
      "Pré-requisito 1",
      "Nível da linha 1 do Padrão 04 — início (maior ou igual a)",
      "Conteúdo da linha 1 do Padrão 04",
      "PDF do item da linha 1 do Padrão 04",
    ])
      expect(screen.getByLabelText(rotulo)).toBeDisabled();
    for (const nome of [
      "Novo ano em Língua Portuguesa",
      "Excluir ano",
      "Novo descritor",
      "Duplicar D01",
      "Excluir D01",
      "Adicionar linha ao Padrão 04",
      "Remover linha 1 do Padrão 04",
      "Anexar PDF do item da linha 1 do Padrão 04",
      "Adicionar pré-requisito",
    ])
      expect(screen.getByRole("button", { name: nome })).toBeDisabled();
    expect(screen.getByLabelText("Buscar descritor")).toBeEnabled();
  });
});
