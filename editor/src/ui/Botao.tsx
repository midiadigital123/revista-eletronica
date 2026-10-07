import type { ButtonHTMLAttributes } from "react";

type Variante = "primario" | "secundario" | "perigo" | "fantasma";

const estilos: Record<Variante, string> = {
  primario: "bg-acento text-white hover:bg-acento/90",
  secundario: "bg-superficie text-tinta border border-linha hover:bg-papel",
  perigo: "bg-erro text-white hover:bg-erro/90",
  fantasma: "text-tinta-suave hover:text-tinta hover:bg-linha/40",
};

export interface BotaoProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variante?: Variante;
  tamanho?: "md" | "sm";
}

export function Botao({ variante = "secundario", tamanho = "md", className = "", type = "button", ...props }: BotaoProps) {
  const medida = tamanho === "sm" ? "h-8 px-3 text-sm" : "h-10 px-4";
  return (
    <button
      type={type}
      className={`inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${medida} ${estilos[variante]} ${className}`}
      {...props}
    />
  );
}
