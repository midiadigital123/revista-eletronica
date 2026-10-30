// Grade de cortes (S11a): preenche os cortes de 2 parceiros e confere a gravação.
// Precisa do servidor com um ano carregado e de um superusuário:
//   docker compose run --rm app python manage.py carregar_cadastros --ano 2026
//   DJANGO_SUPERUSER_PASSWORD=... docker compose run --rm -e DJANGO_SUPERUSER_PASSWORD app \
//     python manage.py createsuperuser --noinput --username e2e --email e2e@exemplo.org
//   E2E_BASE_URL=http://localhost:8011 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=... npx playwright test cortes
// Os parceiros são criados pelo próprio teste, com nome único por execução, e ficam no banco:
// rode só contra um banco descartável (o do seu worktree), nunca contra dados reais.
import { expect, test, type Page } from "@playwright/test";
import { entrar } from "./helpers";

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
