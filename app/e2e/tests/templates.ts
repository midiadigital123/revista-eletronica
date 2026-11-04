// Template próprio dos specs (E4, D-207): quem grava em template cria o seu ("E2E …", LP de 2026) e, no
// fim, o exclui pela tela B. Sem revista, ele sai com as versões. Nenhum spec grava em template que não criou.
import { expect, type Page } from "@playwright/test";

/** Cria o template pelo admin e devolve o id. */
export async function criarTemplate(page: Page, nome: string, fasciculo: "F1" | "F2", texto: string) {
  await page.goto("/admin/nucleo/template/add/");
  await page.selectOption("#id_ano", { label: "2026" });
  const lp = page.locator("#id_componente option", { hasText: "LP" }).first();
  await page.selectOption("#id_componente", (await lp.getAttribute("value"))!);
  await page.selectOption("#id_fasciculo", fasciculo);
  await page.fill("#id_nome", nome);
  await page.fill("#id_texto", texto);
  await page.click("input[name=_save]");
  await expect(page.locator(".messagelist")).toBeVisible();
  await page.goto(`/admin/nucleo/template/?q=${encodeURIComponent(nome)}`);
  const href = await page.locator("#result_list tbody th a", { hasText: nome }).getAttribute("href");
  return href!.match(/template\/(\d+)\//)![1];
}

/** Exclui pela página de excluir: a que está aberta ou, fora dela, pelo "Excluir template…" da lista. */
export async function excluirTemplate(page: Page, nome: string, fasciculo: "F1" | "F2") {
  if (!page.url().includes("/ui/excluir/template/")) {
    await page.goto(`/ui/templates/2026/?aba=${fasciculo}`);
    await page.getByRole("link", { name: `Excluir template ${nome} (LP)…` }).click();
  }
  await expect(page.getByText("Nada usa isto.")).toBeVisible();
  await page.getByLabel("Para confirmar, digite").fill(nome);
  await page.getByRole("button", { name: "Excluir", exact: true }).click();
  await expect(page).toHaveURL(new RegExp(`/ui/templates/2026/\\?aba=${fasciculo}$`));
  await expect(page.getByText(`Exclusão feita: o template ${nome} (LP ${fasciculo}) de 2026.`)).toBeVisible();
  await expect(page.getByRole("link", { name: nome, exact: true })).toHaveCount(0);
}
