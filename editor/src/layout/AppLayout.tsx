import { useMutation, useQueryClient } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { authApi } from "../auth/api";
import { useUsuario } from "../auth/useUsuario";

const classeLink = ({ isActive }: { isActive: boolean }) =>
  cn(
    "rounded-md px-3 py-1.5 text-sm font-medium transition-colors duration-150 ease-saida outline-ring focus-visible:outline-2 focus-visible:outline-offset-2",
    isActive ? "bg-muted text-foreground" : "text-muted-foreground hover:text-foreground",
  );

/** Cabeçalho (sistema, navegação, usuário/sair) + conteúdo. Único contêiner de largura da área autenticada. */
export function AppLayout() {
  const { data: usuario } = useUsuario();
  const qc = useQueryClient();
  const navegar = useNavigate();
  const sair = useMutation({
    mutationFn: authApi.sair,
    // Mesmo se o logout falhar na rede, a sessão local é descartada.
    onSettled: () => {
      qc.clear();
      void navegar("/login", { replace: true });
    },
  });

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center gap-x-8 gap-y-2 px-6 py-3">
          <span className="font-semibold">Revista Eletrônica</span>
          <nav aria-label="Principal" className="flex gap-1">
            <NavLink to="/projetos" className={classeLink}>
              Projetos
            </NavLink>
            {usuario?.perfil === "admin" && (
              <NavLink to="/usuarios" className={classeLink}>
                Usuários
              </NavLink>
            )}
          </nav>
          <div className="ml-auto flex items-center gap-3">
            <span className="truncate text-sm text-muted-foreground">{usuario?.nome}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => sair.mutate()}
              disabled={sair.isPending}
            >
              Sair
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
