import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { ehErroApi } from "../api/client";
import { Aviso } from "../ui";
import { useUsuario } from "./useUsuario";

/** Sem sessão (401) → /login, guardando a origem em state.from. */
export function RotaProtegida({ children }: { children: ReactNode }) {
  const { data, error, isPending, refetch } = useUsuario();
  const local = useLocation();

  if (isPending)
    return (
      <div className="grid min-h-screen place-items-center">
        <Spinner aria-label="Carregando" className="size-6 text-muted-foreground" />
      </div>
    );
  if (ehErroApi(error, 401))
    return <Navigate to="/login" replace state={{ from: local.pathname + local.search }} />;
  if (!data)
    return (
      <div className="mx-auto max-w-xl p-8">
        <Aviso
          tom="erro"
          acao={
            <Button variant="outline" size="sm" onClick={() => void refetch()}>
              Tentar de novo
            </Button>
          }
        >
          Não foi possível verificar a sessão.
        </Aviso>
      </div>
    );
  return <>{children}</>;
}
