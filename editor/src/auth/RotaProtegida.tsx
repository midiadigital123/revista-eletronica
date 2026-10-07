import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { ehErroApi } from "../api/client";
import { Aviso } from "../ui";
import { useUsuario } from "./useUsuario";

/** Sem sessão (401) → /login, guardando a origem em state.from. */
export function RotaProtegida({ children }: { children: ReactNode }) {
  const { data, error, isPending, refetch } = useUsuario();
  const local = useLocation();

  if (isPending)
    return (
      <p role="status" className="p-8 text-sm text-tinta-suave">
        Carregando…
      </p>
    );
  if (ehErroApi(error, 401))
    return <Navigate to="/login" replace state={{ from: local.pathname + local.search }} />;
  if (!data)
    return (
      <div className="mx-auto max-w-xl p-8">
        <Aviso tom="erro" acao={<button className="underline" onClick={() => void refetch()}>Tentar de novo</button>}>
          Não foi possível verificar a sessão.
        </Aviso>
      </div>
    );
  return <>{children}</>;
}
