import { useRef, type ReactNode, type RefObject } from "react";
import { XIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface DialogoProps {
  aberto: boolean;
  aoFechar: () => void;
  titulo: string;
  children: ReactNode;
  /** Botões do rodapé. */
  acoes?: ReactNode;
  /** Envio em curso: Esc, clique fora e o X não fecham. */
  bloqueado?: boolean;
  /** Para onde vai o foco ao fechar se quem abriu sumiu (ex.: item excluído). */
  focoAoFechar?: RefObject<HTMLElement | null>;
}

/** Diálogo modal (Radix): foco preso, Esc e clique fora chamam aoFechar. Nome acessível = título. */
export function Dialogo({
  aberto,
  aoFechar,
  titulo,
  children,
  acoes,
  bloqueado,
  focoAoFechar,
}: DialogoProps) {
  const segurar = (e: Event) => {
    if (bloqueado) e.preventDefault();
  };
  // Sem DialogTrigger, o Radix não sabe quem abriu: guardamos para devolver o foco.
  const origem = useRef<HTMLElement | null>(null);
  return (
    <Dialog open={aberto} onOpenChange={(aberto) => !aberto && !bloqueado && aoFechar()}>
      <DialogContent
        aria-describedby={undefined}
        showCloseButton={false}
        onEscapeKeyDown={segurar}
        onInteractOutside={segurar}
        onOpenAutoFocus={() => {
          origem.current = document.activeElement as HTMLElement | null;
        }}
        onCloseAutoFocus={(e) => {
          e.preventDefault();
          const alvo = origem.current?.isConnected ? origem.current : focoAoFechar?.current;
          alvo?.focus();
        }}
      >
        <DialogHeader className="pr-8">
          <DialogTitle>{titulo}</DialogTitle>
        </DialogHeader>
        <div>{children}</div>
        {acoes && <DialogFooter>{acoes}</DialogFooter>}
        {/* Fechar fica por último no DOM: o foco inicial cai no primeiro campo/ação. */}
        <DialogClose asChild>
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label="Fechar"
            disabled={bloqueado}
            className="absolute top-4 right-4"
          >
            <XIcon />
          </Button>
        </DialogClose>
      </DialogContent>
    </Dialog>
  );
}

interface ConfirmacaoProps {
  aberto: boolean;
  titulo: string;
  mensagem: ReactNode;
  rotuloConfirmar?: string;
  aoConfirmar: () => void;
  aoCancelar: () => void;
  /** Ação em curso: botões desabilitados e diálogo bloqueado. */
  pendente?: boolean;
  focoAoFechar?: RefObject<HTMLElement | null>;
}

/** Confirmação de ação destrutiva (excluir projeto, ano, descritor, usuário). Foco inicial em Cancelar. */
export function Confirmacao({
  aberto,
  titulo,
  mensagem,
  rotuloConfirmar = "Excluir",
  aoConfirmar,
  aoCancelar,
  pendente = false,
  focoAoFechar,
}: ConfirmacaoProps) {
  return (
    <Dialogo
      aberto={aberto}
      aoFechar={aoCancelar}
      titulo={titulo}
      bloqueado={pendente}
      focoAoFechar={focoAoFechar}
      acoes={
        <>
          <Button type="button" variant="outline" onClick={aoCancelar} disabled={pendente}>
            Cancelar
          </Button>
          <Button type="button" variant="destructive" onClick={aoConfirmar} disabled={pendente}>
            {pendente && <Spinner data-icon="inline-start" />}
            {rotuloConfirmar}
          </Button>
        </>
      }
    >
      <div className="text-muted-foreground">{mensagem}</div>
    </Dialogo>
  );
}
