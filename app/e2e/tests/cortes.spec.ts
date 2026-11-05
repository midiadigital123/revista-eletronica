// Grade de cortes (S11a): preenche os cortes de 2 parceiros e confere a gravação.
// Precisa do servidor com um ano carregado e de um superusuário:
//   docker compose run --rm app python manage.py carregar_cadastros --ano 2026
//   DJANGO_SUPERUSER_PASSWORD=... docker compose run --rm -e DJANGO_SUPERUSER_PASSWORD app \
//     python manage.py createsuperuser --noinput --username e2e --email e2e@exemplo.org
//   E2E_BASE_URL=http://localhost:8011 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=... npx playwright test cortes
// Os parceiros são criados pelo próprio teste, com nome único por execução; o limpar.ts os apaga no fim (D-224):
// rode só contra um banco descartável (o do seu worktree), nunca contra dados reais.
import { expect, test, type Page } from "@playwright/test";
import { alpinePronto, entrar, novoParceiro } from "./helpers";

async function criarParceiro(page: Page, nome: string) {
  await page.goto("/admin/nucleo/parceiro/add/");
  await page.fill("#id_nome", nome);
  await page.click("input[name=_save]");
  await expect(page.locator(".messagelist .success")).toBeVisible();
}

test("preenche os cortes de 2 parceiros", async ({ page }) => {
  const sufixo = Date.now().toString(36).toUpperCase();
  const a = `E2E A ${sufixo}`;
  const b = `E2E B ${sufixo}`;
  await entrar(page);
  await criarParceiro(page, a);
  await criarParceiro(page, b);

  await page.goto("/admin/nucleo/corte/");
  const celula = (parceiro: string, coluna: string) => page.getByLabel(`${parceiro} ${coluna}`, { exact: true });

  // Erro da D-055: nada grava e a linha mostra o motivo.
  await celula(a, "5EF LP").fill("200, 150");
  await celula(b, "5EF LP").fill("150, 200, 250");
  await page.click("input[value='Salvar cortes']");
  await expect(page.locator(".errorlist")).toContainText(`${a} — 5EF LP: cortes precisam ser crescentes.`);
  await expect(celula(a, "5EF LP")).toHaveValue("200, 150");

  await celula(a, "5EF LP").fill("125, 175, 225");
  await celula(a, "9EF MT").fill("225 275 325");
  await celula(b, "5EF MT").fill("150, 200, 250, 300");
  await page.click("input[value='Salvar cortes']");
  await expect(page.locator(".messagelist .success")).toContainText("2 parceiro(s) alterado(s)");

  await page.reload();
  await expect(celula(a, "5EF LP")).toHaveValue("125, 175, 225");
  await expect(celula(a, "9EF MT")).toHaveValue("225, 275, 325");
  await expect(celula(b, "5EF LP")).toHaveValue("150, 200, 250");
  await expect(celula(b, "5EF MT")).toHaveValue("150, 200, 250, 300");
  await expect(celula(b, "9EF MT")).toHaveValue("");
});

// Comentários 3 e 6 da revisão de 03/11: sem editar nada, a grade não pode acusar alteração
// nem pedir confirmação ao sair. U3: a grade salva por célula; o status fica ocioso.
test("cortes sem edição não acusa alteração", async ({ page }) => {
  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  const status = page.locator("[data-status-salvo]");
  await alpinePronto(page);
  await expect(status.getByText("Cada campo salva sozinho")).toBeVisible();
  await expect(page.locator("[data-grade] [aria-invalid]")).toHaveCount(0);
  page.on("dialog", (d) => { throw new Error(`diálogo inesperado: ${d.message()}`); });
  await page.reload();
  await alpinePronto(page);
});

