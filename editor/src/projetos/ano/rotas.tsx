import type { RouteObject } from "react-router";
import { SemDescritor, TelaAno } from "./TelaAno";
import { TelaDescritor } from "./TelaDescritor";

/**
 * DONO: A6b. Filhas de /projetos/:slug (montadas por projetos/rotas.tsx).
 * ano/:ano é o layout (faixa/cortes + lista); o descritor aberto é a filha :codigo.
 */
export const rotasAno: RouteObject[] = [
  {
    path: "ano/:ano",
    element: <TelaAno />,
    children: [
      { index: true, element: <SemDescritor /> },
      { path: ":codigo", element: <TelaDescritor /> },
    ],
  },
];
