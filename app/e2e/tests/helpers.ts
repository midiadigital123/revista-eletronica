import { expect, test, type Locator, type Page } from "@playwright/test";

/** Entra pelo login das telas B e cai em `proxima` (`/admin/login/` redireciona para `/conta/entrar/`, D-212). Sem E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA, pula o teste. */
export async function entrar(page: Page, proxima = "/admin/") {
  const usuario = process.env.E2E_ADMIN_USUARIO;
  const senha = process.env.E2E_ADMIN_SENHA;
  test.skip(!usuario || !senha, "defina E2E_ADMIN_USUARIO e E2E_ADMIN_SENHA");
  await page.goto(`/admin/login/?next=${encodeURIComponent(proxima)}`);
  await page.fill("#id_username", usuario!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await expect(page).not.toHaveURL(/\/admin\/login\//);
}

/** O Alpine já ligou a página (o `:data-estado` do status do autosave só existe depois do init).
 * Espera antes o DOMContentLoaded: ele só dispara depois dos scripts `defer`, e o Alpine e o Sortable vêm
 * do jsDelivr com o cache vazio a cada contexto novo. Sem essa espera, um CDN lento (> 5 s) estourava o
 * prazo do expect com a página ainda carregando (U10d, estados.spec). Alpine quebrado continua falhando. */
export async function alpinePronto(page: Page) {
  await page.waitForLoadState("domcontentloaded");
  await expect(page.locator("[data-status-salvo]")).toHaveAttribute("data-estado", "");
}

/** Cortes (U4): "+ Adicionar parceiro" abre a linha com o foco no nome; Enter cria e recarrega. */
export async function novoParceiro(page: Page, nome: string) {
  await alpinePronto(page);
  await page.getByRole("button", { name: "Adicionar parceiro" }).click();
  await expect(page.locator("#novo-parceiro")).toBeFocused();
  await page.keyboard.type(nome);
  await page.keyboard.press("Enter");
  await expect(page.locator(`tr[data-parceiro="${nome}"]`)).toHaveCount(1);
}

/** Parceiro "E2E …" com projeto e revista LP de 2026 (a cascata nasce do corte de 5EF LP). Para os specs que
 * gravam em projeto ou revista: nunca num dado que o teste não criou (D-225); o limpar.ts apaga no fim. */
export async function parceiroComProjeto(page: Page, prefixo: string, colunas = ["5EF LP"]) {
  const nome = `E2E ${prefixo} ${Date.now().toString(36).toUpperCase()}`;
  await page.goto("/ui/projeto/ano/2026/cortes/");
  await novoParceiro(page, nome);
  for (const coluna of colunas) {
    const salvou = page.waitForResponse((r) => r.url().includes("/celula/") && r.status() === 200);
    await page.getByLabel(`${nome} ${coluna}`, { exact: true }).fill("150, 200, 250, 300");
    await page.keyboard.press("Tab");
    await salvou;
  }
  return nome;
}

/** Cópia "E2E …" da matriz Demonstração em 2026 (botão Duplicar): para os specs que editam matriz (D-225).
 * Devolve o nome, a URL e o pk da matriz; o limpar.ts a apaga no fim. */
export async function matrizPropria(page: Page, prefixo: string) {
  const nome = `E2E ${prefixo} ${Date.now().toString(36).toUpperCase()}`;
  await page.goto("/ui/matriz/2026/");
  await page.getByRole("link", { name: "Demonstração" }).first().click();
  await page.getByRole("button", { name: "Duplicar" }).click();
  const dialogo = page.locator("#dlg-duplicar");
  await dialogo.getByLabel("Ano da cópia").selectOption({ label: "2026" });
  await dialogo.getByLabel("Nome").fill(nome);
  await dialogo.getByRole("button", { name: "Duplicar" }).click();
  await expect(page.getByRole("heading", { level: 1, name: nome })).toBeVisible();
  return { nome, url: page.url(), pk: /\/m\/(\d+)\//.exec(page.url())![1] };
}

export const CAPA = { name: "capa.png", mimeType: "image/png", buffer: Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mP4/5oBAATXAesdPD2pAAAAAElFTkSuQmCC", "base64") };

/** Revista LP 2026 própria e pronta para validar (6 de 6): parceiro "E2E …" com cortes de 5EF e 9EF LP,
 * `matriz` pelo lote, nome do projeto, templates Padrão, o infográfico Outras Etapas no mínimo
 * (`infograficoMinimo`) e capa. Para os specs que gravam em revista (D-225), no lugar da DEMONSTRAÇÃO.
 * Devolve o nome do parceiro e o id da revista. */
export async function revistaPropria(page: Page, prefixo: string, matriz = "Demonstração") {
  const { nome, revista } = await fichaComTemplates(page, prefixo, ["5EF LP", "9EF LP"], matriz);
  await infograficoMinimo(page, page.locator(".inf-card"));
  await page.setInputFiles("#arquivo-capa", CAPA);
  await expect(page.locator("#arquivos img.revista-capa")).toBeVisible();
  await expect(page.locator("#situacao")).toContainText("6 de 6 prontos");
  await liberarBloqueio(page);
  return { nome, revista };
}

/** Parceiro "E2E …" com cortes em `colunas`, `matriz` pelo lote e nome do projeto; termina na ficha da
 * revista LP com os templates Padrão do F1 e do F2 (sem infográfico nem capa). Devolve o nome e o id. */
export async function fichaComTemplates(page: Page, prefixo: string, colunas: string[], matriz = "Demonstração") {
  const nome = await parceiroComProjeto(page, prefixo, colunas);
  await atribuirEmMassa(page, nome, { matriz });
  await expect(page.locator("#mensagens")).toContainText("escolhida para 1 parceiro(s)");
  const revista = await revistaDaLista(page, nome, "LP");
  const salvo = page.locator("[data-status-salvo]").getByText(/Salvo às \d/);
  await page.getByRole("link", { name: nome }).first().click();
  await alpinePronto(page);
  await page.fill("#id_nome", `${nome} projeto`);
  await page.press("#id_nome", "Tab");
  await expect(salvo).toBeVisible();
  await liberarBloqueio(page);

  await page.goto(`/ui/revista/2026/${revista}/`);
  await alpinePronto(page);
  await page.selectOption("#template-F1", { label: "Padrão (F1)" });
  await expect(salvo).toBeVisible();
  await page.selectOption("#template-F2", { label: "Padrão (F2)" });
  await expect(page.locator("#textos textarea")).toBeVisible();
  return { nome, revista };
}

/** Ficha da revista: `acao` muda um campo do infográfico; espera a resposta do autosave e o "Salvo às"
 * (depois do 1º envio o "Salvo às" já está visível: só a resposta diz que este gravou). */
export async function salvarInfografico(page: Page, acao: () => Promise<unknown>) {
  const salvou = page.waitForResponse((r) => r.url().includes("acao=infografico") && r.status() === 200);
  await acao();
  await salvou;
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às \d/)).toBeVisible();
}

/** O mínimo para o `cartao` (.inf-card) não ter pendência: os 3 passos desligados e a habilidade. */
export async function infograficoMinimo(page: Page, cartao: Locator) {
  for (const passo of ["Habilidades", "Progressão", "Tarefas"]) {
    await salvarInfografico(page, () => cartao.getByLabel(passo, { exact: true }).uncheck());
  }
  await salvarInfografico(page, () => preencher(cartao.getByLabel("Habilidade destacada"), "Habilidade E2E."));
}

/** Preenche e sai do campo (Tab): o `change` do texto, que dispara o autosave. */
export async function preencher(campo: Locator, valor: string) {
  await campo.fill(valor);
  await campo.press("Tab");
}

/** Nome da regional do projeto `nome` na planilha de Variáveis (projeto novo: nome provisório "<parceiro> - NOME DO PROJETO"). */
export const regional = (page: Page, nome: string) =>
  page.getByLabel(`${nome} - NOME DO PROJETO Nome da regional`, { exact: true });

/** Painel B: roda `acao` e espera o HTMX trocar o corpo (o form velho é marcado e some na troca;
 * sem isso a próxima ação pode cair no corpo que está saindo). */
async function trocarCorpoPainel(page: Page, acao: () => Promise<unknown>) {
  await page.locator("#painel-corpo form.painel-filtros").evaluate((f) => f.setAttribute("data-velho", ""));
  await acao();
  await expect(page.locator("#painel-corpo form.painel-filtros:not([data-velho])")).toHaveCount(1);
}

/** Painel B: escolhe `valor` num select de filtro (#filtro-parceiro, -componente, -template, -matriz, -situacao). */
export async function filtrarPainel(page: Page, seletor: string, valor: string | { label: string }) {
  await trocarCorpoPainel(page, () => page.selectOption(seletor, valor));
}

/** Painel B: clica no contador da coluna (liga ou desliga o filtro de falta) ou, com null, em "Limpar filtro". */
export async function filtrarFalta(page: Page, coluna: string | null) {
  const alvo = coluna
    ? page.locator("#painel-corpo .painel-contadores button", { hasText: coluna })
    : page.locator("#painel-corpo .painel-limpar");
  await trocarCorpoPainel(page, () => alvo.click());
}

/** Mesmo POST do sendBeacon do pagehide: fechar o contexto não dispara o pagehide, e a
 * próxima execução abriria em somente leitura por até 30 s. */
export async function liberarBloqueio(page: Page) {
  const campo = page.locator("#bloqueio-sessao");
  const form = {
    csrfmiddlewaretoken: await page.locator("[name=csrfmiddlewaretoken]").first().inputValue(),
    alvo: (await campo.getAttribute("data-alvo"))!,
    id: (await campo.getAttribute("data-id"))!,
    sessao: await campo.inputValue(),
  };
  expect((await page.request.post("/bloqueio/liberar", { form })).status()).toBe(204);
}

/** Hub Projetos, aba Lista (U7a): marca o parceiro e roda "Atribuir matriz…" ou "Atribuir template…"
 * (o diálogo da barra de ações em massa). Escolhas pelo rótulo: { matriz } ou { componente, f1?, f2? }. */
export async function atribuirEmMassa(
  page: Page, parceiro: string, escolhas: { matriz: string } | { componente: string; f1?: string; f2?: string },
) {
  await page.goto("/ui/projeto/ano/2026/");
  await page.getByLabel(`Marcar ${parceiro}`, { exact: true }).check();
  const titulo = "matriz" in escolhas ? "Atribuir matriz" : "Atribuir template";
  await page.getByRole("button", { name: `${titulo}…` }).click();
  const dialogo = page.getByRole("dialog", { name: titulo });
  await expect(dialogo).toBeVisible();
  if ("matriz" in escolhas) {
    await dialogo.getByLabel("Matriz").selectOption({ label: escolhas.matriz });
  } else {
    await dialogo.getByLabel("Componente").selectOption({ label: escolhas.componente });
    if (escolhas.f1) await dialogo.getByLabel("Template F1").selectOption({ label: escolhas.f1 });
    if (escolhas.f2) await dialogo.getByLabel("Template F2").selectOption({ label: escolhas.f2 });
  }
  await dialogo.getByRole("button", { name: titulo, exact: true }).click();
}

/** A revista LP da demonstração (criar_demo), pela Lista de Projetos: a lista do admin pagina em 100 e,
 * com os projetos E2E que cada execução cria, a DEMONSTRAÇÃO cai na 2ª página (U10d). */
export async function revistaDemo(page: Page) {
  await page.goto("/ui/projeto/ano/2026/");
  return revistaDaLista(page, "DEMONSTRAÇÃO", "LP");
}

/** Lista de Projetos: o id da revista `codigo` (LP, MT) no grupo do parceiro (linha por revista). */
export async function revistaDaLista(page: Page, parceiro: string, codigo: string) {
  const grupo = page.locator("tbody", { has: page.getByLabel(`Marcar ${parceiro}`, { exact: true }) });
  const href = await grupo
    .locator("tr[data-revista]", { has: page.locator(".tag", { hasText: new RegExp(`^${codigo}$`) }) })
    .locator("a.link-linha")
    .getAttribute("href");
  return href!.split("/").at(-2)!;
}
