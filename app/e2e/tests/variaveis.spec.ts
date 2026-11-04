// Planilha de Variáveis (U10d): o projeto aberto por outra pessoa trava só a linha dele, e duas abas
// não se sobrescrevem em silêncio (409 com `atual`, como a grade de Cortes). Preparo de painel.spec.ts
// (criar_demo --ano 2026 e o superusuário e2e). Cria um parceiro com corte (vira projeto) e, na 1ª vez,
// o usuário "e2e-outra" (Pedagógica), cuja senha é trocada a cada execução; as variáveis voltam ao
// valor original no fim.
import { expect, test, type Browser, type Page } from "@playwright/test";
import { alpinePronto, entrar, liberarBloqueio, novoParceiro } from "./helpers";

const PLANILHA = "/ui/projeto/ano/2026/variaveis/";
const OUTRA = "e2e-outra";
const linhaDe = (page: Page, parceiro: string) => page.locator('tbody[id^="projeto-"]', { has: page.getByRole("link", { name: parceiro, exact: true }) });
const regional = (linha: ReturnType<typeof linhaDe>) => linha.locator('input.input[name$="-nome_regional"]');
const status = (page: Page) => page.locator("[data-status-salvo]");

/** Sai do campo e espera o "Salvo às" (ou confirma o modal de impacto, se a revista validada usa a variável). */
async function sairESalvar(page: Page) {
  await page.keyboard.press("Tab");
  const modal = page.getByRole("dialog");
  await expect(status(page).getByText(/Salvo às \d\d:\d\d/).or(modal)).toBeVisible();
  if (await modal.isVisible()) await modal.getByRole("button", { name: /e tirar Validado$/ }).click();
  await expect(status(page).getByText(/Salvo às \d\d:\d\d/)).toBeVisible();
}

/** Parceiro novo com um corte (já com o e2e logado): o projeto dele nasce em 2026 e entra na planilha. */
async function projetoNovo(page: Page, prefixo: string) {
  const nome = `E2E ${prefixo} ${Date.now().toString(36).toUpperCase()}`;
  await page.goto("/ui/projeto/ano/2026/cortes/");
  await novoParceiro(page, nome);
  await alpinePronto(page);
  await page.getByLabel(`${nome} 5EF LP`, { exact: true }).fill("150, 300");
  await sairESalvar(page);
  return nome;
}

/** Outra pessoa da Pedagógica, num contexto de navegador próprio (o bloqueio é por usuário, D-191). */
async function outraPessoa(page: Page, browser: Browser) {
  const senha = `E2e-${crypto.randomUUID()}`;
  await page.goto(`/admin/auth/user/?q=${OUTRA}`);
  const existente = page.getByRole("link", { name: OUTRA, exact: true });
  const nova = !(await existente.count());
  if (nova) {
    await page.goto("/admin/auth/user/add/");
    await page.fill("#id_username", OUTRA);
  } else {
    const href = (await existente.getAttribute("href"))!.split("?")[0]; // /admin/auth/user/<pk>/change/
    await page.goto(href.replace(/change\/$/, "password/"));
  }
  await page.fill("#id_password1", senha);
  await page.fill("#id_password2", senha);
  await page.locator("input[type=submit]").first().click();
  await expect(page.locator(".messagelist .success")).toBeVisible();
  if (nova) {
    await page.locator("#id_groups").selectOption({ label: "Pedagógica" });
    await page.locator("input[name=_save]").click();
    await expect(page.locator(".messagelist .success")).toBeVisible();
  }
  const outra = await (await browser.newContext()).newPage();
  await outra.goto(`/admin/login/?next=${encodeURIComponent(PLANILHA)}`);
  await outra.fill("#id_username", OUTRA);
  await outra.fill("#id_password", senha);
  await outra.click("input[type=submit]");
  await expect(outra).toHaveURL(new RegExp(`${PLANILHA}$`));
  return outra;
}

