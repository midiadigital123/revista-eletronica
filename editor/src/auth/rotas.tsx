import type { RouteObject } from "react-router";
import { Login } from "./Login";

/** Rotas públicas (fora do layout autenticado). */
export const rotasPublicas: RouteObject[] = [{ path: "/login", element: <Login /> }];
