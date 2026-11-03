// Hierarquia do editor de matriz (U9): Configurações (popover com o intervalo mínimo, autosave),
// "+ Novo descritor" no topo da lista e "Excluir descritor" na zona de perigo do fim do painel.
// Preparo de painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e). O intervalo volta ao valor
// original no fim; nada é excluído.
import { expect, test } from "@playwright/test";
import { alpinePronto, entrar, liberarBloqueio } from "./helpers";

test("MEC: Configurações salva o intervalo sozinho; Novo descritor na lista; excluir pede o código", async ({ page }) => {
  await entrar(page, "/ui/matriz/2026/");
  await page.getByRole("link", { name: "Demonstração" }).first().click();
  await page.locator('a[href*="/ui/matriz/mec/"]').first().click();
  await alpinePronto(page);
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
