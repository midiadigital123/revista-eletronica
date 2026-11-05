// Impresso (S13): a pedagógica valida, o impresso vê o que mudou e clica "Revista Impressa Atualizada".
// Com o app no ar e o preparo de painel.spec.ts (criar_demo + superusuário), mais um usuário Impresso:
//   docker compose run --rm app python manage.py shell -c "from django.contrib.auth.models import Group; \
//     from django.contrib.auth import get_user_model; u = get_user_model().objects.create_user('imp-e2e', \
//     password='<senha>', is_staff=True); u.groups.add(Group.objects.get(name='Impresso'))"
//   cd app/e2e && E2E_BASE_URL=http://localhost:8014 E2E_ADMIN_USUARIO=e2e E2E_ADMIN_SENHA=<senha> \
//     E2E_IMPRESSO_USUARIO=imp-e2e E2E_IMPRESSO_SENHA=<senha> npx playwright test impresso
// Grava só na revista que o teste monta (revistaPropria: parceiro "E2E Impresso …", D-225): cópia do
// fechamento do F1, "Validado", foto do impresso e descarte. O limpar.ts apaga tudo no fim (D-224).
import { expect, test, type Browser, type Page } from "@playwright/test";
import { filtrarPainel, revistaPropria } from "./helpers";

const FECHAMENTO = "#id_secao__F1__fechamento";

async function entrar(browser: Browser, usuario: string, senha: string, destino: string, permissions: string[] = []) {
  const page = await (await browser.newContext({ permissions })).newPage();
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
  const { nome } = await revistaPropria(ped, "Impresso");
  await ped.goto("/painel/2026/");
  await filtrarPainel(ped, "#filtro-parceiro", { label: nome });
  await expect(ped).toHaveURL(/parceiro=/);
  const linha = ped.locator("#painel-corpo tbody tr[data-revista]").first();
  const urlPainel = ped.url();
  // O nome leva à revista B; o roteiro edita no admin (mesma revista).
  await ped.goto(`/admin/nucleo/revista/${await linha.getAttribute("data-revista")}/change/`);
  const urlRevista = ped.url();
  await ped.fill(FECHAMENTO, `Fechamento ${marca}.`);
  await ped.click("input[name=_continue]");
  await ped.click("#botao-validado");
  await expect(ped.locator(".messagelist")).toContainText("Revista validada.");
  await liberarBloqueio(ped);

  // 2. Impresso: entra pela coluna Impresso do painel e vê o fechamento novo.
  const page = await entrar(browser, imp!, impSenha!, urlPainel.replace(/^https?:\/\/[^/]+/, ""), ["clipboard-read", "clipboard-write"]);
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  await page.locator("#painel-corpo tbody tr[data-revista]").first().locator("td.coluna-impresso a").click();
  await expect(page.locator("h1")).toHaveText("Impresso");  // tela B: /ui/impresso/<ano>/?revista=
  const urlImpresso = page.url();
  const fechamento = page.locator("#grupo-F1-fechamento");
  // Sem tabela do HtmlDiff. "Copiar texto novo" leva o mesmo texto que a caixa mostra (na primeira entrega,
  // a seção inteira; depois de uma foto, só o trecho que mudou: o diff por palavra é conferido no passo 5).
  await expect(page.locator("table.diff")).toHaveCount(0);
  const novo = fechamento.getByRole("textbox");
  await expect(novo).toHaveValue(new RegExp(`(^|\\n)Fechamento ${marca}\\.$`));
  const copiar = fechamento.locator("[data-copiar^='#novo-']");  // o nome muda para "Copiado" depois do clique
  await expect(copiar).toHaveAccessibleName("Copiar texto novo");
  await copiar.click();
  await expect(copiar).toHaveText("Copiado");
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(await novo.inputValue());
  await expect(page.getByRole("link", { name: "Baixar planilhas" })).toBeVisible();

  // 3. Marca: os avisos zeram e o botão some.
  await page.click("#botao-impressa");
  await expect(page.locator("#mensagens")).toContainText("Revista Impressa Atualizada");
  await expect(page.locator("#conteudo")).toContainText("Sem mudanças desde a última");
  await expect(page.locator("#botao-impressa")).toHaveCount(0);
  await page.goto(urlPainel.replace(/^https?:\/\/[^/]+/, ""));
  await expect(page.locator("#painel-corpo tbody tr[data-revista]").first().locator("td.coluna-impresso .status-ok")).toBeVisible();
  expect(erros).toEqual([]);

  // 4. Limpa: descarta a cópia (o "Validado" cai; o impresso volta a ver o fechamento como mudança).
  await ped.goto(urlRevista);
  await ped.check("#id_descartar__F1__fechamento");
  await ped.click("input[name=_continue]");
  await expect(ped.locator(".messagelist")).toContainText("Textos do F1 salvos: fechamento.");
  await liberarBloqueio(ped);

  // 5. Diff contra a foto: por palavra, e o "Copiar texto novo" leva só o trecho (sem o título nem a marca);
  // "Copiar a seção inteira" leva o título junto.
  await page.goto(urlImpresso);
  await expect(fechamento.locator("del").filter({ hasText: marca })).toBeVisible();
  await expect(novo).not.toHaveValue(new RegExp(marca));
  const trecho = await novo.inputValue();
  await copiar.click();
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(trecho);
  await fechamento.getByRole("button", { name: "Copiar a seção inteira" }).click();
  const inteira = await page.evaluate(() => navigator.clipboard.readText());
  expect(inteira.endsWith(trecho) && inteira.length > trecho.length).toBe(true);
  expect(erros).toEqual([]);
});
