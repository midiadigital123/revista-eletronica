// Hierarquia do editor de matriz (U9): Configurações (popover com o intervalo mínimo, autosave),
// "+ Novo descritor" no topo da lista e "Excluir descritor" na zona de perigo do fim do painel.
// Preparo de painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e). Edita só cópias da Demonstração
// que o próprio teste cria (matrizPropria, D-225; a "E2E Excluir …" sai pela tela, E3, D-205);
// o Impresso (E2E_IMPRESSO_*) só confere que não vê o botão.
import { expect, test } from "@playwright/test";
import { alpinePronto, entrar, liberarBloqueio, matrizPropria } from "./helpers";

test("MEC: Configurações salva o intervalo sozinho; Novo descritor na lista; excluir pede o código", async ({ page }) => {
  await entrar(page, "/ui/matriz/2026/");
  await matrizPropria(page, "MEC"); // edita só a própria cópia da Demonstração (D-225)
  await page.locator('a[href*="/ui/matriz/mec/"]').first().click();
  await alpinePronto(page);
  // Lista: só a alça (≤ 1rem), encostada à esquerda da lista e colada no código; nenhum botão ↑↓.
  const item = page.locator("#lista-ordem > [data-id]").first();
  await expect(item.locator("[data-mover]")).toHaveCount(0);
  const [alca, codigo, linha] = await Promise.all([item.locator(".alca").boundingBox(), item.locator(".matriz-codigo").boundingBox(), page.locator("#lista-ordem").boundingBox()]);
  expect(alca!.width).toBeLessThanOrEqual(16);
  expect(alca!.x - linha!.x).toBeLessThanOrEqual(1);
  expect(codigo!.x - (alca!.x + alca!.width)).toBeLessThanOrEqual(14);

  const cabecalho = page.locator("header.pagina-cab");
  await expect(cabecalho.getByRole("button", { name: "Novo descritor" })).toHaveCount(0);
  await expect(cabecalho.locator("[data-status-salvo]")).toBeVisible();

  // Configurações: popover sob o botão, foco no campo; sai do campo e salva; Esc fecha e volta o foco.
  const config = cabecalho.getByRole("button", { name: "Configurações" });
  const campo = page.getByRole("spinbutton", { name: "Intervalo mínimo" });
  await expect(campo).toBeHidden();
  await config.click();
  await expect(campo).toBeFocused();
  const [b, p] = await Promise.all([config.boundingBox(), page.locator("#mec-config").boundingBox()]);
  expect(p!.y).toBeGreaterThanOrEqual(b!.y + b!.height);
  const original = await campo.inputValue();
  // Salva pelo autosave; se a revista da demo estiver validada (painel.spec), confirma o modal de impacto real.
  const salvar = async (valor: string) => {
    const intervalo = () => page.waitForResponse((r) => r.url().endsWith("/intervalo/"));
    const resposta = intervalo();
    await campo.fill(valor);
    await campo.press("Tab");
    const corpo = await (await resposta).json();
    if (corpo.impacto) {
      const confirmado = intervalo();
      await page.getByRole("button", { name: "Salvar o intervalo mínimo e tirar Validado" }).click();
      expect((await (await confirmado).json()).ok).toBe(true);
    } else expect(corpo.ok).toBe(true);
  };

  await salvar(String(Number(original || 25) + 5));
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às/)).toBeVisible();
  await campo.focus();
  await page.keyboard.press("Escape");
  await expect(campo).toBeHidden();
  await expect(config).toBeFocused();
  await page.reload();
  await alpinePronto(page);
  await config.click();
  await expect(campo).toHaveValue(String(Number(original || 25) + 5));
  await salvar(original);

  // Impacto (resposta simulada; o servidor é coberto em test_ui_matriz): o modal abre sobre o popover,
  // Esc volta o valor gravado e o foco ao campo, e o popover continua aberto.
  const html = `<dialog class="dialogo impacto" x-data="impacto" data-abrir-ao-carregar data-form="form-intervalo" data-campo="confirmar_impacto" aria-labelledby="t-e2e" @cancel.prevent="cancelar">
    <h2 id="t-e2e">Salvar o intervalo mínimo tira o “Validado” de 1 revista(s)</h2><ul class="impacto-lista"><li>E2E Revista</li></ul>
    <footer><button type="button" class="btn btn-outline" @click="cancelar" autofocus>Cancelar</button></footer></dialog>`;
  await page.route("**/intervalo/", (r) => r.fulfill({ json: { ok: false, impacto: { titulo: "Salvar", perdem: ["E2E Revista"], afetadas: 1, html } } }));
  await campo.fill("99");
  await campo.press("Tab");
  const modal = page.getByRole("dialog", { name: /tira o “Validado”/ });
  await expect(modal).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(modal).toHaveCount(0);
  await expect(campo).toHaveValue(original);
  await expect(campo).toBeFocused();
  await page.unroute("**/intervalo/");
  await page.keyboard.press("Escape");
  await expect(campo).toBeHidden();

  // "+ Novo descritor": botão outline no topo da lista, abre o diálogo.
  const lista = page.getByRole("navigation", { name: /^Descritores de/ });
  await lista.getByRole("button", { name: "Novo descritor" }).click();
  await expect(page.locator("#dlg-novo")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator("#dlg-novo")).toBeHidden();

  // Excluir: zona de perigo no fim do painel; a página seguinte exige o código.
  const zona = page.locator("#painel .zona-perigo");
  await expect(zona.getByRole("heading", { name: "Excluir descritor" })).toBeVisible();
  const caixa = await zona.boundingBox();
  const tarefas = await page.locator("#sec-tarefas").boundingBox();
  expect(caixa!.y).toBeGreaterThan(tarefas!.y);
  await zona.getByRole("link", { name: /^Excluir o descritor/ }).click();
  await expect(page.locator("[name=confirmacao]")).toBeVisible();
  await page.getByRole("link", { name: "Voltar sem excluir" }).first().click();
  await expect(page.locator("#form-descritor")).toBeVisible();
  await liberarBloqueio(page);
});

