// Editor de template por seção (U9b) na tela B: o id da seção não é campo, uma seção por vez (o índice
// troca), "{ } Variável" insere no campo focado, Salvar -> impacto -> versão nova. O F2 tem 9 seções fixas:
// sem "+ Adicionar passo" nem "Remover seção" (test_ui_templates.py::test_f2_nao_tem_secao_repetivel).
// Cada execução cria o seu template ("E2E editor <sufixo>", F2 de LP de 2026) e, no fim, o exclui pelo
// "Excluir template…" do editor (E4, D-207). O "Padrão" da demonstração só é aberto na página de excluir,
// que mostra o impedimento sem apagar.
import { expect, test } from "@playwright/test";
import { entrar, liberarBloqueio } from "./helpers";
import { criarTemplate, excluirTemplate, TEXTO_F2 } from "./templates";

test("template: editar o passo do descritor, inserir variável, criar a versão nova e excluir o template", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const nome = `E2E editor ${Date.now().toString(36).toUpperCase()}`;

  await entrar(page);
  const pk = await criarTemplate(page, nome, "F2", TEXTO_F2);
  await page.goto(`/ui/templates/editar/${pk}/`);

  // Uma seção por vez: abre a Abertura; clicar em "Passo: descritor" no índice troca a seção e a prévia.
  const indice = page.locator("#tpl-indice");
  const descritor = page.locator("#secao-passo-descritor");
  await expect(page.locator("#secao-abertura")).toBeVisible();
  await expect(descritor).toBeHidden();
  await indice.getByRole("link", { name: /Passo: descritor/ }).click();
  await expect(descritor).toBeVisible();
  await expect(page.locator("#secao-abertura")).toBeHidden();
  await expect(indice.locator('a[aria-current="true"]')).toHaveAttribute("href", "#secao-passo-descritor");
  await expect(page.locator("#previa [data-previa]:visible")).toHaveCount(1);
  await expect(page.locator('#previa [data-previa="passo-descritor"]')).toBeVisible();

  // O id é estrutura: chip com o rótulo, nenhum campo com "## ".
  await expect(descritor.locator(".tpl-chip")).toHaveText("Passo: descritor");
  await expect(descritor.getByRole("button", { name: "Remover seção" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: "+ Adicionar passo" })).toHaveCount(0);
  const valores = await page.locator("textarea, input:not([type=hidden])").evaluateAll((els) => els.map((e) => (e as HTMLInputElement).value));
  expect(valores.filter((v) => v.includes("## "))).toEqual([]);
  await expect(page.locator("#previa")).not.toContainText("## ");

  const titulo = `Descritor ${Date.now()}`;
  await descritor.locator("[data-campo=titulo]").fill(titulo);
  await expect(page.locator("[data-estado]")).toHaveText("Alterações não salvas.");

  const corpo = descritor.locator("[data-campo=corpo]");
  await corpo.fill("Para ");
  await descritor.locator("[data-variavel]").selectOption("nome_parceiro");
  await descritor.getByRole("button", { name: "{ } Variável" }).click();
  await expect(corpo).toHaveValue("Para {{nome_parceiro}}");
  await expect(page.locator("#previa h3:visible")).toHaveText(titulo); // a prévia segue só com a ativa
  await expect(page.locator("#previa .variavel-vazia")).toContainText(["{{nome_parceiro}}"]);
  await expect(page.locator("#previa")).toContainText("Texto válido para o fascículo.");

  await page.getByRole("button", { name: "Salvar", exact: true }).click();
  const cab = page.getByRole("heading", { name: /Confira o impacto antes de criar a versão \d+/ });
  await expect(cab).toBeVisible();
  const nova = (await cab.textContent())!.match(/versão (\d+)/)![1];
  await page.getByRole("button", { name: `Confirmar e criar versão ${nova}` }).click();

  await expect(page.getByText(`Versão ${nova} criada.`)).toBeVisible();
  await expect(page.locator("#secao-passo-descritor [data-campo=titulo]")).toHaveValue(titulo); // hidden, mas foi junto no Salvar
  await expect(page.locator("#secao-passo-descritor [data-campo=corpo]")).toHaveValue("Para {{nome_parceiro}}");
  expect(erros).toEqual([]);

  // Sem revista, sai com as versões; a página volta à aba do fascículo.
  await liberarBloqueio(page);
  await page.getByRole("link", { name: "Excluir template…" }).click();
  await expect(page.getByRole("heading", { level: 1, name: `Excluir o template ${nome} (LP F2) de 2026` })).toBeVisible();
  await excluirTemplate(page, nome, "F2");
});

test("template em uso: o Padrão da demonstração mostra as revistas e não sai", async ({ page }) => {
  await entrar(page, "/ui/templates/2026/?aba=F1");
  await page.getByRole("link", { name: "Excluir template Padrão (LP)…" }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Excluir o template Padrão (LP F1) de 2026" })).toBeVisible();
  await expect(page.getByText("Não dá para excluir: isto está em uso.")).toBeVisible();
  const linha = page.getByRole("row", { name: /^Revistas/ });
  await expect(linha.getByRole("link").first()).toHaveAttribute("href", /^\/ui\/revista\/2026\/\d+\/$/);
  await expect(page.getByText("Para excluir, troque o template das revistas que o usam.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Excluir" })).toHaveCount(0);

  await page.getByRole("link", { name: "‹ Voltar sem excluir" }).click();
  await expect(page).toHaveURL(/\/ui\/templates\/2026\/\?aba=F1$/);
  await expect(page.getByRole("link", { name: "Excluir template Padrão (LP)…" })).toBeVisible();
});

test("impresso não vê o Excluir template", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto("/admin/login/?next=/ui/templates/2026/?aba=F1");
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page.getByRole("link", { name: "Padrão", exact: true }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: /Excluir template/ })).toHaveCount(0);
});
