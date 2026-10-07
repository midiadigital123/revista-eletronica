import { useId, type ReactNode } from "react";
import { useNavigate } from "react-router";
import {
  Codigo,
  ROTULO_ANO,
  type AnoProjeto,
  type AtualizarDescritorEntrada,
  type Descritor,
} from "../../contrato/schemas";
import { Empty, EmptyDescription, EmptyHeader, EmptyTitle } from "@/components/ui/empty";
import { FieldSet } from "@/components/ui/field";
import { Separator } from "@/components/ui/separator";
import { AreaTexto, CampoTexto } from "../../ui";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import { caminhoDescritor, rotuloPadrao, trocarDescritor, useAnoAtual } from "./dados";
import { EditorEscala, type PersistirPadrao } from "./EditorEscala";
import { ListaTextos } from "./ListaTextos";
import { useAutoSalvar } from "./useAutoSalvar";
import { useTituloPagina } from "../../layout/useTituloPagina";

/** Rota ano/:ano/:codigo. O formulário é remontado (key) quando muda de descritor. */
export function TelaDescritor() {
  const { projeto, anoProjeto, codigo } = useAnoAtual();
  const descritor = anoProjeto?.descritores.find((d) => d.codigo === codigo);
  useTituloPagina(
    projeto && anoProjeto
      ? `${descritor ? codigo : "Descritor não encontrado"} · ${ROTULO_ANO[anoProjeto.ano]} · ${projeto.nome}`
      : null,
  );
  if (!anoProjeto) return null;
  if (!descritor)
    return (
      <Empty role="status" className="border">
        <EmptyHeader>
          <EmptyTitle>
            <h2>Descritor não encontrado</h2>
          </EmptyTitle>
          <EmptyDescription>
            O descritor {codigo} não existe no {ROTULO_ANO[anoProjeto.ano]}.
          </EmptyDescription>
        </EmptyHeader>
      </Empty>
    );
  return (
    <FormDescritor
      key={`${anoProjeto.ano}-${descritor.codigo}`}
      ano={anoProjeto}
      descritor={descritor}
    />
  );
}

type Patch = AtualizarDescritorEntrada;

