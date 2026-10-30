import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  // Em série: painel, impresso e revista-textos gravam a mesma revista DEMONSTRAÇÃO com o mesmo
  // usuário, e a mesma pessoa em outra aba toma o bloqueio (D-191). ~25 s no total.
  workers: 1,
  use: { baseURL: process.env.E2E_BASE_URL ?? "http://localhost:8000" },
  projects: [{ name: "chromium", use: { browserName: "chromium" } }],
});
