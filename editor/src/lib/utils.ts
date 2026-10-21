export { cn } from "cn";

/** Id aleatório. crypto.randomUUID só existe em contexto seguro (HTTPS/localhost); pela rede em http, usa getRandomValues. */
export function novoId(): string {
  // eslint-disable-next-line no-restricted-properties -- único ponto autorizado
  if (typeof crypto.randomUUID === "function") return crypto.randomUUID();
  return Array.from(crypto.getRandomValues(new Uint8Array(16)), (b) =>
    b.toString(16).padStart(2, "0"),
  ).join("");
}