function FormDescritor({ ano, descritor }: { ano: AnoProjeto; descritor: Descritor }) {
  const { slug, modo, salvar } = useEdicao();
  const navigate = useNavigate();
  const idTopicos = useId();
  const { codigo } = descritor;
  const topicos = [...new Set(ano.descritores.map((d) => d.topic).filter(Boolean))].sort();

  const atualizar = (descricao: string, patch: Patch, valor?: string) =>
    salvar({
      descricao: `${descricao} do ${codigo} (${ROTULO_ANO[ano.ano]})`,
      valor,
      executar: () => projetosApi.atualizarDescritor(slug, ano.ano, codigo, patch),
      aplicar: (p, novo) => trocarDescritor(p, ano.ano, codigo, () => novo),
    });

  const persistirPadrao: PersistirPadrao = (padrao, linhas) =>
    salvar({
      descricao: `Escala do ${codigo} (${ROTULO_ANO[ano.ano]}), ${rotuloPadrao(padrao)}`,
      valor: JSON.stringify(linhas),
      executar: () => projetosApi.salvarEscala(slug, ano.ano, codigo, padrao, linhas),
      aplicar: (p, resposta) =>
        trocarDescritor(p, ano.ano, codigo, (d) => ({
          ...d,
          scale: { ...d.scale, [padrao]: resposta },
        })),
    });

  async function renomear(novo: string) {
    const valido = Codigo.safeParse(novo);
    if (!valido.success) throw new Error(valido.error.issues[0]?.message);
    const renomeado = await atualizar("Código", { codigo: novo }, novo);
    navigate(caminhoDescritor(slug, ano.ano, renomeado.codigo), { replace: true });
  }

  const campoCodigo = useAutoSalvar(
    codigo,
    (v) => renomear(v.trim().toUpperCase()),
    (v) => v.trim().toUpperCase(),
  );
  const topico = useAutoSalvar(descritor.topic, (v) => atualizar("Tópico", { topic: v }, v));
  const descricao = useAutoSalvar(descritor.description, (v) =>
    atualizar("Descrição", { description: v }, v),
  );
  const praticas = useAutoSalvar(descritor.bncc.practices, (v) =>
    atualizar("Práticas BNCC", { bncc: { practices: v } }, v),
  );
  const objetos = useAutoSalvar(descritor.bncc.knowledge, (v) =>
    atualizar("Objetos de conhecimento", { bncc: { knowledge: v } }, v),
  );

  return (
    <article aria-labelledby="titulo-descritor" className="flex flex-col gap-6">
      <h2 id="titulo-descritor" className="flex items-baseline gap-3">
        <span className="text-2xl font-semibold tabular-nums">{codigo}</span>
        <span className="text-base font-normal text-muted-foreground">{ROTULO_ANO[ano.ano]}</span>
      </h2>

      {/* <fieldset disabled> nativo: fora do modo edição, desabilita todos os controles de dentro. */}
      <FieldSet disabled={modo !== "edicao"} className="min-w-0 gap-8">
        <Secao titulo="Identificação">
          <div className="grid gap-4 sm:grid-cols-[8rem_1fr]">
            <CampoTexto
              rotulo="Código"
              className="uppercase tabular-nums"
              value={campoCodigo.valor}
              erro={campoCodigo.erro}
              maxLength={3}
              onChange={(e) => campoCodigo.setValor(e.target.value)}
              onBlur={() => void campoCodigo.confirmar()}
            />
            <CampoTexto
              rotulo="Tópico"
              list={idTopicos}
              value={topico.valor}
              erro={topico.erro}
              onChange={(e) => topico.setValor(e.target.value)}
              onBlur={() => void topico.confirmar()}
            />
            <datalist id={idTopicos}>
              {topicos.map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
          </div>
          <AreaTexto
            rotulo="Descrição"
            rows={3}
            value={descricao.valor}
            erro={descricao.erro}
            onChange={(e) => descricao.setValor(e.target.value)}
            onBlur={() => void descricao.confirmar()}
          />
        </Secao>

        <Separator />

        <Secao titulo="Pré-requisitos">
          <ListaTextos
            rotulo="Lista de pré-requisitos"
            rotuloOculto
            rotuloItem="Pré-requisito"
            inicial={descritor.prerequisites}
            persistir={(lista) =>
              atualizar("Pré-requisitos", { prerequisites: lista }, lista.join("\n"))
            }
          />
        </Secao>

        <Separator />

        <Secao titulo="BNCC">
          <div className="grid gap-4 md:grid-cols-2">
            <AreaTexto
              rotulo="Práticas de linguagem"
              value={praticas.valor}
              erro={praticas.erro}
              onChange={(e) => praticas.setValor(e.target.value)}
              onBlur={() => void praticas.confirmar()}
            />
            <AreaTexto
              rotulo="Objetos de conhecimento"
              value={objetos.valor}
              erro={objetos.erro}
              onChange={(e) => objetos.setValor(e.target.value)}
              onBlur={() => void objetos.confirmar()}
            />
          </div>
          <ListaTextos
            rotulo="Habilidades"
            rotuloItem="Habilidade"
            inicial={descritor.bncc.skills}
            persistir={(lista) =>
              atualizar("Habilidades BNCC", { bncc: { skills: lista } }, lista.join("\n"))
            }
          />
        </Secao>

        <Separator />

        <Secao titulo="Escala de proficiência">
          <EditorEscala ano={ano} escala={descritor.scale} persistir={persistirPadrao} />
        </Secao>
      </FieldSet>
    </article>
  );
}

function Secao({ titulo, children }: { titulo: string; children: ReactNode }) {
  const id = useId();
  return (
    <section aria-labelledby={id} className="flex min-w-0 flex-col gap-4">
      <h3 id={id} className="text-lg font-semibold">
        {titulo}
      </h3>
      {children}
    </section>
  );
}
