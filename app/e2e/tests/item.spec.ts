// Arquivo do item na matriz (D-180): abrir o descritor de uma cópia própria da Demonstração, abrir o modal
// "Arquivo do item", subir um PNG com texto alternativo, ver o item no preview e remover.
// Com o app no ar. Preparar (idempotente), na raiz do repositório:
//   APP_PORT=8031 docker compose up -d db app
//   docker compose run --rm app python manage.py migrate
//   docker compose run --rm app python manage.py criar_demo --ano 2026   # só com DEBUG (padrão do compose)
//   docker compose run --rm -e DJANGO_SUPERUSER_PASSWORD=<senha> app \
//     python manage.py createsuperuser --noinput --username e2e --email e2e@exemplo.invalid
//   cd app/e2e && E2E_BASE_URL=http://localhost:8031 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> \
//     npx playwright test item
// Grava só na matriz e na revista que o teste cria (D-225); o limpar.ts apaga as duas no fim (D-224).
import { expect, test, type Page } from "@playwright/test";
import { matrizPropria, revistaPropria } from "./helpers";

// PNG 1×1
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
  "base64",
);
// PDF mínimo de uma página em branco
const PDF = Buffer.from(
  "%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n" +
    "3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n",
);
const TAREFA = "D01 100-150";

/** O D01 do 5EF na matriz `matriz` (pk): a cópia própria tem o mesmo texto da Demonstração. */
async function abrirDescritor(page: Page, matriz: string) {
  const q = encodeURIComponent("Descritor 1 de demonstração (5EF)");
  await page.goto(`/admin/nucleo/descritor/?matriz_etapa_cc__matriz__id__exact=${matriz}&q=${q}`);
  await page.locator("#result_list").getByRole("link", { name: "D01" }).click();
  await expect(page.locator("#bloqueio-sessao")).toBeAttached(); // editável: o modal só existe com o bloqueio
}

async function abrirModal(page: Page) {
  await page.getByRole("button", { name: `Arquivo do item da tarefa ${TAREFA}` }).click();
  const modal = page.getByRole("dialog", { name: `Arquivo do item da tarefa ${TAREFA}` });
  await expect(modal).toBeVisible();
  const confirmar = modal.getByLabel(/Confirmo: afeta/);
  if (await confirmar.count()) await confirmar.check();
  return modal;
}

test("item: sobe um PNG com texto alternativo, vê no preview e remove", async ({ page }) => {
  const usuario = process.env.E2E_ADMIN_USUARIO;
  const senha = process.env.E2E_ADMIN_SENHA;
  test.skip(!usuario || !senha, "defina E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA");
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const alt = `Gráfico do item E2E ${Date.now()}`;

  await page.goto("/admin/login/?next=/admin/");
  await page.fill("#id_username", usuario!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page).toHaveURL(/\/admin\/$/);
  // Matriz e revista próprias (D-225): a cópia da Demonstração e um parceiro "E2E Item …" que a usa.
  const matriz = await matrizPropria(page, "Item");
  const { revista } = await revistaPropria(page, "Item", matriz.nome);

  // 1. Modal: Cancelar fecha sem enviar; depois sobe o PNG.
  await abrirDescritor(page, matriz.pk);
  let modal = await abrirModal(page);
  await modal.getByRole("button", { name: "Cancelar" }).click();
  await expect(modal).toBeHidden();
  modal = await abrirModal(page);
  await modal.getByLabel(/^Arquivo:?$/).setInputFiles({ name: "item.png", mimeType: "image/png", buffer: PNG });
  await modal.getByLabel("Texto alternativo (opcional)").fill(alt);
  await modal.getByRole("button", { name: "Enviar" }).click();
  await expect(page.locator(".messagelist")).toContainText(`Arquivo do item enviado para a tarefa ${TAREFA}.`);
  await expect(page.locator("#tarefa_set-group")).toContainText("PNG");

  // 2. Preview da revista própria: o "Ver item" abre a imagem com o texto alternativo.
  await page.goto(`/preview/${revista}/`);
  await expect(page.locator("body.app-initialized")).toBeAttached();
  await page.locator(".ver-item-btn").first().click();
  const imagem = page.locator("#itemModalImagem");
  await expect(imagem).toBeVisible();
  await expect(imagem).toHaveAttribute("alt", alt);
  await expect.poll(() => imagem.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);

  // 3. Troca por um PDF: o iframe do "Ver item" carrega (200, sem X-Frame-Options DENY).
  await abrirDescritor(page, matriz.pk);
  modal = await abrirModal(page);
  await modal.getByLabel(/^Arquivo:?$/).setInputFiles({ name: "item.pdf", mimeType: "application/pdf", buffer: PDF });
  await modal.getByRole("button", { name: "Enviar" }).click();
  await expect(page.locator(".messagelist")).toContainText(`Arquivo do item enviado para a tarefa ${TAREFA}.`);
  await page.goto(`/preview/${revista}/`);
  await expect(page.locator("body.app-initialized")).toBeAttached();
  const respostaPdf = page.waitForResponse((r) => /\/arquivos\/itens\/[^/]+\.pdf$/.test(r.url()));
  await page.locator(".ver-item-btn").first().click();
  const pdf = await respostaPdf;
  expect(pdf.status()).toBe(200);
  expect((pdf.headers()["x-frame-options"] ?? "").toUpperCase()).not.toBe("DENY");
  await expect(page.locator("#itemModalFrame")).toBeVisible();
  await expect(page.locator("#itemModalFrame")).toHaveAttribute("aria-label", alt);
  const frame = await (await page.locator("#itemModalFrame").elementHandle())!.contentFrame();
  // Bloqueado pelo X-Frame-Options, o Chrome troca o frame por chrome-error://; o Chromium
  // headless não renderiza PDF, então o frame liberado fica em about:blank.
  expect(frame!.url()).not.toContain("chrome-error");

  // 4. Remove o arquivo: a tarefa volta a ficar sem item.
  await abrirDescritor(page, matriz.pk);
  modal = await abrirModal(page);
  await expect(modal.getByRole("link", { name: /\.pdf$/ })).toBeVisible();
  await modal.getByRole("button", { name: "Remover arquivo" }).click();
  await expect(page.locator(".messagelist")).toContainText(`Arquivo do item removido da tarefa ${TAREFA}.`);
  await expect(page.locator("#tarefa_set-group")).not.toContainText("PDF");
  expect(erros).toEqual([]);

  // Libera o bloqueio (fechar o contexto não dispara o pagehide).
  const campo = page.locator("#bloqueio-sessao");
  const form = {
    csrfmiddlewaretoken: await page.locator("[name=csrfmiddlewaretoken]").first().inputValue(),
    alvo: (await campo.getAttribute("data-alvo"))!,
    id: (await campo.getAttribute("data-id"))!,
    sessao: await campo.inputValue(),
  };
  expect((await page.request.post("/bloqueio/liberar", { form })).status()).toBe(204);
});
