// Texto por seção na revista (S11b2): editar → cópia → versão nova do template → aviso + diff →
// descartar → volta ao vivo. Com o app no ar.
// Preparar (idempotente), na raiz do repositório:
//   APP_PORT=8014 docker compose up -d db app
//   docker compose run --rm app python manage.py migrate
//   docker compose run --rm app python manage.py criar_demo --ano 2026   # só com DEBUG (padrão do compose)
//   docker compose run --rm -e DJANGO_SUPERUSER_PASSWORD=<senha> app \
//     python manage.py createsuperuser --noinput --username e2e --email e2e@exemplo.invalid
//   cd app/e2e && E2E_BASE_URL=http://localhost:8014 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> \
//     npx playwright test revista-textos
// Grava de verdade: cada execução cria uma versão nova do template "Padrão" LP F1 de 2026 e
// termina sem cópia na revista DEMONSTRAÇÃO (descartada no fim). Use num banco de desenvolvimento.
import { expect, test, type Page } from "@playwright/test";

const INTRO = "#id_secao__F1__introducao";

async function liberarBloqueio(page: Page) {
  // Mesmo POST do sendBeacon do pagehide: fechar o contexto não dispara o pagehide.
  const campo = page.locator("#bloqueio-sessao");
  const form = {
    csrfmiddlewaretoken: await page.locator("[name=csrfmiddlewaretoken]").first().inputValue(),
    alvo: (await campo.getAttribute("data-alvo"))!,
    id: (await campo.getAttribute("data-id"))!,
    sessao: await campo.inputValue(),
  };
  expect((await page.request.post("/bloqueio/liberar", { form })).status()).toBe(204);
}

test("revista: cópia por seção, aviso com diff e descartar", async ({ page }) => {
  const usuario = process.env.E2E_ADMIN_USUARIO;
  const senha = process.env.E2E_ADMIN_SENHA;
  test.skip(!usuario || !senha, "defina E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA");
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const marca = `E2E ${Date.now()}`;

  await page.goto("/admin/login/?next=/admin/nucleo/revista/");
  await page.fill("#id_username", usuario!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await page.locator("#result_list a", { hasText: "DEMONSTRAÇÃO" }).first().click();
  const urlRevista = page.url();

  // 1. Editar só a introdução do F1: o preview da seção funciona e a cópia nasce ao salvar.
  const area = page.locator(INTRO);
  await area.fill(`Meu texto ${marca} para {{nome_parceiro}}.`);
  const caixa = page.locator(".editor-template", { has: area });
  await expect(caixa.locator(".editor-template-preview")).toContainText(`Meu texto ${marca}`);
  await expect(caixa.locator(".editor-template-preview .variavel-vazia")).toHaveText("{{nome_parceiro}}");
  await page.click("input[name=_continue]");
  await expect(page.locator(".messagelist")).toContainText("Textos do F1 salvos: introducao.");
  await expect(page.locator(".field-secao__F1__introducao .help")).toContainText("Texto editado nesta revista (cópia)");
  await expect(page.locator(".field-secao__F1__fechamento .help")).toContainText("Texto do template");

  // 2. Versão nova do template mudando a introdução (tela de impacto → confirmar).
  const linhaF1 = page.locator("tr", { has: page.locator("td.field-fasciculo", { hasText: "F1" }) });
  const templateId = await linhaF1.locator("select").inputValue();
  await page.goto(`/admin/nucleo/template/${templateId}/change/`);
  const texto = page.locator("#id_texto");
  const atual = await texto.inputValue();
  const novo = atual.replace(/(## introducao\n[^\n]*\n\n[\s\S]*?)(\n+## )/, `$1 Atualizado ${marca}.$2`);
  expect(novo).not.toBe(atual);
  await texto.fill(novo);
  await page.click("input[name=_save]");
  await page.click("input[name=_confirmar]");
  await expect(page.locator(".messagelist")).toContainText("criada");

  // 3. A revista avisa e mostra "seu texto | template novo"; descartar volta ao vivo.
  await page.goto(urlRevista);
  await expect(page.getByText("Seções desatualizadas: introducao.")).toBeVisible();
  const tabela = page.locator(".field-secao__F1__introducao table.diff");
  await expect(tabela).toContainText("Seu texto");
  await expect(tabela).toContainText("Template novo");
  await expect(tabela).toContainText(`Atualizado`);
  await page.check("#id_descartar__F1__introducao");
  await page.click("input[name=_continue]");
  await expect(page.locator(".messagelist")).toContainText("Textos do F1 salvos: introducao.");
  await expect(page.getByText("Seções desatualizadas")).toHaveCount(0);
  await expect(area).toHaveValue(new RegExp(`Atualizado ${marca}\\.`));
  await expect(page.locator(".field-secao__F1__introducao .help")).toContainText("Texto do template");
  expect(erros).toEqual([]);

  await liberarBloqueio(page);
});
