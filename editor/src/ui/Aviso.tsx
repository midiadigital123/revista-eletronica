import type { ReactNode } from "react";

type Tom = "info" | "alerta" | "erro";

const estilos: Record<Tom, string> = {
  info: "bg-acento-claro border-acento/30 text-tinta",
  alerta: "bg-alerta-claro border-alerta/30 text-tinta",
  erro: "bg-erro-claro border-erro/30 text-tinta",
};

/** Faixa de aviso (modo leitura, erros de carga, avisos da escala). */
export function Aviso({ tom = "info", children, acao }: { tom?: Tom; children: ReactNode; acao?: ReactNode }) {
  return (
    <div role={tom === "erro" ? "alert" : "status"} className={`flex items-center justify-between gap-4 rounded-md border px-4 py-3 text-sm ${estilos[tom]}`}>
      <div>{children}</div>
      {acao}
    </div>
  );
}
