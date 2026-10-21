import { QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { queryClient } from "../api/queryClient";
import { definicaoRotas } from "../rotas";

/** Renderiza o app inteiro numa rota, com os mocks MSW. Uso nos testes de tela. */
export function renderizarRota(caminho: string) {
  const router = createMemoryRouter(definicaoRotas, { initialEntries: [caminho] });
  return {
    router,
    ...render(
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <RouterProvider router={router} />
        </TooltipProvider>
      </QueryClientProvider>,
    ),
  };
}
