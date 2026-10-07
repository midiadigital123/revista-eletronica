import { useRef, useState } from "react";
import { flushSync } from "react-dom";
import {
  CONTEUDO_VAZIO,
  padraoDoNivel,
  type AnoProjeto,
  type Cortes,
  type LinhaEscala,
  type Padrao,
  type ScaleRange,
} from "../../contrato/schemas";
import { ehErroApi } from "../../api/client";
import { Info, Plus, X } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn, novoId } from "@/lib/utils";
import { Aviso } from "../../ui";
import { mensagemDeErro, rotuloPadrao } from "./dados";

/** Ordem da revista: Padrão 04 no topo. */
const ORDEM = ["padrao-4", "padrao-3", "padrao-2", "padrao-1"] as const;

/** Na revista, o nível da última linha dos padrões 2, 3 e 4 fica oculto (script.js: ocultarUltimoValor). */
const OCULTA_ULTIMO_NIVEL: ReadonlySet<Padrao> = new Set(["padrao-2", "padrao-3", "padrao-4"]);

/** Cor plena só no cabeçalho; o corpo fica em bg-background para manter o contraste dos campos. */
const FAIXA: Record<Padrao, string> = {
  "padrao-1": "bg-padrao-1",
  "padrao-2": "bg-padrao-2",
  "padrao-3": "bg-padrao-3",
  "padrao-4": "bg-padrao-4",
};

/** Intervalo do padrão segundo os cortes (mesma regra de padraoDoNivel). */
function intervalo(padrao: Padrao, faixa: ScaleRange, cortes: Cortes) {
  const inicio = {
    "padrao-1": faixa.min,
    "padrao-2": cortes["padrao-1"],
    "padrao-3": cortes["padrao-2"],
    "padrao-4": cortes["padrao-3"],
  }[padrao];
  const fim = {
    "padrao-1": cortes["padrao-1"],
    "padrao-2": cortes["padrao-2"],
    "padrao-3": cortes["padrao-3"],
    "padrao-4": faixa.max,
  }[padrao];
  return {
    inicio,
    texto: padrao === "padrao-4" ? `${inicio} ≤ nível ≤ ${fim}` : `${inicio} ≤ nível < ${fim}`,
  };
}

export type PersistirPadrao = (padrao: Padrao, linhas: LinhaEscala[]) => Promise<unknown>;

/** Escala do descritor: um bloco por padrão, cada mudança salva o padrão inteiro. */
export function EditorEscala(props: {
  ano: AnoProjeto;
  escala: Record<Padrao, LinhaEscala[]>;
  persistir: PersistirPadrao;
}) {
  return (
    <div className="flex flex-col gap-4">
      {ORDEM.map((p) => (
        <BlocoPadrao
          key={p}
          padrao={p}
          ano={props.ano}
          inicial={props.escala[p]}
          persistir={props.persistir}
        />
      ))}
    </div>
  );
}

interface Linha {
  id: string;
  level: string;
  content: string;
}

const nivel = (l: Linha) => (l.level.trim() === "" ? NaN : Number(l.level));
/** Ordem decrescente de nível (estável; inválidos no fim), como a API devolve. */
const ordenar = (ls: readonly Linha[]) =>
  [...ls].sort((a, b) =>
    Number.isNaN(nivel(b)) ? -1 : Number.isNaN(nivel(a)) ? 1 : nivel(b) - nivel(a),
  );
const paraApi = (ls: readonly Linha[]): LinhaEscala[] =>
  ls.map((l) => ({ level: nivel(l), content: l.content.trim() }));

