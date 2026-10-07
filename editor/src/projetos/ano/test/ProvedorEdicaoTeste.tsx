import { QueryClientProvider, useQueryClient } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactNode } from "react";
import { Outlet, RouterProvider, createMemoryRouter, useParams } from "react-router";
import { TooltipProvider } from "@/components/ui/tooltip";
import { chaves } from "../../../api/chaves";
import { queryClient } from "../../../api/queryClient";
import type { Projeto } from "../../../contrato/schemas";
import { useProjeto } from "../../consultas";
import { EdicaoContext, type Edicao, type ModoEdicao } from "../../edicao";
import { BotaoNovoAno } from "../BotaoNovoAno";
import { rotasAno } from "../rotas";

/**
 * Provedor de edição mínimo para os testes do A6b (não depende do provedor do
 * A6a): `salvar` executa e aplica no cache (ou invalida), sem fila nem 423.
 */
export function ProvedorEdicaoTeste({ modo, children }: { modo: ModoEdicao; children: ReactNode }) {
  const slug = useParams().slug ?? "";
  const qc = useQueryClient();
  const edicao: Edicao = {
    slug,
    modo,
    bloqueio: null,
    salvamento: { status: "ocioso" },
    async salvar(op) {
      const resposta = await op.executar();
      const aplicar = op.aplicar;
      if (aplicar) qc.setQueryData<Projeto>(chaves.projeto(slug), (p) => p && aplicar(p, resposta));
      else await qc.invalidateQueries({ queryKey: chaves.projeto(slug) });
      return resposta;
    },
  };
  return <EdicaoContext value={edicao}>{children}</EdicaoContext>;
}

function BarraTeste() {
  const slug = useParams().slug ?? "";
  const { data } = useProjeto(slug);
  return data ? <BotaoNovoAno projeto={data} /> : null;
}

/** Renderiza as rotas do ano sob /projetos/:slug com o provedor de teste. */
export function renderizarAno(caminho: string, modo: ModoEdicao = "edicao") {
  const router = createMemoryRouter(
    [
      {
        path: "/projetos/:slug",
        element: (
          <ProvedorEdicaoTeste modo={modo}>
            <BarraTeste />
            <Outlet />
          </ProvedorEdicaoTeste>
        ),
        children: [{ index: true, element: <h1>Página do projeto</h1> }, ...rotasAno],
      },
    ],
    { initialEntries: [caminho] },
  );
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
