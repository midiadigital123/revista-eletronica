import type { ComponentProps } from "react";
import { Button } from "@/components/ui/button";

type Variante = "primario" | "secundario" | "perigo" | "fantasma";

const variantes = {
  primario: "default",
  secundario: "outline",
  perigo: "destructive",
  fantasma: "ghost",
} as const satisfies Record<Variante, ComponentProps<typeof Button>["variant"]>;

export interface BotaoProps extends ComponentProps<"button"> {
  variante?: Variante;
  tamanho?: "md" | "sm";
}

/** Fachada em português sobre o Button do shadcn (type="button" por padrão). */
export function Botao({
  variante = "secundario",
  tamanho = "md",
  type = "button",
  ...props
}: BotaoProps) {
  return (
    <Button
      type={type}
      variant={variantes[variante]}
      size={tamanho === "sm" ? "sm" : "default"}
      {...props}
    />
  );
}
