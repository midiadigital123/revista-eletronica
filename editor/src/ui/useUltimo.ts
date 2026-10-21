import { useState } from "react";

/** Último valor não nulo: mantém o conteúdo do diálogo durante a animação de saída. */
export function useUltimo<T>(valor: T | null): T | null {
  const [ultimo, setUltimo] = useState(valor);
  if (valor !== null && valor !== ultimo) setUltimo(valor);
  return valor ?? ultimo;
}
