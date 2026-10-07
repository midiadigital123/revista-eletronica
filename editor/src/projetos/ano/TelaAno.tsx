import { useId, useState } from "react";
import { ChevronDown, MousePointerClick, SearchX } from "lucide-react";
import { Outlet, useNavigate } from "react-router";
import { Button } from "@/components/ui/button";
import {
  Empty,
  EmptyDescription,
  EmptyHeader,
  EmptyMedia,
  EmptyTitle,
} from "@/components/ui/empty";
import { FieldLegend } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useTituloPagina } from "../../layout/useTituloPagina";
import { rotuloAno, type AnoProjeto } from "../../contrato/schemas";
import { Aviso, Confirmacao } from "../../ui";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import { caminhoProjeto, mensagemDeErro, trocarAnos, useAnoAtual } from "./dados";
import { FaixaCortes } from "./FaixaCortes";
import { ListaDescritores } from "./ListaDescritores";

/** Aba de um ano: faixa e cortes, lista de descritores e o descritor aberto (Outlet). */
export function TelaAno() {
  const { consulta, projeto, anoProjeto, codigo } = useAnoAtual();
  // Com descritor aberto, o título vem da TelaDescritor.
  useTituloPagina(
    projeto && anoProjeto && !codigo ? `${rotuloAno(anoProjeto.ano)} · ${projeto.nome}` : null,
  );

  if (consulta.isPending) return <Carregando />;
  if (consulta.isError)
    return (
      <div className="flex flex-col gap-4">
        <h2 className="text-xl font-semibold tracking-tight">Não foi possível carregar o ano</h2>
        <Aviso tom="erro">{mensagemDeErro(consulta.error)}</Aviso>
      </div>
    );
  if (!projeto || !anoProjeto)
    return (
      <Empty>
        <EmptyHeader>
          <EmptyMedia variant="icon">
            <SearchX />
          </EmptyMedia>
          <EmptyTitle>
            <h2>Ano não encontrado</h2>
          </EmptyTitle>
          <EmptyDescription>Este ano não existe neste projeto.</EmptyDescription>
        </EmptyHeader>
      </Empty>
    );

  return (
    <section aria-labelledby="titulo-ano" className="flex flex-col gap-6">
      <header className="flex flex-col gap-5">
        <div className="flex items-start justify-between gap-4">
          <h2 id="titulo-ano" className="text-xl font-semibold tracking-tight">
            {rotuloAno(anoProjeto.ano)}
          </h2>
          <ExcluirAno ano={anoProjeto} unico={projeto.anos.length === 1} />
        </div>
        <FieldsetEdicao legenda="Faixa da escala e cortes dos padrões">
          <FaixaCortes key={anoProjeto.ano} ano={anoProjeto} />
        </FieldsetEdicao>
      </header>

      <div className="grid items-start gap-6 lg:grid-cols-[20rem_1fr]">
        <ListaRecolhivel ano={anoProjeto} codigo={codigo} />
        <div className="min-w-0">
          <Outlet />
        </div>
      </div>
    </section>
  );
}

/**
 * Abaixo de lg a lista (até 40 itens) empurra o formulário para baixo: com descritor aberto,
 * ela começa recolhida. Recolher é só CSS (`hidden lg:block`): a nav continua no DOM.
 */
function ListaRecolhivel({ ano, codigo }: { ano: AnoProjeto; codigo?: string }) {
  const id = useId();
  const [aberta, setAberta] = useState(!codigo);
  const [codigoAntes, setCodigoAntes] = useState(codigo);
  if (codigo !== codigoAntes) {
    setCodigoAntes(codigo);
    setAberta(!codigo);
  }
  return (
    <div className="flex min-w-0 flex-col gap-3 lg:sticky lg:top-4 lg:max-h-[calc(100dvh-2rem)] lg:overflow-y-auto">
      <Button
        type="button"
        variant="outline"
        className="justify-between lg:hidden"
        aria-expanded={aberta}
        aria-controls={id}
        onClick={() => setAberta((a) => !a)}
      >
        Descritores do {rotuloAno(ano.ano)} ({ano.descritores.length})
        <ChevronDown
          data-icon="inline-end"
          className={cn("transition-transform duration-150 ease-saida", aberta && "rotate-180")}
        />
      </Button>
      <div id={id} className={cn(!aberta && "hidden lg:block")}>
        <ListaDescritores ano={ano} codigoAtual={codigo} />
      </div>
    </div>
  );
}

function Carregando() {
  return (
    <div role="status" className="flex flex-col gap-6">
      <span className="sr-only">Carregando…</span>
      <Skeleton className="h-9 w-32" />
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {[1, 2, 3, 4].map((i) => (
          <Skeleton key={i} className="h-28" />
        ))}
      </div>
      <div className="grid gap-6 lg:grid-cols-[20rem_1fr]">
        <Skeleton className="h-96" />
        <Skeleton className="h-96" />
      </div>
    </div>
  );
}

/** Tela índice do ano, sem descritor selecionado. */
export function SemDescritor() {
  return (
    <Empty className="border">
      <EmptyHeader>
        <EmptyMedia variant="icon">
          <MousePointerClick />
        </EmptyMedia>
        <EmptyTitle>Escolha um descritor</EmptyTitle>
        <EmptyDescription>
          Selecione um na lista ou use “+ Descritor” para criar um novo.
        </EmptyDescription>
      </EmptyHeader>
    </Empty>
  );
}

/** <fieldset disabled> nativo: fora do modo edição, desabilita todos os controles de dentro. */
export function FieldsetEdicao({
  legenda,
  children,
}: {
  legenda: string;
  children: React.ReactNode;
}) {
  const { modo } = useEdicao();
  return (
    <fieldset disabled={modo !== "edicao"} className="min-w-0">
      <FieldLegend variant="label">{legenda}</FieldLegend>
      {children}
    </fieldset>
  );
}

function ExcluirAno({ ano, unico }: { ano: AnoProjeto; unico: boolean }) {
  const { slug, modo, salvar } = useEdicao();
  const navigate = useNavigate();
  const [confirmando, setConfirmando] = useState(false);
  const [erro, setErro] = useState<string>();
  const rotulo = rotuloAno(ano.ano);
  const idMotivo = useId();

  async function excluir() {
    setConfirmando(false);
    try {
      await salvar({
        descricao: `Excluir ano ${rotulo}`,
        executar: () => projetosApi.excluirAno(slug, ano.ano),
        aplicar: (p) => trocarAnos(p, (anos) => anos.filter((a) => a.ano !== ano.ano)),
      });
      navigate(caminhoProjeto(slug));
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }

  return (
    <div className="flex flex-col items-end gap-2">
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={modo !== "edicao" || unico}
        aria-describedby={unico ? idMotivo : undefined}
        onClick={() => setConfirmando(true)}
      >
        Excluir ano
      </Button>
      {/* Texto visível: botão desabilitado não recebe foco nem mostra tooltip. */}
      {unico && (
        <p id={idMotivo} className="text-xs text-muted-foreground">
          O projeto precisa ter ao menos um ano.
        </p>
      )}
      {erro && <Aviso tom="erro">{erro}</Aviso>}
      <Confirmacao
        aberto={confirmando}
        titulo={`Excluir o ano ${rotulo}?`}
        mensagem={`Os ${ano.descritores.length} descritores do ${rotulo} e as escalas deles serão removidos.`}
        aoCancelar={() => setConfirmando(false)}
        aoConfirmar={() => void excluir()}
      />
    </div>
  );
}
