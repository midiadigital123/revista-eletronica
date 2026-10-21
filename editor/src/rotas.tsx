import { Navigate, createBrowserRouter, type RouteObject } from "react-router";
import { RotaProtegida } from "./auth/RotaProtegida";
import { rotasPublicas } from "./auth/rotas";
import { AppLayout } from "./layout/AppLayout";
import { rotasProjetos } from "./projetos/rotas";
import { rotasUsuarios } from "./usuarios/rotas";
import { NaoEncontrado } from "./ui/NaoEncontrado";

/**
 * Ponto único de registro das rotas. Cada módulo exporta as suas; os donos
 * editam o próprio rotas.tsx, não este arquivo.
 */
export const definicaoRotas: RouteObject[] = [
  ...rotasPublicas,
  {
    path: "/",
    element: (
      <RotaProtegida>
        <AppLayout />
      </RotaProtegida>
    ),
    children: [
      { index: true, element: <Navigate to="/projetos" replace /> },
      ...rotasProjetos,
      ...rotasUsuarios,
    ],
  },
  { path: "*", element: <NaoEncontrado /> },
];

export const criarRouter = () => createBrowserRouter(definicaoRotas);