function BlocoPadrao(props: {
  padrao: Padrao;
  ano: AnoProjeto;
  inicial: LinhaEscala[];
  persistir: PersistirPadrao;
}) {
  const { padrao, ano } = props;
  const rotulo = rotuloPadrao(padrao);
  const { inicio, texto } = intervalo(padrao, ano.scaleRange, ano.cortes);
  const [linhas, setLinhas] = useState<Linha[]>(() =>
    props.inicial.map((l) => ({
      id: novoId(),
      level: String(l.level),
      content: l.content === CONTEUDO_VAZIO ? "" : l.content,
    })),
  );
  const [erros, setErros] = useState<Record<string, string>>({});
  const [erroGeral, setErroGeral] = useState<string>();
  const [novaId, setNovaId] = useState<string>();
  const salvo = useRef(JSON.stringify(paraApi(ordenar(linhas))));
  const lista = useRef<HTMLOListElement>(null);
  const botaoAdicionar = useRef<HTMLButtonElement>(null);

  async function salvar(novas: Linha[]) {
    const vazias = novas.filter((l) => Number.isNaN(nivel(l)));
    if (vazias.length)
      return setErros(Object.fromEntries(vazias.map((l) => [l.id, "Informe o nível"])));

    const ordenadas = ordenar(novas);
    const corpo = paraApi(ordenadas);
    const json = JSON.stringify(corpo);
    if (json === salvo.current) return setErros({});
    const anterior = salvo.current;
    salvo.current = json;
    try {
      await props.persistir(padrao, corpo);
      setErros({});
      setErroGeral(undefined);
      setLinhas((atuais) => ordenar(atuais));
    } catch (e) {
      salvo.current = anterior;
      const porLinha: Record<string, string> = {};
      const sufixo = new RegExp(`scale\\.${padrao}\\.(\\d+)\\.level$`);
      if (ehErroApi(e, 400))
        for (const d of e.corpo.detalhes ?? []) {
          const id = ordenadas[Number(sufixo.exec(d.campo)?.[1])]?.id;
          if (id) porLinha[id] ??= d.erro;
        }
      setErros(porLinha);
      setErroGeral(Object.keys(porLinha).length ? undefined : mensagemDeErro(e));
    }
  }

  const mudar = (id: string, campo: "level" | "content", valor: string) =>
    setLinhas((ls) => ls.map((l) => (l.id === id ? { ...l, [campo]: valor } : l)));

  function adicionar() {
    const id = novoId();
    const novas = [...linhas, { id, level: String(inicio), content: "" }];
    setNovaId(id);
    setLinhas(novas);
    void salvar(novas);
  }

  function remover(id: string) {
    const i = linhas.findIndex((l) => l.id === id);
    const novas = linhas.filter((l) => l.id !== id);
    flushSync(() => setLinhas(novas));
    // O botão clicado sumiu: foco no nível da linha que ocupou o lugar, ou em "Adicionar linha".
    const proximo = lista.current?.querySelectorAll<HTMLElement>('input[type="number"]')[i];
    (proximo ?? botaoAdicionar.current)?.focus();
    void salvar(novas);
  }

  return (
    <section
      aria-labelledby={`titulo-${padrao}`}
      className="overflow-hidden rounded-lg border border-border bg-background"
    >
      <header
        className={cn(
          "flex items-baseline justify-between gap-3 px-4 py-2 text-foreground",
          FAIXA[padrao],
        )}
      >
        <h4 id={`titulo-${padrao}`} className="font-semibold">
          {rotulo}
        </h4>
        <span className="text-sm tabular-nums">{texto}</span>
      </header>

      <div className="flex flex-col gap-3 p-4">
        {linhas.length === 0 && <p className="text-sm text-muted-foreground">Sem linhas.</p>}
        <ol ref={lista} className="flex flex-col gap-3">
          {linhas.map((l, i) => {
            const n = i + 1;
            const valor = nivel(l);
            const pertence = Number.isNaN(valor) ? padrao : padraoDoNivel(valor, ano.cortes);
            const idErro = `erro-${l.id}`;
            const rotuloRemover = `Remover linha ${n} do ${rotulo}`;
            return (
              <li
                key={l.id}
                className={cn(
                  "grid grid-cols-[6rem_1fr_auto] items-start gap-2",
                  l.id === novaId && "animate-entra",
                )}
              >
                <Input
                  type="number"
                  aria-label={`Nível da linha ${n} do ${rotulo}`}
                  aria-invalid={Boolean(erros[l.id])}
                  aria-describedby={erros[l.id] ? idErro : undefined}
                  className="bg-background text-right text-base font-semibold tabular-nums"
                  value={l.level}
                  onChange={(e) => mudar(l.id, "level", e.target.value)}
                  onBlur={() => void salvar(linhas)}
                />
                <Textarea
                  aria-label={`Conteúdo da linha ${n} do ${rotulo}`}
                  placeholder="sem item"
                  rows={2}
                  className="min-h-9 bg-background"
                  value={l.content}
                  autoFocus={l.id === novaId}
                  onChange={(e) => mudar(l.id, "content", e.target.value)}
                  onBlur={() => void salvar(linhas)}
                />
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={rotuloRemover}
                      onClick={() => remover(l.id)}
                    >
                      <X />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>Remover e salvar o padrão</TooltipContent>
                </Tooltip>
                <div className="col-span-3 flex flex-col gap-2 empty:hidden">
                  {erros[l.id] && (
                    <p id={idErro} role="alert" className="text-sm text-destructive">
                      {erros[l.id]}
                    </p>
                  )}
                  {pertence !== padrao && (
                    <Aviso tom="alerta">
                      Nível {valor} pertence ao {rotuloPadrao(pertence)} pelos cortes do ano.
                    </Aviso>
                  )}
                  {OCULTA_ULTIMO_NIVEL.has(padrao) && i === linhas.length - 1 && (
                    <p
                      role="note"
                      className="flex items-center gap-1.5 text-sm text-muted-foreground"
                    >
                      <Info aria-hidden className="size-4 shrink-0" />O nível desta linha não
                      aparece na revista.
                    </p>
                  )}
                </div>
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
            aria-label={`Adicionar linha ao ${rotulo}`}
          >
            <Plus data-icon="inline-start" />
            Adicionar linha
          </Button>
          {erroGeral && (
            <p role="alert" className="text-sm text-destructive">
              {erroGeral}
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
