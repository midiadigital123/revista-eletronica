import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import { LoginEntrada } from "../contrato/schemas";
import { Aviso, Botao, CampoTexto } from "../ui";
import { authApi } from "./api";
import { useUsuario } from "./useUsuario";

const destinoDe = (state: unknown): string => {
  const from = (state as { from?: unknown } | null)?.from;
  return typeof from === "string" && from.startsWith("/") && !from.startsWith("//") ? from : "/projetos";
};

export function Login() {
  const navegar = useNavigate();
  const local = useLocation();
  const qc = useQueryClient();
  const { data: logado } = useUsuario();
  const destino = destinoDe(local.state);

  const { register, handleSubmit, formState } = useForm<LoginEntrada>({
    resolver: zodResolver(LoginEntrada),
    defaultValues: { email: "", senha: "" },
  });
  const entrar = useMutation({
    mutationFn: authApi.entrar,
    onSuccess: (usuario) => {
      qc.setQueryData(chaves.eu, usuario);
      void navegar(destino, { replace: true });
    },
  });

  if (logado && !entrar.isPending && !entrar.isSuccess) return <Navigate to={destino} replace />;

  const erro = entrar.error;
  const mensagem = erro ? (ehErroApi(erro, 401) ? "E-mail ou senha incorretos." : erro.message) : null;

  return (
    <main className="grid min-h-screen place-items-center px-4">
      <form
        onSubmit={handleSubmit((d) => entrar.mutate(d))}
        noValidate
        className="flex w-full max-w-sm flex-col gap-5 rounded-lg border border-linha bg-superficie p-8 shadow-sm"
      >
        <header>
          <p className="text-xs font-semibold uppercase tracking-widest text-acento">Revista Eletrônica</p>
          <h1 className="mt-1 text-3xl">Entrar</h1>
        </header>
        {mensagem && <Aviso tom="erro">{mensagem}</Aviso>}
        <CampoTexto rotulo="E-mail" type="email" autoComplete="username" erro={formState.errors.email?.message} {...register("email")} />
        <CampoTexto rotulo="Senha" type="password" autoComplete="current-password" erro={formState.errors.senha?.message} {...register("senha")} />
        <Botao type="submit" variante="primario" disabled={entrar.isPending}>
          {entrar.isPending ? "Entrando…" : "Entrar"}
        </Botao>
      </form>
    </main>
  );
}
