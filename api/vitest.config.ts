import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
    // Cada arquivo sobe seu próprio MongoDB em memória (test/helpers.ts).
    pool: "forks",
    testTimeout: 20_000,
    hookTimeout: 120_000,
  },
});
