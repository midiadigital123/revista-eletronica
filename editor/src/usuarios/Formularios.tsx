import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useId, type ReactNode, type Ref } from "react";
import {
  Controller,
  useForm,
  type FieldValues,
  type Path,
  type UseFormSetError,
} from "react-hook-form";
import { z } from "zod";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import { CriarUsuarioEntrada, Perfil, type Usuario } from "../contrato/schemas";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Field,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
} from "@/components/ui/field";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Spinner } from "@/components/ui/spinner";
import { Aviso, CampoTexto, Dialogo, useUltimo } from "../ui";
import { usuariosApi } from "./api";

type Criar = z.infer<typeof CriarUsuarioEntrada>;

const SchemaEditar = z.object({
  nome: z.string().trim().min(1, "Informe o nome").max(120),
  perfil: Perfil,
  ativo: z.boolean(),
  senha: z.string().refine((s) => s === "" || s.length >= 8, "Mínimo de 8 caracteres"),
});
type Editar = z.infer<typeof SchemaEditar>;

const PERFIS = [
  { valor: "editor", rotulo: "Editor" },
  { valor: "admin", rotulo: "Administrador" },
] as const;

type ValorPerfil = Criar["perfil"];

function Perfis({
  valor,
  aoMudar,
  aoSair,
  erro,
  ref,
}: {
  valor: ValorPerfil;
  aoMudar: (v: ValorPerfil) => void;
  aoSair: () => void;
  erro?: string;
  ref: Ref<HTMLDivElement>;
}) {
  const id = useId();
  return (
    <FieldSet data-invalid={erro ? true : undefined}>
      <FieldLegend id={`${id}-legenda`} variant="label">
        Perfil
      </FieldLegend>
      <RadioGroup
        ref={ref}
        value={valor}
        onValueChange={(v) => aoMudar(v as ValorPerfil)}
        onBlur={aoSair}
        aria-labelledby={`${id}-legenda`}
        aria-invalid={erro ? true : undefined}
        aria-describedby={erro ? `${id}-erro` : undefined}
        className="flex flex-wrap gap-4"
      >
        {PERFIS.map((p) => (
          <Field key={p.valor} orientation="horizontal" className="w-auto">
            <RadioGroupItem value={p.valor} id={`${id}-${p.valor}`} />
            <FieldLabel htmlFor={`${id}-${p.valor}`}>{p.rotulo}</FieldLabel>
          </Field>
        ))}
      </RadioGroup>
      {erro && <FieldError id={`${id}-erro`}>{erro}</FieldError>}
    </FieldSet>
  );
}

function Acoes({
  form,
  rotulo,
  pendente,
  aoFechar,
}: {
  form: string;
  rotulo: string;
  pendente: boolean;
  aoFechar: () => void;
}) {
  return (
    <>
      <Button type="button" variant="outline" onClick={aoFechar} disabled={pendente}>
        Cancelar
      </Button>
      <Button type="submit" form={form} disabled={pendente}>
        {pendente && <Spinner data-icon="inline-start" />}
        {rotulo}
      </Button>
    </>
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
      if (ehErroApi(e) && e.campo && campos.includes(e.campo))
        setError(e.campo as Path<T>, { message: e.message });
    },
  });
}

const erroGeral = (e: unknown, campos: readonly string[]): ReactNode =>
  e instanceof Error && !(ehErroApi(e) && e.campo && campos.includes(e.campo)) ? (
    <Aviso tom="erro">{e.message}</Aviso>
  ) : null;

const CAMPOS_CRIAR = ["email", "nome", "senha", "perfil"] as const;

export function FormCriar({ aberto, aoFechar }: { aberto: boolean; aoFechar: () => void }) {
  const {
    register,
    control,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<Criar>({
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
      bloqueado={salvar.isPending}
      acoes={
        <Acoes
          form="form-criar-usuario"
          rotulo="Criar"
          pendente={salvar.isPending}
          aoFechar={aoFechar}
        />
      }
    >
      <form id="form-criar-usuario" noValidate onSubmit={handleSubmit((d) => salvar.mutate(d))}>
        <FieldGroup>
          {erroGeral(salvar.error, CAMPOS_CRIAR)}
          <CampoTexto
            rotulo="E-mail"
            type="email"
            erro={errors.email?.message}
            {...register("email")}
          />
          <CampoTexto rotulo="Nome" erro={errors.nome?.message} {...register("nome")} />
          <CampoTexto
            rotulo="Senha"
            type="password"
            autoComplete="new-password"
            ajuda="Mínimo de 8 caracteres"
            erro={errors.senha?.message}
            {...register("senha")}
          />
          <Controller
            control={control}
            name="perfil"
            render={({ field }) => (
              <Perfis
                valor={field.value}
                aoMudar={field.onChange}
                aoSair={field.onBlur}
                ref={field.ref}
                erro={errors.perfil?.message}
              />
            )}
          />
        </FieldGroup>
      </form>
    </Dialogo>
  );
}

const CAMPOS_EDITAR = ["nome", "perfil", "ativo", "senha"] as const;

export function FormEditar({
  usuario,
  aoFechar,
}: {
  usuario: Usuario | null;
  aoFechar: () => void;
}) {
  const {
    register,
    control,
    handleSubmit,
    setError,
    reset,
    formState: { errors },
  } = useForm<Editar>({
    resolver: zodResolver(SchemaEditar),
    defaultValues: { nome: "", perfil: "editor", ativo: true, senha: "" },
  });
  // Conteúdo continua visível durante a animação de saída.
  const exibido = useUltimo(usuario);
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
      titulo={`Editar ${exibido?.nome ?? ""}`}
      bloqueado={salvar.isPending}
      acoes={
        <Acoes
          form="form-editar-usuario"
          rotulo="Salvar"
          pendente={salvar.isPending}
          aoFechar={aoFechar}
        />
      }
    >
      <form id="form-editar-usuario" noValidate onSubmit={handleSubmit((d) => salvar.mutate(d))}>
        <FieldGroup>
          {erroGeral(salvar.error, CAMPOS_EDITAR)}
          <p className="text-sm text-muted-foreground">{exibido?.email}</p>
          <CampoTexto rotulo="Nome" erro={errors.nome?.message} {...register("nome")} />
          <Controller
            control={control}
            name="perfil"
            render={({ field }) => (
              <Perfis
                valor={field.value}
                aoMudar={field.onChange}
                aoSair={field.onBlur}
                ref={field.ref}
                erro={errors.perfil?.message}
              />
            )}
          />
          <Controller
            control={control}
            name="ativo"
            render={({ field }) => (
              <Field data-invalid={errors.ativo ? true : undefined}>
                <Field orientation="horizontal">
                  <Checkbox
                    id="usuario-ativo"
                    name={field.name}
                    checked={field.value}
                    onCheckedChange={(v) => field.onChange(v === true)}
                    onBlur={field.onBlur}
                    ref={field.ref}
                    aria-invalid={errors.ativo ? true : undefined}
                    aria-describedby={errors.ativo ? "usuario-ativo-erro" : undefined}
                  />
                  <FieldLabel htmlFor="usuario-ativo">Ativo</FieldLabel>
                </Field>
                {errors.ativo && (
                  <FieldError id="usuario-ativo-erro">{errors.ativo.message}</FieldError>
                )}
              </Field>
            )}
          />
          <CampoTexto
            rotulo="Nova senha"
            type="password"
            autoComplete="new-password"
            ajuda="Deixe em branco para manter a atual"
            erro={errors.senha?.message}
            {...register("senha")}
          />
        </FieldGroup>
      </form>
    </Dialogo>
  );
}
