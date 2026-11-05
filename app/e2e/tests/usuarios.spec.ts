// Usuários na tela B (S9): o administrador cria um usuário Mídias Digitais, gera o link de acesso e o desativa.
// Não há exclusão (D-205): cada execução deixa um usuário "e2e-midias-<sufixo>" inativo no banco.
// Rode só contra um banco descartável (E2E_ADMIN_*: o superusuário `e2e`, como nos outros specs). As regras do
// perfil Admin (não superusuário) estão nos testes Django (nucleo/tests/test_ui_usuarios.py).
import { expect, test } from "@playwright/test";
import { entrar } from "./helpers";

test("administrador cria um usuário Mídias Digitais e o desativa", async ({ page }) => {
  await entrar(page, "/ui/anos/");
  await page.getByRole("link", { name: "Usuários", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Usuários" })).toBeVisible();

  const nome = `e2e-midias-${Date.now().toString(36)}`;
  const senha = `Senha-${crypto.randomUUID()}`;
  await page.getByRole("link", { name: "Novo usuário" }).click();
  await page.getByLabel("Usuário", { exact: true }).fill(nome);
  await page.getByLabel("Primeiro nome").fill("Teste");
  await page.getByLabel("Grupo").selectOption({ label: "Mídias Digitais" });
  await page.getByLabel("Senha", { exact: true }).fill(senha);
  await page.getByLabel("Confirmação de senha").fill(senha);
  await page.getByRole("button", { name: "Criar usuário" }).click();

  await expect(page.getByText(`Usuário ${nome} criado no grupo Mídias Digitais.`)).toBeVisible();
  const linha = page.getByRole("row").filter({ has: page.getByRole("rowheader", { name: nome }) });
  await expect(linha.getByRole("combobox", { name: `Grupo de ${nome}` }).locator("option:checked")).toHaveText("Mídias Digitais");
  await expect(linha.getByText("Ativo")).toBeVisible();

  // Link de acesso: a página mostra o link de definir senha e a mensagem pronta para enviar.
  await linha.getByRole("button", { name: `Link de acesso de ${nome}` }).click();
  await expect(page.getByRole("heading", { level: 1, name: `Link de acesso de ${nome}` })).toBeVisible();
  await expect(page.getByLabel("Link", { exact: true })).toHaveValue(/\/conta\/senha\/[^/]+\/[^/]+\/$/);
  await expect(page.getByLabel("Mensagem pronta")).toHaveValue(new RegExp(`Usuário: ${nome}`));
  await page.getByRole("link", { name: "‹ Usuários" }).click();

  await linha.getByRole("button", { name: `Desativar ${nome}` }).click();
  await expect(page.getByText(`${nome} desativado: não entra mais.`)).toBeVisible();
  await expect(linha.getByText("Desativado")).toBeVisible();
  await expect(linha.getByRole("button", { name: `Ativar ${nome}` })).toBeVisible();
});
