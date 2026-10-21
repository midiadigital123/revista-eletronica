import type { ReactNode } from "react";
import { CircleAlert, Info, TriangleAlert } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";

type Tom = "info" | "alerta" | "erro";

const icones = { info: Info, alerta: TriangleAlert, erro: CircleAlert } satisfies Record<
  Tom,
  unknown
>;

/** Faixa de aviso (modo leitura, erros de carga, avisos da escala). */
export function Aviso({
  tom = "info",
  children,
  acao,
  semRole,
}: {
  tom?: Tom;
  children: ReactNode;
  acao?: ReactNode;
  /** Dentro de uma região viva já montada (ex.: role="status" do pai). */
  semRole?: boolean;
}) {
  const Icone = icones[tom];
  return (
    <Alert
      role={semRole ? undefined : tom === "erro" ? "alert" : "status"}
      variant={tom === "erro" ? "destructive" : tom === "alerta" ? "warning" : "default"}
      className={acao ? "has-[>svg]:grid-cols-[auto_1fr_auto]" : undefined}
    >
      <Icone />
      <AlertDescription>{children}</AlertDescription>
      {acao && <div className="col-start-3 row-start-1 self-center">{acao}</div>}
    </Alert>
  );
}
