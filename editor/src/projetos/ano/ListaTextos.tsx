import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import { Plus, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { FieldLegend, FieldSet } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn, novoId as gerarId } from "@/lib/utils";
import { useAutoSalvar } from "./useAutoSalvar";

interface Item {
  id: string;
  texto: string;
}

const textos = (itens: readonly Item[]) => itens.map((i) => i.texto.trim()).filter(Boolean);

/**
 * Lista de textos (pré-requisitos, habilidades BNCC). A API substitui a lista
 * inteira: cada mudança envia todos os itens; itens vazios são descartados.
 */
export function ListaTextos(props: {
  rotulo: string;
  /** Só para leitores de tela, quando a seção já tem um título igual. */
  rotuloOculto?: boolean;
  rotuloItem: string;
  inicial: readonly string[];
  persistir: (lista: string[]) => Promise<unknown>;
}) {
  const { rotulo, rotuloItem } = props;
  const campo = useAutoSalvar<Item[]>(
    props.inicial.map((texto) => ({ id: gerarId(), texto })),
    (itens) => props.persistir(textos(itens)),
    (itens) => JSON.stringify(textos(itens)),
  );
  const [novoId, setNovoId] = useState<string>();
  const lista = useRef<HTMLOListElement>(null);
  const botaoAdicionar = useRef<HTMLButtonElement>(null);
  const itens = campo.valor;

  const mudar = (id: string, texto: string) =>
    campo.setValor(itens.map((i) => (i.id === id ? { ...i, texto } : i)));

  function adicionar() {
    const id = gerarId();
    setNovoId(id);
    campo.setValor([...itens, { id, texto: "" }]);
  }

  function remover(id: string) {
    const i = itens.findIndex((item) => item.id === id);
    const restantes = itens.filter((item) => item.id !== id);
    flushSync(() => campo.setValor(restantes));
    // O botão clicado sumiu: foco no item que ocupou o lugar, ou em "Adicionar".
    const proximo = lista.current?.querySelectorAll<HTMLElement>("input")[i];
    (proximo ?? botaoAdicionar.current)?.focus();
    void campo.confirmar(restantes);
  }

  return (
    <FieldSet className="gap-3">
      <FieldLegend variant="label" className={cn("mb-0", props.rotuloOculto && "sr-only")}>
        {rotulo}
      </FieldLegend>
      {itens.length === 0 && <p className="text-sm text-muted-foreground">Nenhum item.</p>}
      <ol ref={lista} className="flex flex-col gap-2">
        {itens.map((item, i) => {
          const rotuloRemover = `Remover ${rotuloItem.toLowerCase()} ${i + 1}`;
          return (
            <li
              key={item.id}
              className={cn("flex items-center gap-2", item.id === novoId && "animate-entra")}
            >
              <span
                aria-hidden
                className="w-6 shrink-0 text-right text-sm text-muted-foreground tabular-nums"
              >
                {i + 1}
              </span>
              <Input
                aria-label={`${rotuloItem} ${i + 1}`}
                className="flex-1"
                value={item.texto}
                autoFocus={item.id === novoId}
                onChange={(e) => mudar(item.id, e.target.value)}
                onBlur={() => void campo.confirmar()}
              />
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    size="icon"
                    variant="ghost"
                    aria-label={rotuloRemover}
                    onClick={() => remover(item.id)}
                  >
                    <X />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Remover e salvar a lista</TooltipContent>
              </Tooltip>
            </li>
          );
        })}
      </ol>
      <div className="flex items-center gap-3">
        <Button
          ref={botaoAdicionar}
          variant="outline"
          size="sm"
          onClick={adicionar}
          aria-label={`Adicionar ${rotuloItem.toLowerCase()}`}
        >
          <Plus data-icon="inline-start" />
          Adicionar {rotuloItem.toLowerCase()}
        </Button>
        {campo.erro && (
          <p role="alert" className="text-sm text-destructive">
            {campo.erro}
          </p>
        )}
      </div>
    </FieldSet>
  );
}
