import { z } from "zod";

// Sem isso o Zod testa `new Function` e a CSP do nginx (sem 'unsafe-eval') registra violação no console.
z.config({ jitless: true });
