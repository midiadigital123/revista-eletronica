import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import { LoginEntrada } from "../contrato/schemas";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { FieldGroup } from "@/components/ui/field";
import { Spinner } from "@/components/ui/spinner";
import { useTituloPagina } from "../layout/useTituloPagina";
import { Aviso, CampoTexto } from "../ui";
import { authApi } from "./api";
import { useUsuario } from "./useUsuario";

const destinoDe = (state: unknown): string => {
  const from = (state as { from?: unknown } | null)?.from;
  return typeof from === "string" && from.startsWith("/") && !from.startsWith("//")
    ? from
    : "/projetos";
};

export function Login() {
  const navegar = useNavigate();
  const local = useLocation();
  const qc = useQueryClient();
  const { data: logado } = useUsuario();
  const destino = destinoDe(local.state);
  useTituloPagina("Entrar");

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
  const mensagem = erro
    ? ehErroApi(erro, 401)
      ? "E-mail ou senha incorretos."
      : erro.message
    : null;

  return (
    <main className="grid min-h-screen place-items-center bg-background px-4">
      <Card className="w-full max-w-sm">
        <form
          onSubmit={handleSubmit((d) => entrar.mutate(d))}
          noValidate
          className="flex flex-col gap-6"
        >
          <CardHeader>
            <CardTitle>
              <h1>Entrar</h1>
            </CardTitle>
            <CardDescription>Acesse o editor da Revista Eletrônica.</CardDescription>
          </CardHeader>
          <CardContent>
            <FieldGroup>
              {mensagem && <Aviso tom="erro">{mensagem}</Aviso>}
              <CampoTexto
                rotulo="E-mail"
                type="email"
                autoComplete="username"
                erro={formState.errors.email?.message}
                {...register("email")}
              />
              <CampoTexto
                rotulo="Senha"
                type="password"
                autoComplete="current-password"
                erro={formState.errors.senha?.message}
                {...register("senha")}
              />
            </FieldGroup>
          </CardContent>
          <CardFooter>
            <Button type="submit" className="w-full" disabled={entrar.isPending}>
              {entrar.isPending && <Spinner aria-hidden data-icon="inline-start" />}
              {entrar.isPending ? "Entrando…" : "Entrar"}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </main>
  );
}
