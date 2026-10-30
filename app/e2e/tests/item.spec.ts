// Arquivo do item na matriz (D-180): abrir o descritor da matriz Demonstração, abrir o modal
// "Arquivo do item", subir um PNG com texto alternativo, ver o item no preview e remover.
// Com o app no ar. Preparar (idempotente), na raiz do repositório:
//   APP_PORT=8031 docker compose up -d db app
//   docker compose run --rm app python manage.py migrate
//   docker compose run --rm app python manage.py criar_demo --ano 2026   # só com DEBUG (padrão do compose)
//   docker compose run --rm -e DJANGO_SUPERUSER_PASSWORD=<senha> app \
//     python manage.py createsuperuser --noinput --username e2e --email e2e@exemplo.invalid
//   cd app/e2e && E2E_BASE_URL=http://localhost:8031 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> \
//     npx playwright test item
// Grava de verdade, mas termina como começou: a tarefa D01 100-150 do 5EF fica sem arquivo.
import { expect, test, type Page } from "@playwright/test";

// PNG 1×1
const PNG = Buffer.from(
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
  "base64",
);
const TAREFA = "D01 100-150";

async function abrirDescritor(page: Page) {
  await page.goto(`/admin/nucleo/descritor/?q=${encodeURIComponent("Descritor 1 de demonstração (5EF)")}`);
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

  await page.goto("/admin/login/");
  await page.fill("#id_username", usuario!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page).toHaveURL(/\/admin\/$/);

  // 1. Modal: Cancelar fecha sem enviar; depois sobe o PNG.
  await abrirDescritor(page);
  let modal = await abrirModal(page);
  await modal.getByRole("button", { name: "Cancelar" }).click();
  await expect(modal).toBeHidden();
  modal = await abrirModal(page);
  await modal.getByLabel(/^Arquivo:?$/).setInputFiles({ name: "item.png", mimeType: "image/png", buffer: PNG });
  await modal.getByLabel("Texto alternativo (opcional)").fill(alt);
  await modal.getByRole("button", { name: "Enviar" }).click();
  await expect(page.locator(".messagelist")).toContainText(`Arquivo do item enviado para a tarefa ${TAREFA}.`);
  await expect(page.locator("#tarefa_set-group")).toContainText("PNG");

  // 2. Preview da revista DEMONSTRAÇÃO: o "Ver item" abre a imagem com o texto alternativo.
  await page.goto("/admin/nucleo/revista/");
  const href = await page.locator("#result_list a", { hasText: "DEMONSTRAÇÃO" }).first().getAttribute("href");
  const revista = href!.match(/revista\/(\d+)\//)![1];
  await page.goto(`/preview/${revista}/`);
  await expect(page.locator("body.app-initialized")).toBeAttached();
  await page.locator(".ver-item-btn").first().click();
  const imagem = page.locator("#itemModalImagem");
  await expect(imagem).toBeVisible();
  await expect(imagem).toHaveAttribute("alt", alt);
  await expect.poll(() => imagem.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);

  // 3. Remove o arquivo: a tarefa volta a ficar sem item.
  await abrirDescritor(page);
  modal = await abrirModal(page);
  await expect(modal.getByRole("link", { name: /\.png$/ })).toBeVisible();
  await modal.getByRole("button", { name: "Remover arquivo" }).click();
  await expect(page.locator(".messagelist")).toContainText(`Arquivo do item removido da tarefa ${TAREFA}.`);
  await expect(page.locator("#tarefa_set-group")).not.toContainText("PNG");
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
