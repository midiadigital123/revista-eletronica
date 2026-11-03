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
import { alpinePronto, filtrarFalta, filtrarPainel } from "./helpers";

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

  // 1. Filtros: parceiro DEMONSTRAÇÃO e o contador "Validado" (o fim da execução anterior deixa sem).
  // Painel B: o select e o contador trocam o corpo pelo HTMX e empurram a URL.
  await filtrarPainel(page, "#filtro-parceiro", { label: "DEMONSTRAÇÃO" });
  await filtrarFalta(page, "Validado");
  await expect(page).toHaveURL(/falta=validado/);
  await expect(page.locator(".painel-contadores a[aria-current=true]")).toContainText("Validado");
  await expect(page.locator("#painel-corpo .painel-grupo")).toHaveCount(1);
  const linhas = page.locator("#painel-corpo tbody tr[data-revista]");
  await expect(linhas).toHaveCount(1);
  const linha = linhas.first();
  await expect(linha).toContainText("DEMONSTRAÇÃO");
  await expect(linha.locator("td.coluna-validado .status-falta")).toBeVisible();
  const urlPainel = page.url();

  // 2. Nome padrão do projeto é pendência (Variáveis): o "falta" leva à ficha B do projeto.
  const variaveis = linha.locator("td.coluna-variaveis a", { hasText: "falta" });
  if (await variaveis.count()) {
    await variaveis.click();
    await expect(page).toHaveURL(/\/ui\/projeto\/\d+\/$/);
    await alpinePronto(page);
    await page.fill("#id_nome", "DEMONSTRAÇÃO E2E");
    await page.press("#id_nome", "Tab"); // U3: o campo salva sozinho ao sair dele
    await expect(page.locator("[data-status-salvo]").getByText(/Salvo às \d/)).toBeVisible(); // o texto oculto (x-show) já existe: espera o visível
    await page.goto(urlPainel);
    await expect(linha.locator("td.coluna-variaveis .status-ok")).toBeVisible();
  }

  // 3. Revista: muda um texto (hash novo), salva e clica em "Validado".
  // O nome leva à revista B; o roteiro edita no admin (mesma revista).
  await page.goto(`/admin/nucleo/revista/${await linha.getAttribute("data-revista")}/change/`);
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
  await filtrarFalta(page, null);
  await expect(page).not.toHaveURL(/falta=/);
  await expect(page.locator("#painel-corpo tbody tr[data-revista]").first().locator("td.coluna-validado .status-ok")).toBeVisible();

  // 5. Limpa: descarta a cópia (o hash muda e o "Validado" cai).
  await page.goto(urlRevista);
  await page.check("#id_descartar__F1__fechamento");
  await page.click("input[name=_continue]");
  await expect(page.locator(".messagelist")).toContainText("Textos do F1 salvos: fechamento.");
  await expect(page.locator("#validacao")).not.toContainText("✓ Validado");
  expect(erros).toEqual([]);

  await liberarBloqueio(page);
});

test("painel: agrupado por parceiro, seleção por grupo", async ({ page }) => {
  const usuario = process.env.E2E_ADMIN_USUARIO;
  const senha = process.env.E2E_ADMIN_SENHA;
  test.skip(!usuario || !senha, "defina E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA");
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  await page.goto("/admin/login/?next=/painel/2026/");
  await page.fill("#id_username", usuario!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");

  await expect(page.locator(".painel-tarefa")).toHaveCount(0);  // sem o card "Próxima tarefa"
  const grupos = page.locator("#painel-corpo .painel-grupo");
  test.skip((await grupos.count()) < 2, "precisa de 2 parceiros com revista no ano (ver o preparo do U8)");
  await expect(grupos.first()).toContainText(/\d+ de \d+ revistas? completas?/);

  // Marcar o parceiro marca as revistas dele; a caixa "todas" fica indeterminada.
  const grupo = grupos.first().locator("input[data-grupo]");
  const id = (await grupo.getAttribute("data-grupo"))!;
  const dele = page.locator(`input[name=revista][data-de="${id}"]`);
  const n = await dele.count();
  await grupo.check();
  for (let i = 0; i < n; i++) await expect(dele.nth(i)).toBeChecked();
  await expect(page.locator("[data-selecionadas]")).toHaveText(`${n} selecionada(s)`);
  await expect(page.locator("[data-validar]")).toBeEnabled();
  expect(await page.locator("[data-todas]").evaluate((c: HTMLInputElement) => c.indeterminate)).toBe(true);
  await grupo.uncheck();
  await expect(page.locator("[data-selecionadas]")).toHaveText("Nenhuma selecionada");
  await expect(page.locator("[data-validar]")).toBeDisabled();

  // Coluna Revista fixa: rolar a tabela na horizontal (tela estreita) liga a sombra da borda.
  await page.setViewportSize({ width: 480, height: 800 });
  await page.locator(".painel-caixa").evaluate((c) => { c.scrollTop = 0; c.scrollLeft = 40; c.dispatchEvent(new Event("scroll")); });
  await expect(page.locator(".painel-caixa")).toHaveAttribute("data-rolou-x", "");
  expect(erros).toEqual([]);
});
