import { useRef, useState } from "react";
import { mensagemDeErro } from "./dados";

/**
 * Estado local de um campo que salva ao sair (blur). Inicializa uma vez (o
 * componente recebe key da entidade) e não se reseta quando o cache muda.
 * `confirmar` só persiste se o valor serializado mudou desde o último envio.
 */
export function useAutoSalvar<T>(
  inicial: T,
  persistir: (valor: T) => Promise<unknown>,
  serializar: (valor: T) => string = JSON.stringify,
) {
  const [valor, setValor] = useState(inicial);
  const [erro, setErro] = useState<string>();
  const salvo = useRef(serializar(inicial));

  async function confirmar(novo: T = valor) {
    const atual = serializar(novo);
    if (atual === salvo.current) return;
    const anterior = salvo.current;
    salvo.current = atual;
    try {
      await persistir(novo);
      setErro(undefined);
    } catch (e) {
      salvo.current = anterior;
      setErro(mensagemDeErro(e));
    }
  }

  return { valor, setValor, erro, confirmar };
}
