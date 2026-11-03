// Seletor de ano do cabeçalho (U6): trocar de ano no painel filtrado cai na mesma tela, com o filtro.
// Precisa de dois anos: crie um ano vazio (ex.: 2025) depois do criar_demo 2026. Não use abrir_ano 2027:
// ele copia os descritores e o item.spec passa a achar dois "D01". Só lê.
import { expect, test } from "@playwright/test";
import { entrar, filtrarFalta } from "./helpers";

test("seletor de ano: troca no painel filtrado mantém a tela e o filtro", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  await entrar(page, "/painel/2026/");
  await filtrarFalta(page, "Validado"); // HTMX: a URL muda sem renderizar o cabeçalho (U8: contador no lugar do select)
  await expect(page).toHaveURL(/\/painel\/2026\/\?falta=validado(&|$)/);

  const nav = page.getByRole("navigation", { name: "Principal" }).getByRole("link");
  await expect(nav).toHaveText(["Painel", "Projetos", "Matrizes", "Templates", "Impresso"]);

  // Teclado: Enter abre, o foco vai ao ano atual, Esc fecha e o foco volta ao botão.
  const botao = page.getByRole("button", { name: /^Ano 2026/ });
  await botao.focus();
  await page.keyboard.press("Enter");
  const painel = page.locator("#seletor-ano");
  await expect(painel).toBeVisible();
  await expect(painel.locator('a[aria-current="page"]')).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(painel).toBeHidden();
  await expect(botao).toBeFocused();

  await botao.click();
  const outro = painel.locator("a[data-ano]:not([aria-current])").first();
  const ano = (await outro.textContent())!.trim();
  await outro.click();
  await expect(page).toHaveURL(new RegExp(`/painel/${ano}/\\?falta=validado(&|$)`));
  await expect(page.locator('#painel-corpo input[name="falta"]')).toHaveValue("validado"); // U8: a falta ativa vai num campo oculto
  await expect(page.getByRole("button", { name: new RegExp(`^Ano ${ano}`) })).toBeVisible();

  // O ano fica na sessão: a rota sem ano leva a ele.
  await page.goto("/ui/matriz/");
  await expect(page).toHaveURL(new RegExp(`/ui/matriz/${ano}/$`));
  expect(erros).toEqual([]);
});
