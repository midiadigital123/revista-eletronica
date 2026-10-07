import { afterEach, expect, it, vi } from "vitest";
import { sessaoEdicao } from "./sessaoEdicao";

afterEach(() => {
  vi.unstubAllGlobals();
  sessionStorage.clear();
});

it("gera id sem crypto.randomUUID (http pela rede, contexto não seguro)", () => {
  const getRandomValues = globalThis.crypto.getRandomValues.bind(globalThis.crypto);
  vi.stubGlobal("crypto", { getRandomValues });
  const id = sessaoEdicao();
  expect(id).toMatch(/^[0-9a-f]{32}$/);
  expect(sessaoEdicao()).toBe(id);
});
