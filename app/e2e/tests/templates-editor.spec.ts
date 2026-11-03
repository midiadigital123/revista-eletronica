// Editor de template por seção (U9b) na tela B: o id da seção não é campo, uma seção por vez (o índice
// troca), "{ } Variável" insere no campo focado, adicionar/remover passo, Salvar -> impacto -> versão nova.
// Usa um template próprio ("E2E editor por seção", F2 de LP), criado pelo admin na 1ª execução,
// para não mexer no "Padrão". Cada execução cria a versão seguinte dele.
import { expect, test } from "@playwright/test";
import { entrar, liberarBloqueio } from "./helpers";

const NOME = "E2E editor por seção";
const TEXTO = "## abertura\nAbertura\n\nOlá.\n\n## passo1\nPasso um\n\nPara ";

test("template: editar o Passo 1, inserir variável e criar a versão nova", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));

  await entrar(page, `/admin/nucleo/template/?q=${encodeURIComponent(NOME)}`);
  await expect(page.locator("#changelist")).toBeVisible(); // count() não espera a lista carregar
  let link = page.locator("#result_list tbody th a", { hasText: NOME });
  if ((await link.count()) === 0) {
    await page.goto("/admin/nucleo/template/add/");
    await page.selectOption("#id_ano", { label: "2026" });
    const lp = page.locator("#id_componente option", { hasText: "LP" }).first();
    await page.selectOption("#id_componente", (await lp.getAttribute("value"))!);
    await page.selectOption("#id_fasciculo", "F2");
    await page.fill("#id_nome", NOME);
    await page.fill("#id_texto", TEXTO + "todos.\n");
    await page.click("input[name=_save]");
    await expect(page.locator(".messagelist")).toBeVisible();
    await page.goto(`/admin/nucleo/template/?q=${encodeURIComponent(NOME)}`);
    link = page.locator("#result_list tbody th a", { hasText: NOME });
  }
  const pk = (await link.first().getAttribute("href"))!.match(/template\/(\d+)\//)![1];
  await page.goto(`/ui/templates/editar/${pk}/`);

  // Uma seção por vez: abre a Abertura; clicar em "Passo 1" no índice troca a seção e a prévia.
  const indice = page.locator("#tpl-indice");
  const passo1 = page.locator("#secao-passo1");
  await expect(page.locator("#secao-abertura")).toBeVisible();
  await expect(passo1).toBeHidden();
  await indice.getByRole("link", { name: /Passo 1/ }).click();
  await expect(passo1).toBeVisible();
  await expect(page.locator("#secao-abertura")).toBeHidden();
  await expect(indice.locator('a[aria-current="true"]')).toHaveAttribute("href", "#secao-passo1");
  await expect(page.locator("#previa [data-previa]:visible")).toHaveCount(1);
  await expect(page.locator('#previa [data-previa="passo1"]')).toBeVisible();

  // O id é estrutura: chip com o rótulo, nenhum campo com "## ".
  await expect(passo1.locator(".tpl-chip")).toHaveText("Passo 1");
  const valores = await page.locator("textarea, input:not([type=hidden])").evaluateAll((els) => els.map((e) => (e as HTMLInputElement).value));
  expect(valores.filter((v) => v.includes("## "))).toEqual([]);
  await expect(page.locator("#previa")).not.toContainText("## ");

  const titulo = `Passo um ${Date.now()}`;
  await passo1.locator("[data-campo=titulo]").fill(titulo);
  await expect(page.locator("[data-estado]")).toHaveText("Alterações não salvas.");

  const corpo = passo1.locator("[data-campo=corpo]");
  await corpo.fill("Para ");
  await passo1.locator("[data-variavel]").selectOption("nome_parceiro");
  await passo1.getByRole("button", { name: "{ } Variável" }).click();
  await expect(corpo).toHaveValue("Para {{nome_parceiro}}");
  await expect(page.locator("#previa h3:visible")).toHaveText(titulo); // a prévia segue só com a ativa
  await expect(page.locator("#previa .variavel-vazia")).toContainText(["{{nome_parceiro}}"]);
  await expect(page.locator("#previa")).toContainText("Texto válido para o fascículo.");

  // Adicionar passo numera em sequência; o índice acompanha; remover desfaz.
  await page.getByRole("button", { name: "+ Adicionar passo" }).click();
  const passo2 = page.locator("#secao-passo2");
  await expect(passo2.locator(".tpl-chip")).toHaveText("Passo 2");
  await expect(passo2.locator("[data-campo=titulo]")).toBeFocused(); // a seção nova vira a ativa
  await expect(passo1).toBeHidden();
  await expect(page.locator("#tpl-indice")).toContainText("Passo 2");
  await expect(page.locator('#tpl-indice a[href="#secao-passo2"]')).toContainText("erro"); // vazio: inválido
  await expect(passo2.locator("[data-campo=titulo]")).toHaveAttribute("aria-invalid", "true");
  await passo2.getByRole("button", { name: "Remover seção" }).click();
  await expect(passo2).toHaveCount(0);
  await expect(passo1).toBeVisible(); // remover ativa a vizinha
  await expect(page.locator('#tpl-indice a[href="#secao-passo2"]')).toHaveCount(0);

  await page.getByRole("button", { name: "Salvar", exact: true }).click();
  const cab = page.getByRole("heading", { name: /Confira o impacto antes de criar a versão \d+/ });
  await expect(cab).toBeVisible();
  const nova = (await cab.textContent())!.match(/versão (\d+)/)![1];
  await page.getByRole("button", { name: `Confirmar e criar versão ${nova}` }).click();

  await expect(page.getByText(`Versão ${nova} criada.`)).toBeVisible();
  await expect(page.locator("#secao-passo1 [data-campo=titulo]")).toHaveValue(titulo); // hidden, mas foi junto no Salvar
  await expect(page.locator("#secao-passo1 [data-campo=corpo]")).toHaveValue("Para {{nome_parceiro}}");
  expect(erros).toEqual([]);

  await liberarBloqueio(page);
});
