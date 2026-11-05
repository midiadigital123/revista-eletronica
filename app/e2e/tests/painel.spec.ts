// Painel da temporada e "Validado" (S12): abrir o painel, filtrar, validar uma revista própria (D-225).
// Com o app no ar. Preparar (idempotente), na raiz do repositório:
//   APP_PORT=8014 docker compose up -d db app
//   docker compose run --rm app python manage.py migrate
//   docker compose run --rm app python manage.py criar_demo --ano 2026   # só com DEBUG (padrão do compose)
//   docker compose run --rm -e DJANGO_SUPERUSER_PASSWORD=<senha> app \
//     python manage.py createsuperuser --noinput --username e2e --email e2e@exemplo.invalid
//   cd app/e2e && E2E_BASE_URL=http://localhost:8014 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> \
//     npx playwright test painel
// Grava só na revista que o teste monta (revistaPropria: parceiro "E2E Painel …", D-225): cópia do
// fechamento do F1, valida e descarta a cópia. O limpar.ts apaga tudo no fim (D-224).
import { expect, test, type Page } from "@playwright/test";
import { entrar, filtrarFalta, filtrarPainel, revistaPropria } from "./helpers";

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
  const { nome } = await revistaPropria(page, "Painel");
  await page.goto("/painel/2026/");

  // 1. Filtros: o parceiro próprio e o contador "Validado" (a revista nasce sem).
  // Painel B: o select e o contador trocam o corpo pelo HTMX e empurram a URL.
  await filtrarPainel(page, "#filtro-parceiro", { label: nome });
  await filtrarFalta(page, "Validado");
  await expect(page).toHaveURL(/falta=validado/);
  await expect(page.locator(".painel-contadores button[aria-pressed=true]")).toContainText("Validado");
  await expect(page.locator("#painel-corpo .painel-grupo")).toHaveCount(1);
  const linhas = page.locator("#painel-corpo tbody tr[data-revista]");
  await expect(linhas).toHaveCount(1);
  const linha = linhas.first();
  await expect(linha).toContainText(nome);
  await expect(linha.locator("td.coluna-validado .status-falta")).toBeVisible();
  const urlPainel = page.url();

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
  await page.locator(".painel-caixa").evaluate((c) => { c.scrollTop = 0; c.scrollLeft = 40; });
  await expect(page.locator(".painel-caixa")).toHaveAttribute("data-rolou-esq", "");
  expect(erros).toEqual([]);
});

test("painel: o contador ativo desliga o filtro de falta", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  await entrar(page, "/painel/2026/");
  const linhas = page.locator("#painel-corpo tbody tr[data-revista]");
  const total = await linhas.count();
  const contador = page.locator("#painel-corpo .painel-contadores button").first();
  test.skip(!(await contador.count()), "nenhuma coluna com falta no ano");
  const rotulo = (await contador.textContent())!.split(" sem ")[0].replace(/^\s*\d+/, "").trim();
  await expect(page.locator(".painel-limpar-tudo")).toHaveCount(0); // sem filtro, sem "Limpar filtros"

  await filtrarFalta(page, rotulo);
  await expect(page).toHaveURL(/falta=/);
  await expect(page.locator(".painel-contadores button[aria-pressed=true]")).toContainText(rotulo);
  await expect(page.locator(".painel-limpar-tudo")).toBeVisible();

  await filtrarFalta(page, rotulo); // de novo no mesmo contador: volta ao estado inicial
  await expect(page).not.toHaveURL(/falta=/);
  await expect(page.locator(".painel-contadores button[aria-pressed=true]")).toHaveCount(0);
  await expect(linhas).toHaveCount(total);
  await expect(page.locator(".painel-limpar-tudo")).toHaveCount(0);
  expect(erros).toEqual([]);
});

test("painel: 'usado por N' dos Templates abre o painel filtrado, e o filtro se mexe", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  await entrar(page, "/ui/templates/2026/");
  const usado = page.getByRole("link", { name: /^usado por \d+/ }).first();
  test.skip(!(await usado.count()), "nenhum template em uso no ano");
  const n = Number((await usado.textContent())!.match(/\d+/)![0]);
  await usado.click();

  await expect(page).toHaveURL(/\/painel\/2026\/\?template=\d+/);
  const pk = new URL(page.url()).searchParams.get("template")!;
  const template = page.locator("#filtro-template");
  await expect(template).toHaveValue(pk); // cai no select preenchido, não num chip
  const linhas = page.locator("#painel-corpo tbody tr[data-revista]");
  await expect(linhas).toHaveCount(n);
  await expect(page.locator(".painel-limpar-tudo")).toBeVisible();

  // Trocar o componente: o do template mantém as revistas; outro esvazia o recorte.
  const codigo = (await template.locator("option:checked").textContent())!.split(" · ")[0].trim();
  const outro = await page
    .locator("#filtro-componente option")
    .evaluateAll((os, c) => os.map((o) => o.textContent!.trim()).find((t) => t !== "Todos" && t !== c), codigo);
  await filtrarPainel(page, "#filtro-componente", { label: codigo });
  await expect(page).toHaveURL(new RegExp(`template=${pk}`));
  await expect(page).toHaveURL(/componente=\d+/);
  await expect(page.locator("#filtro-template")).toHaveValue(pk);
  await expect(linhas).toHaveCount(n);
  if (outro) {
    await filtrarPainel(page, "#filtro-componente", { label: outro });
    await expect(page.locator("#painel-corpo")).toContainText("Nenhuma revista com esse filtro");
  }

  // "Limpar filtros" volta à página sem filtro nenhum.
  await page.locator("#painel-corpo form.painel-filtros").evaluate((f) => f.setAttribute("data-velho", ""));
  await page.locator(".painel-limpar-tudo").click();
  await expect(page.locator("#painel-corpo form.painel-filtros:not([data-velho])")).toHaveCount(1);
  await expect(page).toHaveURL(/\/painel\/2026\/$/);
  await expect(page.locator("#filtro-template")).toHaveValue("");
  expect(erros).toEqual([]);
});
