import { useMutation, useQueryClient } from "@tanstack/react-query";
import { NavLink, Outlet, useNavigate } from "react-router";
import { authApi } from "../auth/api";
import { useUsuario } from "../auth/useUsuario";
import { Botao } from "../ui";

const classeLink = ({ isActive }: { isActive: boolean }) =>
  `border-b-2 py-1 text-sm font-medium ${isActive ? "border-acento text-tinta" : "border-transparent text-tinta-suave hover:text-tinta"}`;

/** Cabeçalho (sistema, navegação, usuário/sair) + conteúdo. */
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
    <div className="min-h-screen bg-papel">
      <header className="border-b border-linha bg-superficie">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-8 gap-y-2 px-6 py-3">
          <span className="font-display text-xl font-semibold">Revista Eletrônica — Editor</span>
          <nav aria-label="Principal" className="flex gap-6">
            <NavLink to="/projetos" className={classeLink}>
              Projetos
            </NavLink>
            {usuario?.perfil === "admin" && (
              <NavLink to="/usuarios" className={classeLink}>
                Usuários
              </NavLink>
            )}
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="text-tinta-suave">{usuario?.nome}</span>
            <Botao tamanho="sm" onClick={() => sair.mutate()} disabled={sair.isPending}>
              Sair
            </Botao>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  );
}
