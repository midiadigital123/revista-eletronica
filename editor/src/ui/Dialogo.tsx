import { useEffect, useId, useRef, type ReactNode } from "react";

interface DialogoProps {
  aberto: boolean;
  aoFechar: () => void;
  titulo: string;
  children: ReactNode;
  /** Botões do rodapé. */
  acoes?: ReactNode;
}

/** Diálogo modal com <dialog> nativo (foco, Esc e backdrop do navegador). */
export function Dialogo({ aberto, aoFechar, titulo, children, acoes }: DialogoProps) {
  const ref = useRef<HTMLDialogElement>(null);
  const tituloId = useId();

  useEffect(() => {
    const dialogo = ref.current;
    if (!dialogo) return;
    if (aberto && !dialogo.open) dialogo.showModal?.();
    if (!aberto && dialogo.open) dialogo.close?.();
  }, [aberto]);

  return (
    <dialog
      ref={ref}
      onClose={aoFechar}
      aria-labelledby={tituloId}
      className="m-auto w-full max-w-lg rounded-lg border border-linha bg-superficie p-0 text-tinta shadow-xl backdrop:bg-tinta/40"
    >
      {aberto && (
        <div className="flex flex-col gap-4 p-6">
          <h2 id={tituloId} className="text-xl">
            {titulo}
          </h2>
          <div>{children}</div>
          {acoes && <div className="flex justify-end gap-2">{acoes}</div>}
        </div>
      )}
    </dialog>
  );
}

interface ConfirmacaoProps {
  aberto: boolean;
  titulo: string;
  mensagem: ReactNode;
  rotuloConfirmar?: string;
  aoConfirmar: () => void;
  aoCancelar: () => void;
}

/** Confirmação de ação destrutiva (excluir projeto, ano, descritor, usuário). */
export function Confirmacao({ aberto, titulo, mensagem, rotuloConfirmar = "Excluir", aoConfirmar, aoCancelar }: ConfirmacaoProps) {
  return (
    <Dialogo
      aberto={aberto}
      aoFechar={aoCancelar}
      titulo={titulo}
      acoes={
        <>
          <button type="button" onClick={aoCancelar} className="h-10 rounded-md border border-linha px-4">
            Cancelar
          </button>
          <button type="button" onClick={aoConfirmar} className="h-10 rounded-md bg-erro px-4 font-medium text-white">
            {rotuloConfirmar}
          </button>
        </>
      }
    >
      <p className="text-tinta-suave">{mensagem}</p>
    </Dialogo>
  );
}
