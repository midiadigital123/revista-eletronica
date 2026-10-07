import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, type ReactNode } from "react";
import { useForm, type FieldValues, type Path, type UseFormSetError } from "react-hook-form";
import { z } from "zod";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import { CriarUsuarioEntrada, Perfil, type Usuario } from "../contrato/schemas";
import { Aviso, Botao, CampoTexto, Dialogo } from "../ui";
import { usuariosApi } from "./api";

type Criar = z.infer<typeof CriarUsuarioEntrada>;

const SchemaEditar = z.object({
  nome: z.string().trim().min(1, "Informe o nome").max(120),
  perfil: Perfil,
  ativo: z.boolean(),
  senha: z.string().refine((s) => s === "" || s.length >= 8, "Mínimo de 8 caracteres"),
});
type Editar = z.infer<typeof SchemaEditar>;

function Perfis({ valor, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { valor?: never }) {
  void valor;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor="usuario-perfil" className="text-sm font-semibold">Perfil</label>
      <select id="usuario-perfil" className="h-10 rounded-md border border-linha bg-superficie px-3" {...props}>
        <option value="editor">Editor</option>
        <option value="admin">Administrador</option>
      </select>
    </div>
  );
}

/** Erro com `campo` conhecido vai para o campo; o resto vira Aviso. */
function useSalvar<T extends FieldValues, R>(
  fn: (d: T) => Promise<R>,
  setError: UseFormSetError<T>,
  campos: readonly string[],
  aoFechar: () => void,
) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: chaves.usuarios });
      aoFechar();
    },
    onError: (e) => {
      if (ehErroApi(e) && e.campo && campos.includes(e.campo)) setError(e.campo as Path<T>, { message: e.message });
    },
  });
}

const erroGeral = (e: unknown, campos: readonly string[]): ReactNode =>
  e instanceof Error && !(ehErroApi(e) && e.campo && campos.includes(e.campo)) ? <Aviso tom="erro">{e.message}</Aviso> : null;

const CAMPOS_CRIAR = ["email", "nome", "senha", "perfil"] as const;

export function FormCriar({ aberto, aoFechar }: { aberto: boolean; aoFechar: () => void }) {
  const { register, handleSubmit, setError, reset, formState: { errors } } = useForm<Criar>({
    resolver: zodResolver(CriarUsuarioEntrada),
    defaultValues: { email: "", nome: "", senha: "", perfil: "editor" },
  });
  const salvar = useSalvar((d: Criar) => usuariosApi.criar(d), setError, CAMPOS_CRIAR, aoFechar);
  useEffect(() => {
    if (aberto) {
      reset();
      salvar.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- só ao abrir
  }, [aberto, reset]);

  return (
    <Dialogo
      aberto={aberto}
      aoFechar={aoFechar}
      titulo="Novo usuário"
      acoes={
        <>
          <Botao onClick={aoFechar}>Cancelar</Botao>
          <Botao type="submit" form="form-criar-usuario" variante="primario" disabled={salvar.isPending}>Criar</Botao>
        </>
      }
    >
      <form id="form-criar-usuario" noValidate onSubmit={handleSubmit((d) => salvar.mutate(d))} className="flex flex-col gap-4">
        {erroGeral(salvar.error, CAMPOS_CRIAR)}
        <CampoTexto rotulo="E-mail" type="email" erro={errors.email?.message} {...register("email")} />
        <CampoTexto rotulo="Nome" erro={errors.nome?.message} {...register("nome")} />
        <CampoTexto rotulo="Senha" type="password" autoComplete="new-password" ajuda="Mínimo de 8 caracteres" erro={errors.senha?.message} {...register("senha")} />
        <Perfis {...register("perfil")} />
      </form>
    </Dialogo>
  );
}

const CAMPOS_EDITAR = ["nome", "perfil", "ativo", "senha"] as const;

export function FormEditar({ usuario, aoFechar }: { usuario: Usuario | null; aoFechar: () => void }) {
  const { register, handleSubmit, setError, reset, formState: { errors } } = useForm<Editar>({
    resolver: zodResolver(SchemaEditar),
    defaultValues: { nome: "", perfil: "editor", ativo: true, senha: "" },
  });
  const salvar = useSalvar(
    (d: Editar) => {
      const { senha, ...resto } = d;
      return usuariosApi.atualizar(usuario!.id, senha ? { ...resto, senha } : resto);
    },
    setError,
    CAMPOS_EDITAR,
    aoFechar,
  );
  useEffect(() => {
    if (usuario) {
      reset({ nome: usuario.nome, perfil: usuario.perfil, ativo: usuario.ativo, senha: "" });
      salvar.reset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- só ao trocar de usuário
  }, [usuario, reset]);

  return (
    <Dialogo
      aberto={usuario !== null}
      aoFechar={aoFechar}
      titulo={`Editar ${usuario?.nome ?? ""}`}
      acoes={
        <>
          <Botao onClick={aoFechar}>Cancelar</Botao>
          <Botao type="submit" form="form-editar-usuario" variante="primario" disabled={salvar.isPending}>Salvar</Botao>
        </>
      }
    >
      <form id="form-editar-usuario" noValidate onSubmit={handleSubmit((d) => salvar.mutate(d))} className="flex flex-col gap-4">
        {erroGeral(salvar.error, CAMPOS_EDITAR)}
        <p className="text-sm text-tinta-suave">{usuario?.email}</p>
        <CampoTexto rotulo="Nome" erro={errors.nome?.message} {...register("nome")} />
        <Perfis {...register("perfil")} />
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" className="size-4 accent-acento" {...register("ativo")} /> Ativo
        </label>
        <CampoTexto rotulo="Nova senha" type="password" autoComplete="new-password" ajuda="Deixe em branco para manter a atual" erro={errors.senha?.message} {...register("senha")} />
      </form>
    </Dialogo>
  );
}