// U7a: Cortes, Variáveis, Revistas e Lotes viraram o hub Projetos. As URLs antigas redirecionam para a
// aba equivalente (favoritos não quebram) e as abas trocam de tela mantendo o ano.
test("rotas antigas levam às abas do hub Projetos", async ({ page }) => {
  await entrar(page, "/cortes/2026/");
  await expect(page).toHaveURL(/\/ui\/projeto\/ano\/2026\/cortes\/$/);
  const abas = page.getByRole("navigation", { name: "Projetos de 2026" });
  await expect(abas.getByRole("link", { name: "Cortes" })).toHaveAttribute("aria-current", "page");
  await abas.getByRole("link", { name: "Variáveis" }).click();
  await expect(page).toHaveURL(/\/ui\/projeto\/ano\/2026\/variaveis\/$/);
  await page.goto("/ui/variaveis/2026/");
  await expect(page).toHaveURL(/\/ui\/projeto\/ano\/2026\/variaveis\/$/);
  for (const antiga of ["/ui/revista/2026/", "/ui/lotes/2026/matriz/", "/ui/lotes/2026/template/"]) {
    await page.goto(antiga);
    await expect(page).toHaveURL(/\/ui\/projeto\/ano\/2026\/$/);
  }
  await expect(page.getByRole("button", { name: "Atribuir matriz…" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Atribuir template…" })).toBeVisible();
});

// E2 (D-205, D-208): "Excluir…" no nome do parceiro leva à página de excluir e volta para a grade.
// Os parceiros "E2E…" daqui não ficam na grade: o livre é excluído; o com corte é desativado e,
// sem o corte, sai também de 2026. O 2025 (vazio) só é lido.
const GRADE = "/ui/projeto/ano/2026/cortes/";
const linha = (page: Page, nome: string) => page.locator(`tr[data-parceiro="${nome}"]`);

test("exclui pela grade um parceiro sem cortes", async ({ page }) => {
  const nome = `E2E Livre ${Date.now().toString(36).toUpperCase()}`;
  await entrar(page, GRADE);
  await novoParceiro(page, nome);
  await linha(page, nome).getByRole("link", { name: `Excluir ${nome}…` }).click();
  await expect(page).toHaveURL(/\/ui\/excluir\/parceiro\/\d+\/\?voltar=/);
  await expect(page.getByText("Nada usa isto.")).toBeVisible();
  await page.getByLabel("Para confirmar, digite").fill(nome);
  await page.getByRole("button", { name: "Excluir" }).click();
  await expect(page).toHaveURL(new RegExp(`${GRADE}$`));
  await expect(page.getByText(`Exclusão feita: o parceiro ${nome}.`)).toBeVisible();
  await expect(linha(page, nome)).toHaveCount(0);
});

test("parceiro com corte desativado some do ano sem dados e fica marcado no ano com dados", async ({ page }) => {
  const nome = `E2E Sai ${Date.now().toString(36).toUpperCase()}`;
  await entrar(page, GRADE);
  await novoParceiro(page, nome);
  await alpinePronto(page);
  const celula = linha(page, nome).locator("td input.input").first();
  const status = page.locator("[data-status-salvo]");
  await celula.fill("125");
  await page.keyboard.press("Tab");
  await expect(status.getByText(/Salvo às \d\d:\d\d/)).toBeVisible();

  await linha(page, nome).getByRole("link", { name: `Excluir ${nome}…` }).click();
  await expect(page.getByText("Não dá para excluir: isto está em uso.")).toBeVisible();
  await page.getByRole("button", { name: "Desativar o parceiro" }).click();
  await expect(page).toHaveURL(new RegExp(`${GRADE}$`));
  await expect(page.getByText(`Parceiro ${nome} desativado: sai da grade dos anos em que não tem cortes.`)).toBeVisible();
  await expect(linha(page, nome).getByText("desativado", { exact: true })).toBeVisible();

  await page.goto("/ui/projeto/ano/2025/cortes/");
  await expect(page.locator("[data-grade]")).toBeVisible();
  await expect(linha(page, nome)).toHaveCount(0);

  // Limpa o corte (o projeto é arquivado): sem dados em 2026, o desativado sai da grade de 2026 também.
  await page.goto(GRADE);
  await alpinePronto(page);
  await linha(page, nome).locator("td input.input").first().fill("");
  await page.keyboard.press("Tab");
  await expect(status.getByText(/Salvo às \d\d:\d\d/)).toBeVisible();
  await page.reload();
  await expect(linha(page, nome)).toHaveCount(0);
});

test("impresso não vê Excluir na grade", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto(`/admin/login/?next=${GRADE}`);
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page.locator("[data-grade] tbody tr[data-parceiro]").first()).toBeVisible();
  await expect(page.locator("[data-grade]").getByRole("link", { name: /^Excluir / })).toHaveCount(0);
});