test("planilha: projeto aberto por outra pessoa trava só a linha dele; o resto segue editável", async ({ page, browser }) => {
  await entrar(page);
  const parceiro = await projetoNovo(page, "Travado");
  const parceiroLivre = await projetoNovo(page, "Livre");
  const outra = await outraPessoa(page, browser);
  await alpinePronto(outra);

  // A 1ª pessoa (e2e) abre a ficha do projeto: segura o bloqueio dele.
  await page.goto(PLANILHA);
  const pk = (await linhaDe(page, parceiro).getAttribute("id"))!.replace("projeto-", "");
  await page.goto(`/ui/projeto/${pk}/`);
  await expect(page.locator("#bloqueio-sessao")).toHaveCount(1);

  // A outra pessoa edita a linha travada: só ela fica só leitura, com o nome de quem edita.
  const travada = linhaDe(outra, parceiro);
  const livre = linhaDe(outra, parceiroLivre);
  const original = await regional(livre).inputValue();
  await regional(travada).fill("E2E travada");
  await outra.keyboard.press("Tab");
  await expect(status(outra).getByText("Não salvo: projeto aberto por outra pessoa")).toBeVisible();
  await expect(travada.getByRole("alert")).toContainText(`em edição por ${process.env.E2E_ADMIN_USUARIO}`);
  await expect(travada.locator('input.input[name$="-sigla_programa"]')).not.toBeEditable();
  await expect(travada.getByRole("button", { name: /^Copiar de/ })).toBeDisabled();
  await expect(outra.getByText("a página ficou somente leitura")).toHaveCount(0);

  // O resto da planilha continua editável e salva (o status segue no erro da linha travada: erro vence salvo).
  await expect(regional(livre)).toBeEditable();
  for (const valor of [`${original} E2E`, original]) {
    const salvou = outra.waitForResponse((r) => r.url().endsWith("/campo/") && r.status() === 200);
    await regional(livre).fill(valor);
    await outra.keyboard.press("Tab");
    expect((await (await salvou).json()).ok).toBe(true); // projeto novo: nenhuma revista validada, sem modal
  }
  await expect(regional(livre)).not.toHaveAttribute("aria-invalid", "true");

  // A ficha fecha: "Tentar de novo" grava e a linha volta a ser editável.
  await liberarBloqueio(page);
  await status(outra).getByRole("button", { name: "Tentar de novo" }).click();
  await expect(status(outra).getByText(/Salvo às \d\d:\d\d/)).toBeVisible();
  await expect(travada.locator('input.input[name$="-sigla_programa"]')).toBeEditable();
  await expect(travada.getByRole("alert")).toHaveCount(0);
  await outra.context().close();
});

test("planilha: a outra aba com o valor antigo recebe conflito com o valor de agora e não grava por cima", async ({ page, context }) => {
  await entrar(page);
  const parceiro = await projetoNovo(page, "Duas abas");
  await page.goto(PLANILHA);
  await alpinePronto(page);
  const outra = await context.newPage();
  await outra.goto(PLANILHA);
  await alpinePronto(outra);

  await regional(linhaDe(page, parceiro)).fill("Regional A");
  await sairESalvar(page);
  await regional(linhaDe(outra, parceiro)).fill("Regional B");
  await outra.keyboard.press("Tab");
  await expect(status(outra).getByText("Não salvo: outra pessoa mudou este valor")).toBeVisible();
  await expect(linhaDe(outra, parceiro).getByText("agora: Regional A")).toBeVisible();
  await page.reload();
  await expect(regional(linhaDe(page, parceiro))).toHaveValue("Regional A");

  // "Tentar de novo" na 2ª aba grava por cima, de propósito.
  await status(outra).getByRole("button", { name: "Tentar de novo" }).click();
  await expect(status(outra).getByText(/Salvo às \d\d:\d\d/)).toBeVisible();
  await page.reload();
  await expect(regional(linhaDe(page, parceiro))).toHaveValue("Regional B");
  await outra.close();
});
