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
import path from "node:path";
import { expect, test } from "@playwright/test";
import { alpinePronto, atribuirEmMassa, entrar, liberarBloqueio, novoParceiro, revistaDaLista } from "./helpers";

const INTRO = "#id_secao__F1__introducao";
const SVG = path.join(__dirname, "../../nucleo/tests/fixtures/f2-lp.svg");
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mP4/5oBAATXAesdPD2pAAAAAElFTkSuQmCC", "base64");

test("revista: cópia por seção, aviso com diff e descartar", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const marca = `E2E ${Date.now()}`;

  await entrar(page, "/admin/nucleo/revista/");
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

// U8b: página da revista em duas colunas. Monta um parceiro "E2E Revista <sufixo>" com cortes de LP
// (a cascata cria projeto e revista sem template), matriz pelo lote e nome do projeto; na revista:
// templates salvam ao escolher e liberam "Textos", o SVG vai pelo clique e a capa por soltar (miniatura
// + "Salvo às"), a Situação chega a 6 de 6 e "Validar revista" valida. Os dados ficam no banco.
test("revista: templates, arquivos por soltar e validar pela coluna Situação", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const nome = `E2E Revista ${Date.now().toString(36).toUpperCase()}`;
  const salvo = page.locator("[data-status-salvo]").getByText(/Salvo às \d/);

  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  await novoParceiro(page, nome);
  for (const coluna of ["5EF LP", "9EF LP"]) {
    const salvou = page.waitForResponse((r) => r.url().includes("/celula/") && r.status() === 200);
    await page.getByLabel(`${nome} ${coluna}`, { exact: true }).fill("150, 200, 250, 300");
    await page.keyboard.press("Tab");
    await salvou;
  }
  await atribuirEmMassa(page, nome, { matriz: "Demonstração" });
  await expect(page.locator("#mensagens")).toContainText("escolhida para 1 parceiro(s)");
  const revista = await revistaDaLista(page, nome, "LP");
  await page.goto("/ui/projeto/ano/2026/");
  await page.getByRole("link", { name: nome }).first().click();
  await page.fill("#id_nome", `${nome} projeto`);
  await page.press("#id_nome", "Tab");
  await expect(salvo).toBeVisible();
  await liberarBloqueio(page);

  await page.goto(`/ui/revista/2026/${revista}/`);
  const situacao = page.locator("#situacao");
  await expect(situacao).toContainText("2 de 6 prontos");
  await expect(situacao.getByRole("link", { name: "Falta escolher o template do F1." })).toHaveAttribute("href", "#templates");
  await expect(page.locator("#botao-validado")).toBeDisabled();
  await expect(page.locator("#validar-motivo")).toHaveText("Resolva as pendências acima para validar.");
  await expect(page.locator("#textos")).toContainText("Escolha os templates acima");

  // 1. Templates: salvam ao escolher; com os dois, "Textos" libera.
  await page.selectOption("#template-F1", { label: "Padrão (F1)" });
  await expect(salvo).toBeVisible();
  await page.selectOption("#template-F2", { label: "Padrão (F2)" });
  await expect(page.locator("#textos textarea")).toBeVisible();
  await expect(situacao).not.toContainText("Falta escolher o template");

  // 1b. Trocar o template de um fascículo com cópia de seção: o modal pede a frase (D-171); Esc volta o select.
  await page.locator("#textos textarea").fill("Texto E2E da revista.");
  await page.keyboard.press("Tab"); // salva sozinho ao sair do campo
  await expect(page.locator("#secoes")).toContainText("cópia");
  const padrao = await page.locator("#template-F1").inputValue();
  const modal = page.getByRole("dialog", { name: "Trocar o template do F1 apaga 1 cópia(s) de seção" });
  await page.selectOption("#template-F1", "");
  await expect(modal).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(modal).toBeHidden();
  await expect(page.locator("#template-F1")).toHaveValue(padrao);
  await page.selectOption("#template-F1", "");
  await modal.getByLabel(/Para confirmar/).fill("descartar 1 cópia");
  await modal.getByRole("button", { name: "Trocar o template do F1 e apagar cópias" }).click();
  await expect(page.locator("#textos")).toContainText("Escolha os templates acima");
  await page.selectOption("#template-F1", padrao);
  await expect(page.locator("#textos textarea")).toBeVisible();

  // 2. SVG pelo clique (input do rótulo) e capa por soltar: envia ao escolher e troca a parte de arquivos.
  await page.setInputFiles("#arquivo-svg", SVG);
  await expect(page.locator("#arquivos")).toContainText("SVG enviado");
  const transfer = await page.evaluateHandle((b64) => {
    const dt = new DataTransfer();
    const bytes = Uint8Array.from(atob(b64), (c) => c.charCodeAt(0));
    dt.items.add(new File([bytes], "capa.png", { type: "image/png" }));
    return dt;
  }, PNG.toString("base64"));
  await page.dispatchEvent("label[for=arquivo-capa]", "drop", { dataTransfer: transfer });
  await expect(page.locator("#arquivos img.revista-capa")).toBeVisible();
  await expect(salvo).toBeVisible();

  // 3. Sem pendência: "Validar revista" primário; validar mostra quem validou.
  await expect(situacao).toContainText("6 de 6 prontos");
  await page.locator("#botao-validado").click();
  await expect(page.locator("#situacao")).toContainText("Validada por");
  await liberarBloqueio(page);
  expect(erros).toEqual([]);
});

