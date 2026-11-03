import { expect, test, type Page } from "@playwright/test";

/** Entra no admin e cai em `proxima`. Sem E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA, pula o teste. */
export async function entrar(page: Page, proxima = "/admin/") {
  const usuario = process.env.E2E_ADMIN_USUARIO;
  const senha = process.env.E2E_ADMIN_SENHA;
  test.skip(!usuario || !senha, "defina E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA");
  await page.goto(`/admin/login/?next=${encodeURIComponent(proxima)}`);
  await page.fill("#id_username", usuario!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page).not.toHaveURL(/\/admin\/login\//);
}

/** O Alpine já ligou a página (o `:data-estado` do status do autosave só existe depois do init). */
export const alpinePronto = (page: Page) => expect(page.locator("[data-status-salvo]")).toHaveAttribute("data-estado", "");

/** Cortes (U4): "+ Adicionar parceiro" abre a linha com o foco no nome; Enter cria e recarrega. */
export async function novoParceiro(page: Page, nome: string) {
  await alpinePronto(page);
  await page.getByRole("button", { name: "Adicionar parceiro" }).click();
  await expect(page.locator("#novo-parceiro")).toBeFocused();
  await page.keyboard.type(nome);
  await page.keyboard.press("Enter");
  await expect(page.locator(`tr[data-parceiro="${nome}"]`)).toHaveCount(1);
}

/** Painel B: roda `acao` e espera o HTMX trocar o corpo (o form velho é marcado e some na troca;
 * sem isso a próxima ação pode cair no corpo que está saindo). */
async function trocarCorpoPainel(page: Page, acao: () => Promise<unknown>) {
  await page.locator("#painel-corpo form.painel-filtros").evaluate((f) => f.setAttribute("data-velho", ""));
  await acao();
  await expect(page.locator("#painel-corpo form.painel-filtros:not([data-velho])")).toHaveCount(1);
}

/** Painel B: escolhe `valor` no select `seletor` (hoje só o #filtro-parceiro). */
export async function filtrarPainel(page: Page, seletor: string, valor: string | { label: string }) {
  await trocarCorpoPainel(page, () => page.selectOption(seletor, valor));
}

/** Painel B: clica no contador da coluna (filtro de falta) ou, com null, em "Limpar filtro". */
export async function filtrarFalta(page: Page, coluna: string | null) {
  const alvo = coluna
    ? page.locator("#painel-corpo .painel-contadores a", { hasText: coluna })
    : page.locator("#painel-corpo .painel-limpar");
  await trocarCorpoPainel(page, () => alvo.click());
}

/** Mesmo POST do sendBeacon do pagehide: fechar o contexto não dispara o pagehide, e a
 * próxima execução abriria em somente leitura por até 30 s. */
export async function liberarBloqueio(page: Page) {
  const campo = page.locator("#bloqueio-sessao");
  const form = {
    csrfmiddlewaretoken: await page.locator("[name=csrfmiddlewaretoken]").first().inputValue(),
    alvo: (await campo.getAttribute("data-alvo"))!,
    id: (await campo.getAttribute("data-id"))!,
    sessao: await campo.inputValue(),
  };
  expect((await page.request.post("/bloqueio/liberar", { form })).status()).toBe(204);
}

/** Hub Projetos, aba Lista (U7a): marca o parceiro e roda "Atribuir matriz…" ou "Atribuir template…"
 * (o diálogo da barra de ações em massa). Escolhas pelo rótulo: { matriz } ou { componente, f1?, f2? }. */
export async function atribuirEmMassa(
  page: Page, parceiro: string, escolhas: { matriz: string } | { componente: string; f1?: string; f2?: string },
) {
  await page.goto("/ui/projeto/ano/2026/");
  await page.getByLabel(`Marcar ${parceiro}`, { exact: true }).check();
  const titulo = "matriz" in escolhas ? "Atribuir matriz" : "Atribuir template";
  await page.getByRole("button", { name: `${titulo}…` }).click();
  const dialogo = page.getByRole("dialog", { name: titulo });
  await expect(dialogo).toBeVisible();
  if ("matriz" in escolhas) {
    await dialogo.getByLabel("Matriz").selectOption({ label: escolhas.matriz });
  } else {
    await dialogo.getByLabel("Componente").selectOption({ label: escolhas.componente });
    if (escolhas.f1) await dialogo.getByLabel("Template F1").selectOption({ label: escolhas.f1 });
    if (escolhas.f2) await dialogo.getByLabel("Template F2").selectOption({ label: escolhas.f2 });
  }
  await dialogo.getByRole("button", { name: titulo, exact: true }).click();
}

/** Lista de Projetos: o id da revista `codigo` (LP, MT) no grupo do parceiro (linha por revista). */
export async function revistaDaLista(page: Page, parceiro: string, codigo: string) {
  const grupo = page.locator("tbody", { has: page.getByLabel(`Marcar ${parceiro}`, { exact: true }) });
  const href = await grupo
    .locator("a.link-linha", { has: page.locator(".badge", { hasText: new RegExp(`^${codigo}$`) }) })
    .getAttribute("href");
  return href!.split("/").at(-2)!;
}
