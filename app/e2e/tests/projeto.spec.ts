// Página do projeto com abas (U7b): Dados, Matriz, Cortes, Passos e cores, Revistas. Monta um parceiro
// "E2E Projeto <sufixo>" com cortes de LP (a cascata cria projeto e revista); os dados ficam no banco.
// A matriz salva ao escolher (autosave, sem revista validada não há modal) e a aba Cortes mostra só a
// linha do parceiro. Preparar como em painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e).
import { expect, test } from "@playwright/test";
import { entrar, liberarBloqueio, novoParceiro } from "./helpers";

test("projeto: abas, matriz salva ao escolher, cortes do parceiro e cartões das revistas", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const nome = `E2E Projeto ${Date.now().toString(36).toUpperCase()}`;

  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  await novoParceiro(page, nome);
  const salvou = page.waitForResponse((r) => r.url().includes("/celula/") && r.status() === 200);
  await page.getByLabel(`${nome} 5EF LP`, { exact: true }).fill("150, 200, 250, 300");
  await page.keyboard.press("Tab");
  await salvou;

  await page.goto("/ui/projeto/ano/2026/");
  await page.locator("tr", { has: page.getByLabel(`Marcar ${nome}`, { exact: true }) }).locator("a.link-linha").click();
  const abas = page.getByRole("navigation", { name: "Partes do projeto" });
  await expect(abas.getByRole("link", { name: "Dados" })).toHaveAttribute("aria-current", "page");
  await expect(page.locator("#id_nome")).toBeVisible();

  // Matriz: o select salva sozinho (campoAuto) e continua escolhido ao recarregar.
  await abas.getByRole("link", { name: "Matriz" }).click();
  await expect(page.locator("#id_nome")).toBeHidden();
  await page.getByLabel(`Matriz de ${nome} em 2026`).selectOption({ label: "Demonstração" });
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às \d/)).toBeVisible();
  await page.reload();
  await expect(page.locator("#pj-matriz option:checked")).toHaveText("Demonstração");

  // Cortes: só a linha deste parceiro, com o valor gravado.
  await abas.getByRole("link", { name: "Cortes" }).click();
  await expect(page.getByLabel(`${nome} 5EF LP`, { exact: true })).toHaveValue("150, 200, 250, 300");
  await expect(page.locator("#grade tbody tr[data-parceiro]")).toHaveCount(1);

  // Revistas: um cartão por componente, com o caminho para a página da revista.
  await abas.getByRole("link", { name: "Revistas" }).click();
  const cartao = page.locator(".pj-cartao", { hasText: "LP" });
  await expect(cartao).toContainText("Sem “Validado”");
  await expect(cartao.getByRole("link", { name: /^Abrir revista/ })).toBeVisible();
  await liberarBloqueio(page);
  expect(erros).toEqual([]);
});
