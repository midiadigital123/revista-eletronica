import { useEffect } from "react";

/**
 * Título da aba do navegador. Efeitos rodam do filho para o pai: só a rota mais
 * profunda deve passar um título; as de cima passam null quando têm filha ativa.
 */
export function useTituloPagina(titulo: string | null) {
  useEffect(() => {
    if (titulo) document.title = `${titulo} · Revista Eletrônica`;
  }, [titulo]);
}
