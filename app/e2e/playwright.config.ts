import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  // Em série: painel, impresso e revista-textos gravam a mesma revista DEMONSTRAÇÃO com o mesmo
  // usuário, e a mesma pessoa em outra aba toma o bloqueio (D-191). ~25 s no total.
  workers: 1,
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8000" },
  // D-224: apaga os parceiros e templates "E2E …" que os specs deixam (limpar.ts → manage.py limpar_e2e).
  globalTeardown: "./limpar.ts",
  // U10d: todo spec roda em 1280×720 (o padrão) e em 1440×900, a largura da crítica do impeccable.
  projects: [
    { name: "chromium", use: { browserName: "chromium" } },
    { name: "desktop-1440", use: { browserName: "chromium", viewport: { width: 1440, height: 900 } } },
  ],
});
