import "@testing-library/jest-dom/vitest";
import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vitest";
import { queryClient } from "../api/queryClient";
import { resetarMockDb } from "../mocks/db";
import { servidorMock } from "../mocks/server";

// jsdom não implementa <dialog>.showModal/close; o primitivo ui/Dialogo depende deles.
beforeAll(() => {
  HTMLDialogElement.prototype.showModal ??= function (this: HTMLDialogElement) {
    this.setAttribute("open", "");
  };
  HTMLDialogElement.prototype.close ??= function (this: HTMLDialogElement) {
    this.removeAttribute("open");
    this.dispatchEvent(new Event("close"));
  };
  // jsdom não tem ResizeObserver; Checkbox/RadioGroup do Radix usam para medir o input oculto.
  globalThis.ResizeObserver ??= class {
    observe() {}
    unobserve() {}
    disconnect() {}
  };
  servidorMock.listen({ onUnhandledRequest: "error" });
});
afterEach(() => {
  cleanup();
  servidorMock.resetHandlers();
  queryClient.clear();
  resetarMockDb();
  sessionStorage.clear();
});
afterAll(() => servidorMock.close());
