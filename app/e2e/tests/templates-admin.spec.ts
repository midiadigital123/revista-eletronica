// Editor de template no admin (S11b1): "Inserir variável" e preview ao vivo, com o app no ar.
// Preparar (idempotente), na raiz do repositório:
//   APP_PORT=8012 docker compose up -d db app
//   docker compose run --rm app python manage.py carregar_cadastros --ano 2026
//   docker compose run --rm app python manage.py carregar_templates --ano 2026
//   docker compose run --rm -e DJANGO_SUPERUSER_PASSWORD=<senha> app \
//     python manage.py createsuperuser --noinput --username e2e --email e2e@exemplo.invalid
//   cd app/e2e && E2E_BASE_URL=http://localhost:8012 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> \
//     npx playwright test templates-admin
// Não salva nada: só digita, insere a variável e confere o preview (sair libera o bloqueio).
import { expect, test } from "@playwright/test";
import { entrar, liberarBloqueio } from "./helpers";

test("template: Inserir variável atualiza o preview", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));

  await entrar(page, "/admin/nucleo/template/?fasciculo__exact=F2");
  await expect(page.locator('.abas-templates [aria-current="page"]')).toHaveText("Textos F2");
  await page.locator("#result_list tbody tr th a").first().click();

  const editor = page.locator(".editor-template");
  const preview = editor.locator(".editor-template-preview");
  await expect(preview.locator("section.secao").first()).toBeVisible(); // preview inicial do texto salvo

  const area = editor.locator("textarea");
  await area.fill("## abertura\nBoas-vindas\n\nOlá, ");
  await editor.locator(".editor-template-variavel").selectOption("ano");
  await editor.getByRole("button", { name: "Inserir variável" }).click();

  await expect(area).toHaveValue("## abertura\nBoas-vindas\n\nOlá, {{ano}}");
  await expect(preview.locator(".variavel-vazia")).toHaveText("{{ano}}");
  await expect(preview.locator("h3")).toHaveText("Boas-vindas");
  await expect(editor.locator(".editor-template-erros")).toContainText("passo1"); // validar ao vivo
  expect(erros).toEqual([]);

  await liberarBloqueio(page);
});
