// Impresso (S13): a pedagógica valida, o impresso vê o que mudou e clica "Revista Impressa Atualizada".
// Com o app no ar e o preparo de painel.spec.ts (criar_demo + superusuário), mais um usuário Impresso:
//   docker compose run --rm app python manage.py shell -c "from django.contrib.auth.models import Group; \
//     from django.contrib.auth import get_user_model; u = get_user_model().objects.create_user('imp-e2e', \
//     password='<senha>', is_staff=True); u.groups.add(Group.objects.get(name='Impresso'))"
//   cd app/e2e && E2E_BASE_URL=http://localhost:8014 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> \
//     E2E_IMPRESSO_USUARIO=imp-e2e E2E_IMPRESSO_SENHA=<senha> npx playwright test impresso
// Grava de verdade: cópia do fechamento do F1 com uma marca nova, "Validado", foto do impresso; no fim
// descarta a cópia (a revista volta ao texto do template, sem "Validado").
import { expect, test, type Browser, type Page } from "@playwright/test";
import { filtrarPainel } from "./helpers";

const FECHAMENTO = "#id_secao__F1__fechamento";

async function entrar(browser: Browser, usuario: string, senha: string, destino: string) {
  const page = await (await browser.newContext()).newPage();
  await page.goto(`/admin/login/?next=${destino}`);
  await page.fill("#id_username", usuario);
  await page.fill("#id_password", senha);
  await page.click("input[type=submit]");
  return page;
}

async function liberarBloqueio(page: Page) {
  const campo = page.locator("#bloqueio-sessao");
  const form = {
    csrfmiddlewaretoken: await page.locator("[name=csrfmiddlewaretoken]").first().inputValue(),
    alvo: (await campo.getAttribute("data-alvo"))!,
    id: (await campo.getAttribute("data-id"))!,
    sessao: await campo.inputValue(),
  };
  expect((await page.request.post("/bloqueio/liberar", { form })).status()).toBe(204);
}

test("impresso: valida, vê o diff e marca impressa", async ({ browser }) => {
  const { E2E_ADMIN_USUARIO: adm, E2E_ADMIN_SENHA: admSenha, E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: impSenha } = process.env;
  test.skip(!adm || !admSenha || !imp || !impSenha, "defina E2E_ADMIN_* e E2E_IMPRESSO_*");
  const marca = `E2E ${Date.now()}`;

  // 1. Pedagógica: muda o fechamento (hash novo) e valida.
  const ped = await entrar(browser, adm!, admSenha!, "/painel/2026/");
  await filtrarPainel(ped, "#filtro-parceiro", { label: "DEMONSTRAÇÃO" });
  await expect(ped).toHaveURL(/parceiro=/);
  const linha = ped.locator("#painel-corpo tbody tr").first();
  const variaveis = linha.locator("td.coluna-variaveis a", { hasText: "falta" });
  const urlPainel = ped.url();
  if (await variaveis.count()) {
    await variaveis.click();  // ficha B do projeto
    await ped.fill("#id_nome", "DEMONSTRAÇÃO E2E");
    await ped.getByRole("button", { name: "Salvar projeto" }).click();
    await ped.goto(urlPainel);
  }
  // O nome leva à revista B; o roteiro edita no admin (mesma revista).
  await ped.goto(`/admin/nucleo/revista/${await linha.getAttribute("data-revista")}/change/`);
  const urlRevista = ped.url();
  await ped.fill(FECHAMENTO, `Fechamento ${marca}.`);
  await ped.click("input[name=_continue]");
  await ped.click("#botao-validado");
  await expect(ped.locator(".messagelist")).toContainText("Revista validada.");
  await liberarBloqueio(ped);

  // 2. Impresso: entra pela coluna Impresso do painel e vê o fechamento novo.
  const page = await entrar(browser, imp!, impSenha!, urlPainel.replace(/^https?:\/\/[^/]+/, ""));
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  await page.locator("#painel-corpo tbody tr").first().locator("td.coluna-impresso a").click();
  await expect(page.locator("h1")).toHaveText("Impresso");  // tela B: /ui/impresso/<ano>/?revista=
  const fechamento = page.locator("#grupo-F1-fechamento");
  await expect(fechamento.locator("textarea")).toHaveValue(new RegExp(`Fechamento ${marca}\\.`));
  await expect(page.getByRole("button", { name: "Copiar texto novo" }).first()).toBeVisible();
  await expect(page.getByRole("link", { name: "Baixar planilhas" })).toBeVisible();

  // 3. Marca: os avisos zeram e o botão some.
  await page.click("#botao-impressa");
  await expect(page.locator("#mensagens")).toContainText("Revista Impressa Atualizada");
  await expect(page.locator("#conteudo")).toContainText("Sem mudanças desde a última");
  await expect(page.locator("#botao-impressa")).toHaveCount(0);
  await page.goto(urlPainel.replace(/^https?:\/\/[^/]+/, ""));
  await expect(page.locator("#painel-corpo tbody tr").first().locator("td.coluna-impresso .status-ok")).toBeVisible();
  expect(erros).toEqual([]);

  // 4. Limpa: descarta a cópia (o "Validado" cai; o impresso volta a ver o fechamento como mudança).
  await ped.goto(urlRevista);
  await ped.check("#id_descartar__F1__fechamento");
  await ped.click("input[name=_continue]");
  await expect(ped.locator(".messagelist")).toContainText("Textos do F1 salvos: fechamento.");
  await liberarBloqueio(ped);
});
