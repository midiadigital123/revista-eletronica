import type { RouteObject } from "react-router";
import { Usuarios } from "./Usuarios";

/** Gestão de usuários (só admin). */
export const rotasUsuarios: RouteObject[] = [{ path: "usuarios", element: <Usuarios /> }];
