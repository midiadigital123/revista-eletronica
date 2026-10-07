import { setupWorker } from "msw/browser";
import { mockDb } from "./db";
import { handlers } from "./handlers";

export async function iniciarMocks() {
  // Em dev com mocks, já entra logado como admin (troque em /login).
  mockDb.sessaoUsuarioId = "000000000000000000000001";
  await setupWorker(...handlers).start({ onUnhandledRequest: "bypass", quiet: true });
}
