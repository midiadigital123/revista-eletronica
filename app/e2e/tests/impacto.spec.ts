// Modal de impacto (U2) com o renomear inline (U5): renomear um parceiro com revista validada pede
// confirmação num modal que lista as revistas; Esc cancela, devolve o nome antigo e o foco ao campo;
// confirmar grava.
// Monta a própria revista (revistaPropria: parceiro "E2E Impacto <sufixo>" em 2026, pronta para validar),
// põe um fechamento com {{nome_parceiro}} e valida; o limpar.ts apaga no fim (D-224).
// Preparar como em painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e).
import { expect, test } from "@playwright/test";
import { entrar, liberarBloqueio, revistaPropria } from "./helpers";

test("renomear parceiro validado pela grade abre o modal; Esc volta o nome e o foco; confirmar grava", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));

  // 1. Revista própria pronta (revistaPropria); no admin, um fechamento com o nome do parceiro e o "Validado".
  await entrar(page);
  const { nome, revista } = await revistaPropria(page, "Impacto");
  const novo = `${nome} Novo`;
  await page.goto(`/admin/nucleo/revista/${revista}/change/`);
  // O nome do parceiro só entra no hash se algum texto usa a variável: o fechamento passa a usar.
  await page.fill("#id_secao__F1__fechamento", "Fechamento de {{nome_parceiro}}.");
  await page.click("input[name=_continue]");
  await expect(page.locator(".messagelist")).toContainText("Textos do F1 salvos: fechamento.");
  await page.click("#botao-validado");
  await expect(page.locator(".messagelist")).toContainText("Revista validada.");
  await liberarBloqueio(page);

  // 2. Renomear inline (U5): lápis → campo com foco; Enter salva pelo autosave, que abre o modal.
  await page.goto("/ui/projeto/ano/2026/cortes/");
  const linha = page.locator(`tr[data-parceiro="${nome}"]`);
  const campo = page.getByLabel(`Novo nome de ${nome}`);
  const modal = page.getByRole("dialog", { name: "Renomear tira o “Validado” de 1 revista(s)" });
  await linha.getByRole("button", { name: `Renomear ${nome}` }).click();
  await expect(campo).toBeFocused();
  await campo.fill(novo);
  await campo.press("Enter");
  await expect(modal).toBeVisible();
  await expect(modal.getByRole("listitem")).toContainText(nome);
  await expect(modal.getByRole("button", { name: "Cancelar" })).toBeFocused();

  // 3. Esc: fecha, o nome antigo volta e o foco vai ao campo. Nada gravou.
  await page.keyboard.press("Escape");
  await expect(modal).toBeHidden();
  await expect(campo).toHaveValue(nome);
  await expect(campo).toBeFocused();

  // 4. Sair do campo também salva; confirmar grava e o nome novo aparece na linha.
  await campo.fill(novo);
  await campo.press("Tab");
  await expect(modal).toBeVisible();
  await modal.getByRole("button", { name: "Renomear e tirar Validado" }).click();
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às \d/)).toBeVisible();
  await expect(linha.locator(".nome-inline-texto")).toHaveText(novo);
  await expect(campo).toBeHidden();
  await expect(linha.getByRole("button", { name: `Renomear ${novo}` })).toBeVisible();
  await page.reload();
  await expect(page.locator(`tr[data-parceiro="${novo}"]`)).toHaveCount(1);
  expect(erros).toEqual([]);
});
