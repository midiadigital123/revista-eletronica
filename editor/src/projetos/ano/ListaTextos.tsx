import { useState } from "react";
import { Botao } from "../../ui";
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
  rotuloItem: string;
  inicial: readonly string[];
  persistir: (lista: string[]) => Promise<unknown>;
}) {
  const { rotulo, rotuloItem } = props;
  const campo = useAutoSalvar<Item[]>(
    props.inicial.map((texto) => ({ id: crypto.randomUUID(), texto })),
    (itens) => props.persistir(textos(itens)),
    (itens) => JSON.stringify(textos(itens)),
  );
  const [novoId, setNovoId] = useState<string>();
  const itens = campo.valor;

  const mudar = (id: string, texto: string) =>
    campo.setValor(itens.map((i) => (i.id === id ? { ...i, texto } : i)));

  function adicionar() {
    const id = crypto.randomUUID();
    setNovoId(id);
    campo.setValor([...itens, { id, texto: "" }]);
  }

  function remover(id: string) {
    const restantes = itens.filter((i) => i.id !== id);
    campo.setValor(restantes);
    void campo.confirmar(restantes);
  }

  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-sm font-semibold text-tinta">{rotulo}</legend>
      {itens.length === 0 && <p className="text-sm text-tinta-suave">Nenhum item.</p>}
      <ol className="flex flex-col gap-1.5">
        {itens.map((item, i) => (
          <li key={item.id} className="flex items-center gap-2">
            <span aria-hidden className="w-6 text-right font-mono text-xs text-tinta-suave">
              {i + 1}
            </span>
            <input
              aria-label={`${rotuloItem} ${i + 1}`}
              className="h-9 flex-1 rounded-md border border-linha bg-superficie px-3 text-sm disabled:bg-papel disabled:text-tinta-suave"
              value={item.texto}
              autoFocus={item.id === novoId}
              onChange={(e) => mudar(item.id, e.target.value)}
              onBlur={() => void campo.confirmar()}
            />
            <Botao
              tamanho="sm"
              variante="fantasma"
              aria-label={`Remover ${rotuloItem.toLowerCase()} ${i + 1}`}
              onClick={() => remover(item.id)}
            >
              ×
            </Botao>
          </li>
        ))}
      </ol>
      <div className="flex items-center gap-3">
        <Botao tamanho="sm" onClick={adicionar} aria-label={`Adicionar ${rotuloItem.toLowerCase()}`}>
          + item
        </Botao>
        {campo.erro && (
          <p role="alert" className="text-xs text-erro">
            {campo.erro}
          </p>
        )}
      </div>
    </fieldset>
  );
}
