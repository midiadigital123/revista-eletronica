import { setupServer } from "msw/node";
import { handlers } from "./handlers";

/** Servidor MSW dos testes (Vitest/jsdom). Iniciado em src/test/setup.ts. */
export const servidorMock = setupServer(...handlers);
