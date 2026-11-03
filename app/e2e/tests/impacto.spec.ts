// Modal de impacto (U2): renomear um parceiro com revista validada pede confirmação num modal que
// lista as revistas; Esc cancela, devolve o nome antigo e o foco ao campo; confirmar grava.
// Monta o próprio parceiro "E2E Impacto <sufixo>" no ano 2026 (cortes, matriz "Demonstração" e
// templates "Padrão" do criar_demo, SVG do F2, capa e um fechamento com {{nome_parceiro}}) e valida
// a revista; os dados ficam no banco.
// Preparar como em painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e).
import path from "node:path";
import { expect, test } from "@playwright/test";
import { entrar, liberarBloqueio } from "./helpers";

const SVG = path.join(__dirname, "../../nucleo/tests/fixtures/f2-lp.svg");
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mP4/5oBAATXAesdPD2pAAAAAElFTkSuQmCC", "base64");
const CORTES = "150, 200, 250, 300";

test("renomear parceiro validado abre o modal; Esc volta o nome e o foco; confirmar grava", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const nome = `E2E Impacto ${Date.now().toString(36).toUpperCase()}`;
  const novo = `${nome} Novo`;
  const mensagens = page.locator("#mensagens");

  // 1. Parceiro e cortes de LP: a cascata cria o projeto e a revista.
  await entrar(page, "/cortes/2026/");
  await page.fill("#novo-parceiro", nome);
  await page.getByRole("button", { name: "Adicionar parceiro" }).click();
  await page.getByLabel(`${nome} 5EF LP`, { exact: true }).fill(CORTES);
  await page.getByLabel(`${nome} 9EF LP`, { exact: true }).fill(CORTES);
  await page.getByRole("button", { name: "Salvar cortes" }).click();
  await expect(mensagens).toContainText("Cortes gravados (1 parceiro(s) alterado(s)).");

  // 2. Matriz e templates pelos lotes (antes de abrir o projeto: o lote pula projeto em edição).
  await page.goto("/ui/lotes/2026/matriz/");
  await page.getByLabel(nome, { exact: true }).check();
  await page.selectOption("#lote-matriz", { label: "Demonstração" });
  await page.getByRole("button", { name: "Aplicar aos selecionados" }).click();
  await expect(mensagens).toContainText("escolhida para 1 parceiro(s)");

  await page.goto("/ui/lotes/2026/template/");
  await page.locator("nav a", { hasText: /^LP$/ }).click();
  const alvo = page.getByLabel(nome);
  const revista = await alvo.getAttribute("value");
  await alvo.check();
  await page.selectOption("#lote-template_f1", { label: "Padrão" });
  await page.selectOption("#lote-template_f2", { label: "Padrão" });
  await page.getByRole("button", { name: "Aplicar aos selecionados" }).click();
  await expect(mensagens).toContainText("Template escolhido em 1 revista(s).");

  // 3. Nome do projeto (pendência), SVG e capa; depois o "Validado".
  await page.goto("/ui/projeto/ano/2026/");
  await page.getByRole("link", { name: nome }).first().click();
  await page.fill("#id_nome", `${nome} projeto`);
  await page.press("#id_nome", "Tab"); // U3: o campo salva sozinho ao sair dele
  await expect(page.locator("[data-status-salvo]")).toContainText("Salvo às");
  await liberarBloqueio(page);

  await page.goto(`/admin/nucleo/revista/${revista}/change/`);
  await page.setInputFiles("#id_arquivo_svg", SVG);
  await page.setInputFiles("#id_arquivo_capa", { name: "capa.png", mimeType: "image/png", buffer: PNG });
  // O nome do parceiro só entra no hash se algum texto usa a variável: o fechamento passa a usar.
  await page.fill("#id_secao__F1__fechamento", "Fechamento de {{nome_parceiro}}.");
  await page.click("input[name=_continue]");
  await expect(page.locator(".messagelist")).toContainText("Textos do F1 salvos: fechamento.");
  await page.click("#botao-validado");
  await expect(page.locator(".messagelist")).toContainText("Revista validada.");
  await liberarBloqueio(page);

  // 4. Renomear: o modal abre com a revista, o foco entra nele.
  await page.goto("/cortes/2026/");
  const linha = page.locator(`tr[data-parceiro="${nome}"]`);
  const campo = page.getByLabel(`Novo nome de ${nome}`);
  const modal = page.getByRole("dialog", { name: "Renomear tira o “Validado” de 1 revista(s)" });
  const renomear = async () => {
    await linha.locator("details").evaluate((d: HTMLDetailsElement) => { d.open = true; });
    await campo.fill(novo);
    await linha.locator("button", { hasText: "Renomear" }).click();
    await expect(modal).toBeVisible();
  };
  await renomear();
  await expect(modal.getByRole("listitem")).toContainText(nome);
  await expect(modal.getByRole("button", { name: "Cancelar" })).toBeFocused();

  // 5. Esc: fecha, o nome antigo volta e o foco vai ao campo. Nada gravou.
  await page.keyboard.press("Escape");
  await expect(modal).toBeHidden();
  await expect(campo).toHaveValue(nome);
  await expect(campo).toBeFocused();
  await expect(page.locator(`tr[data-parceiro="${nome}"]`)).toHaveCount(1);

  // 6. Confirmar grava e avisa quem perdeu o "Validado".
  await renomear();
  await modal.getByRole("button", { name: "Renomear e tirar Validado" }).click();
  await expect(mensagens).toContainText(`Parceiro renomeado para ${novo}. 1 revista(s) perderam o “Validado”.`);
  await expect(page.locator(`tr[data-parceiro="${novo}"]`)).toHaveCount(1);
  expect(erros).toEqual([]);
});
