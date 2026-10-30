// Painel da temporada e "Validado" (S12): abrir o painel, filtrar, validar a revista DEMONSTRAÇÃO.
// Com o app no ar. Preparar (idempotente), na raiz do repositório:
//   APP_PORT=8014 docker compose up -d db app
//   docker compose run --rm app python manage.py migrate
//   docker compose run --rm app python manage.py criar_demo --ano 2026   # só com DEBUG (padrão do compose)
//   docker compose run --rm -e DJANGO_SUPERUSER_PASSWORD=<senha> app \
//     python manage.py createsuperuser --noinput --username e2e --email e2e@exemplo.invalid
//   cd app/e2e && E2E_BASE_URL=http://localhost:8014 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> \
//     npx playwright test painel
// Grava de verdade: troca o nome padrão do projeto DEMONSTRAÇÃO (se ainda for o padrão), cria uma
// cópia do fechamento do F1 com uma marca nova (para o hash mudar a cada execução), valida e
// descarta a cópia no fim (a revista volta ao texto do template, sem "Validado").
import { expect, test, type Page } from "@playwright/test";
import { filtrarPainel } from "./helpers";

const FECHAMENTO = "#id_secao__F1__fechamento";

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

test("painel: filtrar e validar uma revista", async ({ page }) => {
  const usuario = process.env.E2E_ADMIN_USUARIO;
  const senha = process.env.E2E_ADMIN_SENHA;
  test.skip(!usuario || !senha, "defina E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA");
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const marca = `E2E ${Date.now()}`;

  await page.goto("/admin/login/?next=/painel/2026/");
  await page.fill("#id_username", usuario!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page.locator("#painel-corpo table")).toBeVisible();

  // 1. Filtros: parceiro DEMONSTRAÇÃO e "falta Validado" (o fim da execução anterior deixa sem).
  // Painel B: os selects trocam o corpo pelo HTMX e empurram a URL.
  await filtrarPainel(page, "#filtro-parceiro", { label: "DEMONSTRAÇÃO" });
  await filtrarPainel(page, "#filtro-falta", "validado");
  await expect(page).toHaveURL(/falta=validado/);
  const linhas = page.locator("#painel-corpo tbody tr");
  await expect(linhas).toHaveCount(1);
  const linha = linhas.first();
  await expect(linha).toContainText("DEMONSTRAÇÃO");
  await expect(linha.locator("td.coluna-validado .status-falta")).toBeVisible();
  const urlPainel = page.url();

  // 2. Nome padrão do projeto é pendência (Variáveis): o "falta" leva ao projeto.
  const variaveis = linha.locator("td.coluna-variaveis a", { hasText: "falta" });
  if (await variaveis.count()) {
    await variaveis.click();
    await page.fill("#id_nome", "DEMONSTRAÇÃO E2E");
    await page.click("input[name=_save]");
    await expect(page.locator(".messagelist")).toContainText("alterado com sucesso");
    await page.goto(urlPainel);
    await expect(linha.locator("td.coluna-variaveis .status-ok")).toBeVisible();
  }

  // 3. Revista: muda um texto (hash novo), salva e clica em "Validado".
  await linha.locator("th a.link-linha").click(); // o outro link da célula é o preview
  const urlRevista = page.url();
  await page.fill(FECHAMENTO, `Fechamento ${marca}.`);
  await page.click("input[name=_continue]");
  await expect(page.locator(".messagelist")).toContainText("Textos do F1 salvos: fechamento.");
  await expect(page.locator("#validacao")).not.toContainText("✓ Validado");
  await page.click("#botao-validado");
  await expect(page.locator(".messagelist")).toContainText("Revista validada.");
  await expect(page.locator("#validacao")).toContainText("✓ Validado");

  // 4. O painel com "falta Validado" não mostra mais a revista; sem o filtro, ✓.
  await page.goto(urlPainel);
  await expect(page.locator("#painel-corpo")).toContainText("Nenhuma revista com esse filtro");
  await filtrarPainel(page, "#filtro-falta", "");
  await expect(page.locator("#painel-corpo tbody tr").first().locator("td.coluna-validado .status-ok")).toBeVisible();

  // 5. Limpa: descarta a cópia (o hash muda e o "Validado" cai).
  await page.goto(urlRevista);
  await page.check("#id_descartar__F1__fechamento");
  await page.click("input[name=_continue]");
  await expect(page.locator(".messagelist")).toContainText("Textos do F1 salvos: fechamento.");
  await expect(page.locator("#validacao")).not.toContainText("✓ Validado");
  expect(erros).toEqual([]);

  await liberarBloqueio(page);
});
