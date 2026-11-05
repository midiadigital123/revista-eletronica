// Voltar e avançar numa página com bloqueio (D-222): ao sair, o pagehide libera o bloqueio; a página
// que o navegador restaura do bfcache recarrega e pega outro, em vez de mostrar "Você perdeu o bloqueio".
// O bfcache de verdade não acontece sob o Playwright (notRestoredReasons: "masked"), então o teste faz
// o que ele faz: libera o bloqueio (o pagehide) e dispara o pageshow com persisted.
import { expect, test } from "@playwright/test";
import { entrar, liberarBloqueio } from "./helpers";

test("revista: voltar e avançar (bfcache) recarrega com bloqueio novo e continua editável", async ({ page }) => {
  await entrar(page, "/ui/projeto/ano/2026/");
  const livre = page.locator('tbody:not(:has-text("Em edição")) tr[data-revista] a.link-linha');
  await page.goto((await livre.first().getAttribute("href"))!);
  const campo = page.locator("#bloqueio-sessao");
  const antes = await campo.inputValue();

  await liberarBloqueio(page);
  await Promise.all([
    page.waitForEvent("load"),
    page.evaluate(() => dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }))),
  ]);

  await expect(campo).not.toHaveValue(antes); // GET novo: outra sessão de bloqueio
  await page.waitForTimeout(1000); // a renovação antiga respondia 409 logo depois do pageshow
  await expect(page.getByText("perdeu o bloqueio")).toHaveCount(0);
  await liberarBloqueio(page);
});
