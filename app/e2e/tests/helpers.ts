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

/** Painel B: escolhe `valor` no select `seletor` e espera o HTMX trocar o corpo (o form velho
 * é marcado e some na troca; sem isso o próximo select pode cair no form que está saindo). */
export async function filtrarPainel(page: Page, seletor: string, valor: string | { label: string }) {
  await page.locator("#painel-corpo form.painel-filtros").evaluate((f) => f.setAttribute("data-velho", ""));
  await page.selectOption(seletor, valor);
  await expect(page.locator("#painel-corpo form.painel-filtros:not([data-velho])")).toHaveCount(1);
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
