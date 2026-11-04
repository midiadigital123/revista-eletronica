// Página do projeto com abas (U7b): Dados, Matriz, Cortes, Passos e cores, Revistas. Monta um parceiro
// "E2E Projeto <sufixo>" com cortes de LP (a cascata cria projeto e revista); os dados ficam no banco.
// A matriz salva ao escolher (autosave, sem revista validada não há modal); a aba Cortes mostra só o
// parceiro, um bloco por etapa; Passos e cores sobrescreve e volta ao herdado (cor do ano, passo da
// matriz). Preparar como em painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e).
import { expect, test } from "@playwright/test";
import { alpinePronto, entrar, liberarBloqueio, novoParceiro } from "./helpers";

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
  await page.locator("tr", { has: page.getByLabel(`Marcar ${nome}`, { exact: true }) }).locator("a.painel-grupo-nome").click();
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

  // Cortes: só este parceiro, um bloco por etapa; o campo salva sozinho e fica ao recarregar.
  await abas.getByRole("link", { name: "Cortes" }).click();
  const corte = page.getByLabel(`${nome} 5EF LP`, { exact: true });
  await expect(corte).toHaveValue("150, 200, 250, 300");
  const rotulos = await page.locator("#grade input[name^='c-']").evaluateAll((es) => es.map((e) => e.getAttribute("aria-label")));
  expect(rotulos.length).toBeGreaterThan(0);
  expect(rotulos.every((r) => r?.startsWith(`${nome} `))).toBe(true);
  await expect(page.locator("#grade table")).toHaveCount(0);
  await alpinePronto(page);
  await corte.fill("150, 200, 250, 320");
  await page.keyboard.press("Tab");
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às \d/)).toBeVisible();
  await page.reload();
  await expect(page.getByLabel(`${nome} 5EF LP`, { exact: true })).toHaveValue("150, 200, 250, 320");

  // Passos e cores: a cor sobrescreve e volta à do ano; o passo sobrescreve, "sem linhas vazias"
  // é outra coisa, e "Voltar ao passo da matriz" limpa.
  await abas.getByRole("link", { name: "Passos e cores" }).click();
  await alpinePronto(page);
  const gravou = () => page.waitForResponse((r) => r.url().includes("/campo/") && r.status() === 200);
  const amostra = page.locator(".pj-amostra").nth(1);
  await expect(amostra.getByText("do ano", { exact: true })).toBeVisible();
  let ok = gravou();
  await amostra.locator("input[type=color]").fill("#123456");
  await ok;
  await expect(amostra.getByText("sobrescrita", { exact: true })).toBeVisible();
  await page.reload();
  await alpinePronto(page);
  await expect(amostra.locator("input[type=color]")).toHaveValue("#123456");
  ok = gravou();
  await amostra.getByRole("button", { name: /^Voltar à cor do ano/ }).click();
  await ok;
  await expect(amostra.getByText("do ano", { exact: true })).toBeVisible();
  await expect(amostra.getByRole("button", { name: /^Voltar à cor do ano/ })).toBeHidden();

  const celula = page.locator(".pj-celula").first();
  const passo = celula.locator("input[type=number]");
  await expect(celula.getByText("da matriz", { exact: true })).toBeVisible();
  ok = gravou();
  await passo.fill("30");
  await page.keyboard.press("Tab");
  await ok;
  await expect(celula.getByText("sobrescrito", { exact: true })).toBeVisible();
  ok = gravou();
  await celula.getByRole("checkbox", { name: /Sem linhas vazias/ }).check();
  await ok;
  await expect(passo).toBeDisabled();
  await page.reload();
  await alpinePronto(page);
  await expect(celula.getByRole("checkbox", { name: /Sem linhas vazias/ })).toBeChecked();
  await expect(celula.getByText("sobrescrito", { exact: true })).toBeVisible();
  ok = gravou();
  await celula.getByRole("button", { name: /^Voltar ao passo da matriz/ }).click();
  await ok;
  await expect(celula.getByText("da matriz", { exact: true })).toBeVisible();
  await expect(passo).toBeEnabled();
  await expect(passo).toHaveValue("");
  await page.reload();
  await alpinePronto(page);
  await expect(celula.getByRole("checkbox", { name: /Sem linhas vazias/ })).not.toBeChecked();

  // Revistas: um cartão por componente, com o caminho para a página da revista.
  await abas.getByRole("link", { name: "Revistas" }).click();
  const cartao = page.locator(".pj-cartao", { hasText: "LP" });
  await expect(cartao).toContainText("Sem “Validado”");
  await expect(cartao.getByRole("link", { name: /^Abrir revista/ })).toBeVisible();
  await liberarBloqueio(page);
  expect(erros).toEqual([]);
});