// E3 (D-205): "Excluir matriz…" na zona de perigo do fim da Matriz → página comum de exclusão. A Demonstração
// está em uso (os parceiros da demo apontam para ela) e não sai; a cópia que o próprio teste cria sai pelo nome.
test("Matriz: Excluir matriz… mostra o que impede na Demonstração e apaga a cópia sem uso", async ({ page }) => {
  await entrar(page, "/ui/matriz/2026/");
  await page.getByRole("link", { name: "Demonstração" }).first().click();
  const detalhe = page.url();
  const zona = page.locator(".zona-perigo");
  await expect(zona.getByRole("heading", { name: "Excluir matriz" })).toBeVisible();
  const [caixa, tabela] = await Promise.all([zona.boundingBox(), page.locator(".matriz-tabela").boundingBox()]);
  expect(caixa!.y).toBeGreaterThan(tabela!.y + tabela!.height - 1); // no fim, não no topo
  const excluir = zona.getByRole("link", { name: "Excluir matriz…" });
  await expect(excluir).toHaveClass(/btn-destrutivo/);
  await excluir.focus();
  await expect(excluir).toBeFocused();
  await page.keyboard.press("Enter");

  await expect(page).toHaveURL(/\/ui\/excluir\/matriz\/\d+\/\?voltar=/);
  await expect(page.getByText("Não dá para excluir: isto está em uso.")).toBeVisible();
  const uso = page.getByRole("row", { name: /^Parceiros que usam a matriz/ });
  await expect(uso.getByRole("link").first()).toHaveAttribute("href", /\/lotes\//);
  await expect(page.getByRole("button", { name: "Excluir" })).toHaveCount(0);
  await page.getByRole("link", { name: "Voltar sem excluir" }).first().click();
  await expect(page).toHaveURL(/\/ui\/matriz\/2026\/$/);
  await expect(page.getByRole("link", { name: "Demonstração" }).first()).toBeVisible();

  // Cópia própria, sem parceiro: sai digitando o nome e volta à lista do ano.
  const nome = `E2E Excluir ${Date.now().toString(36).toUpperCase()}`;
  await page.goto(detalhe);
  await page.getByRole("button", { name: "Duplicar" }).click();
  const dialogo = page.locator("#dlg-duplicar");
  await dialogo.getByLabel("Ano da cópia").selectOption({ label: "2026" });
  await dialogo.getByLabel("Nome").fill(nome);
  await dialogo.getByRole("button", { name: "Duplicar" }).click();
  await expect(page.getByRole("heading", { level: 1, name: nome })).toBeVisible();
  await page.locator(".zona-perigo").getByRole("link", { name: "Excluir matriz…" }).click();
  await expect(page.getByText("Nada usa isto.")).toBeVisible();
  const enviar = page.getByRole("button", { name: "Excluir" });
  await expect(enviar).toBeDisabled();
  await page.getByLabel("Para confirmar, digite").fill(nome);
  await enviar.click();
  await expect(page).toHaveURL(/\/ui\/matriz\/2026\/$/);
  await expect(page.getByText(`Exclusão feita: a matriz ${nome} de 2026.`)).toBeVisible();
  await expect(page.getByRole("link", { name: nome })).toHaveCount(0);
});

test("Matriz: o Impresso não vê Excluir matriz…", async ({ browser }) => {
  const { E2E_IMPRESSO_USUARIO: imp, E2E_IMPRESSO_SENHA: senha } = process.env;
  test.skip(!imp || !senha, "defina E2E_IMPRESSO_*");
  const page = await (await browser.newContext()).newPage();
  await page.goto("/admin/login/?next=/ui/matriz/2026/");
  await page.fill("#id_username", imp!);
  await page.fill("#id_password", senha!);
  await page.click("input[type=submit]");
  await page.getByRole("link", { name: "Demonstração" }).first().click();
  await expect(page.getByText(/^Só leitura/)).toBeVisible();
  await expect(page.locator(".zona-perigo")).toHaveCount(0);
});
