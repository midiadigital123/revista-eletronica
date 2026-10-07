import { useId, type ComponentProps, type ReactNode } from "react";
import { Field, FieldDescription, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface Base {
  rotulo: string;
  /** Mensagem de erro (do Zod ou do ErroApi.campo). */
  erro?: string;
  ajuda?: ReactNode;
}

function Moldura({
  id,
  rotulo,
  erro,
  ajuda,
  children,
}: Base & { id: string; children: ReactNode }) {
  return (
    <Field data-invalid={erro ? true : undefined}>
      <FieldLabel htmlFor={id}>{rotulo}</FieldLabel>
      {children}
      {ajuda && !erro && <FieldDescription id={`${id}-ajuda`}>{ajuda}</FieldDescription>}
      {erro && <FieldError id={`${id}-erro`}>{erro}</FieldError>}
    </Field>
  );
}

const descritoPor = (id: string, erro?: string, ajuda?: ReactNode) =>
  erro ? `${id}-erro` : ajuda ? `${id}-ajuda` : undefined;

/** Input com rótulo, ajuda e erro acessíveis. Compatível com register() do React Hook Form (ref é repassado). */
export function CampoTexto({ rotulo, erro, ajuda, id, ...props }: Base & ComponentProps<"input">) {
  const gerado = useId();
  const campoId = id ?? gerado;
  return (
    <Moldura id={campoId} rotulo={rotulo} erro={erro} ajuda={ajuda}>
      <Input
        id={campoId}
        aria-invalid={Boolean(erro)}
        aria-describedby={descritoPor(campoId, erro, ajuda)}
        {...props}
      />
    </Moldura>
  );
}

export function AreaTexto({
  rotulo,
  erro,
  ajuda,
  id,
  rows = 3,
  ...props
}: Base & ComponentProps<"textarea">) {
  const gerado = useId();
  const campoId = id ?? gerado;
  return (
    <Moldura id={campoId} rotulo={rotulo} erro={erro} ajuda={ajuda}>
      <Textarea
        id={campoId}
        rows={rows}
        aria-invalid={Boolean(erro)}
        aria-describedby={descritoPor(campoId, erro, ajuda)}
        {...props}
      />
    </Moldura>
  );
}
