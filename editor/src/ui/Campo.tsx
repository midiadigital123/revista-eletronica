import { useId, type InputHTMLAttributes, type ReactNode, type TextareaHTMLAttributes } from "react";

interface Base {
  rotulo: string;
  /** Mensagem de erro (do Zod ou do ErroApi.campo). */
  erro?: string;
  ajuda?: ReactNode;
}

const classeControle =
  "w-full rounded-md border border-linha bg-superficie px-3 py-2 text-tinta placeholder:text-tinta-suave/70 disabled:bg-papel disabled:text-tinta-suave aria-[invalid=true]:border-erro";

function Moldura({ id, rotulo, erro, ajuda, children }: Base & { id: string; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id} className="text-sm font-semibold text-tinta">
        {rotulo}
      </label>
      {children}
      {ajuda && !erro && (
        <p id={`${id}-ajuda`} className="text-xs text-tinta-suave">
          {ajuda}
        </p>
      )}
      {erro && (
        <p id={`${id}-erro`} role="alert" className="text-xs text-erro">
          {erro}
        </p>
      )}
    </div>
  );
}

const descritoPor = (id: string, erro?: string, ajuda?: ReactNode) =>
  erro ? `${id}-erro` : ajuda ? `${id}-ajuda` : undefined;

/** Input com rótulo, ajuda e erro acessíveis. Compatível com register() do React Hook Form. */
export function CampoTexto({ rotulo, erro, ajuda, id, ref, className = "", ...props }: Base & InputHTMLAttributes<HTMLInputElement> & { ref?: React.Ref<HTMLInputElement> }) {
  const gerado = useId();
  const campoId = id ?? gerado;
  return (
    <Moldura id={campoId} rotulo={rotulo} erro={erro} ajuda={ajuda}>
      <input
        ref={ref}
        id={campoId}
        aria-invalid={Boolean(erro)}
        aria-describedby={descritoPor(campoId, erro, ajuda)}
        {...props}
        className={`${classeControle} h-10 ${className}`}
      />
    </Moldura>
  );
}

export function AreaTexto({ rotulo, erro, ajuda, id, ref, rows = 3, className = "", ...props }: Base & TextareaHTMLAttributes<HTMLTextAreaElement> & { ref?: React.Ref<HTMLTextAreaElement> }) {
  const gerado = useId();
  const campoId = id ?? gerado;
  return (
    <Moldura id={campoId} rotulo={rotulo} erro={erro} ajuda={ajuda}>
      <textarea
        ref={ref}
        id={campoId}
        rows={rows}
        aria-invalid={Boolean(erro)}
        aria-describedby={descritoPor(campoId, erro, ajuda)}
        {...props}
        className={`${classeControle} resize-y ${className}`}
      />
    </Moldura>
  );
}
