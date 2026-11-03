// Modal de impacto (U2) com o renomear inline (U5): renomear um parceiro com revista validada pede
// confirmação num modal que lista as revistas; Esc cancela, devolve o nome antigo e o foco ao campo;
// confirmar grava.
// Monta o próprio parceiro "E2E Impacto <sufixo>" no ano 2026 (cortes, matriz "Demonstração" e
// templates "Padrão" do criar_demo, SVG do F2, capa e um fechamento com {{nome_parceiro}}) e valida
// a revista; os dados ficam no banco.
// Preparar como em painel.spec.ts (criar_demo --ano 2026 e o superusuário e2e).
import path from "node:path";
import { expect, test } from "@playwright/test";
import { alpinePronto, atribuirEmMassa, entrar, liberarBloqueio, novoParceiro, revistaDaLista } from "./helpers";

const SVG = path.join(__dirname, "../../nucleo/tests/fixtures/f2-lp.svg");
const PNG = Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR42mP4/5oBAATXAesdPD2pAAAAAElFTkSuQmCC", "base64");
const CORTES = "150, 200, 250, 300";

test("renomear parceiro validado pela grade abre o modal; Esc volta o nome e o foco; confirmar grava", async ({ page }) => {
  const erros: string[] = [];
  page.on("pageerror", (e) => erros.push(e.message));
  const nome = `E2E Impacto ${Date.now().toString(36).toUpperCase()}`;
  const novo = `${nome} Novo`;
  const mensagens = page.locator("#mensagens");

  // 1. Parceiro e cortes de LP: a cascata cria o projeto e a revista.
  await entrar(page, "/ui/projeto/ano/2026/cortes/");
  await novoParceiro(page, nome);
  // U3: cada célula salva sozinha ao sair dela.
  for (const coluna of ["5EF LP", "9EF LP"]) {
    const salvou = page.waitForResponse((r) => r.url().includes("/celula/") && r.status() === 200);
    await page.getByLabel(`${nome} ${coluna}`, { exact: true }).fill(CORTES);
    await page.keyboard.press("Tab");
    await salvou;
  }
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às/)).toBeVisible();

  // 2. Matriz e templates pela barra de ações em massa da Lista de Projetos (U7a; antes de abrir o
  // projeto: a ação em massa pula projeto em edição). O id da revista vem da linha LP do parceiro.
  await atribuirEmMassa(page, nome, { matriz: "Demonstração" });
  await expect(mensagens).toContainText("escolhida para 1 parceiro(s)");
  await atribuirEmMassa(page, nome, { componente: "LP · Língua Portuguesa", f1: "Padrão", f2: "Padrão" });
  await expect(mensagens).toContainText("Template escolhido em 1 revista(s).");
  const revista = await revistaDaLista(page, nome, "LP");

  // 3. Nome do projeto (pendência), SVG e capa; depois o "Validado".
  await page.goto("/ui/projeto/ano/2026/");
  await page.getByRole("link", { name: nome }).first().click();
  await alpinePronto(page);
  await page.fill("#id_nome", `${nome} projeto`);
  await page.press("#id_nome", "Tab"); // U3: o campo salva sozinho ao sair dele
  await expect(page.locator("[data-status-salvo]").getByText(/Salvo às \d/)).toBeVisible(); // o texto oculto (x-show) já existe: espera o visível
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

  // 4. Renomear inline (U5): lápis → campo com foco; Enter salva pelo autosave, que abre o modal.
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

  // 5. Esc: fecha, o nome antigo volta e o foco vai ao campo. Nada gravou.
  await page.keyboard.press("Escape");
  await expect(modal).toBeHidden();
  await expect(campo).toHaveValue(nome);
  await expect(campo).toBeFocused();

  // 6. Sair do campo também salva; confirmar grava e o nome novo aparece na linha.
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
