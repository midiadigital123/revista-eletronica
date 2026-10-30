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
