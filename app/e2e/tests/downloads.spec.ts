// Downloads pela tela B (S8): as planilhas F1/F2 na ficha da revista (o gabarito de ids saiu com o SVG
// do F2, fase 3), a planilha de grupos na aba Cortes. Cada botão tem que baixar de verdade (evento
// download), sem passar pelo admin.
// Só lê: não grava nada. Preparo de painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e).
import { expect, test } from "@playwright/test";
import { entrar, revistaDemo } from "./helpers";

test("Revista: Baixar planilhas baixa pela tela B", async ({ page }) => {
  await entrar(page, "/ui/projeto/ano/2026/");
  const revista = await revistaDemo(page);
  await page.goto(`/ui/revista/2026/${revista}/`);

  const planilhas = page.getByRole("link", { name: "Baixar planilhas" });
  await expect(planilhas).toHaveAttribute("href", new RegExp(`/impresso/${revista}/planilhas/$`));
  const [zip] = await Promise.all([page.waitForEvent("download"), planilhas.click()]);
  expect(zip.suggestedFilename()).toMatch(/\.zip$/);
});

test("Cortes: Baixar planilha de grupos baixa o xlsx pela tela B", async ({ page }) => {
  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  const link = page.getByRole("link", { name: "Baixar planilha de grupos" });
  await expect(link).toHaveAttribute("href", "/cortes/2026/exportar/");
  const [planilha] = await Promise.all([page.waitForEvent("download"), link.click()]);
  expect(planilha.suggestedFilename()).toBe("cortes-2026.xlsx");
});
