import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { z } from "zod";
import { App } from "./App";
import "./index.css";

// Sem isso o Zod testa `new Function` e a CSP do nginx (sem 'unsafe-eval') registra violação no console.
z.config({ jitless: true });

async function iniciar() {
  // Mocks só em desenvolvimento e só com VITE_MOCK=1 (npm run dev:mock).
  // Fica fora do bundle de produção: o import dinâmico é eliminado pelo Vite.
  if (import.meta.env.DEV && import.meta.env.VITE_MOCK === "1") {
    const { iniciarMocks } = await import("./mocks/browser");
    await iniciarMocks();
  }
  createRoot(document.getElementById("root")!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  );
}

void iniciar();
