import type { RouteObject } from "react-router";
import { AbaPagina } from "./AbaPagina";
import { rotasAno } from "./ano/rotas";
import { ListaProjetos } from "./ListaProjetos";
import { ProjetoLayout } from "./ProjetoLayout";

/**
 * DONO: A6a. Lista de projetos e casca do projeto (abas, ações, bloqueio,
 * provedor de edição, aba Página). As telas de ano vêm de ./ano/rotas (A6b).
 */
export const rotasProjetos: RouteObject[] = [
  { path: "projetos", element: <ListaProjetos /> },
  {
    path: "projetos/:slug",
    element: <ProjetoLayout />,
    children: [{ index: true, element: <AbaPagina /> }, ...rotasAno],
  },
];