// Auditoria 03/11: o texto da seção salva sozinho ao sair do campo; sair da página e voltar mantém o
// texto. Com o cursor ainda no campo (sem o `change`), sair avisa. Termina descartando a cópia.
test("revista: o texto da seção salva sozinho e não se perde ao sair", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const marca = `E2E autosave ${Date.now().toString(36)}`;
  const status = page.locator("[data-status-salvo]");
  const salvo = status.getByText(/Salvo às \d/);

  await entrar(page, "/admin/nucleo/revista/");
  await page.locator("#result_list a", { hasText: "DEMONSTRAÇÃO" }).first().click();
  const pk = page.url().match(/revista\/(\d+)\//)![1];
  const url = `/ui/revista/2026/${pk}/`;
  await page.goto(url);
  await alpinePronto(page);
  const area = page.locator("#texto-secao");
  await expect(status).toContainText("Cada campo salva sozinho");

  // 1. Digitar e sair do campo: grava (com o modal, se a revista estava validada) e vira cópia.
  await area.fill(`Meu texto ${marca}.`);
  await page.keyboard.press("Tab");
  const modal = page.locator("dialog.impacto[open]");
  await expect(salvo.or(modal)).toBeVisible();
  if (await modal.isVisible()) await modal.getByRole("button", { name: /tirar Validado/ }).click();
  await expect(salvo).toBeVisible();
  await expect(page.locator(".revista-secao-cab .badge")).toHaveText("cópia desta revista");
  await expect(page.getByRole("button", { name: "Descartar cópia" })).toBeVisible();

  // 2. Sair pela volta ao projeto (sem aviso: está salvo) e voltar: o texto continua lá.
  const dialogos: string[] = [];
  const contar = (d: { type: () => string; dismiss: () => Promise<void> }) => { dialogos.push(d.type()); void d.dismiss(); };
  page.on("dialog", contar);
  await page.locator("a.voltar").click();
  await expect(page).toHaveURL(/\/ui\/projeto\/\d+\//);
  expect(dialogos).toEqual([]);
  page.off("dialog", contar);
  await page.goto(url);
  await expect(area).toHaveValue(`Meu texto ${marca}.`);

  // 3. Digitando, sem sair do campo: fechar a aba pede confirmação.
  await alpinePronto(page);
  await area.fill(`Ainda digitando ${marca}`);
  const dialogo = page.waitForEvent("dialog");
  await page.close({ runBeforeUnload: true });
  const d = await dialogo;
  expect(d.type()).toBe("beforeunload");
  await d.dismiss();
  expect(page.isClosed()).toBe(false);

  // 4. Descartar a cópia (botão com confirmação): volta ao texto do template.
  await area.fill(`Meu texto ${marca}.`);
  page.once("dialog", (x) => void x.accept());
  await page.getByRole("button", { name: "Descartar cópia" }).click();
  await expect(page.locator(".revista-secao-cab .badge")).toHaveText("texto do template");
  await expect(area).not.toHaveValue(new RegExp(marca));
  expect(erros).toEqual([]);
  await liberarBloqueio(page);
});
