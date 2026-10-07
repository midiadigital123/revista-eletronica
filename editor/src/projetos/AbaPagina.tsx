import { useQuery } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { chaves } from "../api/chaves";
import type { CampoPagina } from "../contrato/campos-pagina";
import {
  IMAGEM_MAX_BYTES,
  IMAGEM_MIMES,
  type ImagemPagina,
  type Pagina,
  type Projeto,
} from "../contrato/schemas";
import { RotateCcw, X } from "lucide-react";
import { AreaTexto, Aviso, CampoTexto } from "../ui";
import { Button } from "@/components/ui/button";
import {
  Field,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSeparator,
  FieldSet,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { projetosApi } from "./api";
import { useTituloPagina } from "../layout/useTituloPagina";
import { useProjeto } from "./consultas";
import { useEdicao, type Edicao } from "./edicao";
import { mensagemDeErro } from "./formato";

type ValorPagina = Pagina[string];

const ehImagem = (v: ValorPagina | undefined): v is ImagemPagina =>
  typeof v === "object" && !Array.isArray(v);

/** Aplica a Pagina devolvida pela API ao projeto em cache (sem refetch). */
const aplicarPagina = (projeto: Projeto, pagina: Pagina): Projeto => ({ ...projeto, pagina });

/** Aba "Página" (rota index de /projetos/:slug): formulário gerado de GET /api/pagina/campos. */
export function AbaPagina() {
  const edicao = useEdicao();
  const { data: projeto } = useProjeto(edicao.slug);
  useTituloPagina(projeto?.nome ?? null);
  const campos = useQuery({
    queryKey: chaves.camposPagina,
    queryFn: projetosApi.camposPagina,
    staleTime: Infinity,
  });

  if (campos.isPending || !projeto)
    return (
      <div role="status" className="flex max-w-3xl flex-col gap-6">
        <span className="sr-only">Carregando…</span>
        <Skeleton className="h-6 w-48" />
        {[0, 1, 2].map((i) => (
          <div key={i} className="flex flex-col gap-2">
            <Skeleton className="h-4 w-32" />
            <Skeleton className="h-9 w-full" />
          </div>
        ))}
      </div>
    );
  if (campos.isError)
    return (
      <Aviso tom="erro">Não foi possível carregar os campos: {mensagemDeErro(campos.error)}</Aviso>
    );

  const somenteLeitura = edicao.modo !== "edicao";
  return (
    <section aria-labelledby="titulo-pagina" className="flex max-w-3xl flex-col gap-1">
      <h2 id="titulo-pagina" className="text-xl font-semibold tracking-tight">
        Página da revista
      </h2>
      <p className="text-sm text-muted-foreground">
        {somenteLeitura
          ? "Modo leitura: os campos estão bloqueados enquanto você não detém a edição."
          : "As alterações são salvas ao sair de cada campo. Campo vazio usa o texto padrão da revista."}
      </p>
      {/* Só desabilita ao trocar de modo (não remonta): texto ainda não salvo continua no campo. */}
      <fieldset disabled={somenteLeitura} className="mt-6 min-w-0">
        <FieldGroup>
          {campos.data.map((campo, i) => (
            <div key={campo.chave} className="flex flex-col gap-7">
              {i > 0 && <FieldSeparator />}
              {campo.tipo === "texto" && (
                <CampoTextoPagina
                  campo={campo}
                  inicial={projeto.pagina[campo.chave]}
                  edicao={edicao}
                />
              )}
              {campo.tipo === "paragrafos" && (
                <CampoParagrafos
                  campo={campo}
                  inicial={projeto.pagina[campo.chave]}
                  edicao={edicao}
                />
              )}
              {campo.tipo === "imagem" && (
                <CampoImagem campo={campo} valor={projeto.pagina[campo.chave]} edicao={edicao} />
              )}
            </div>
          ))}
        </FieldGroup>
      </fieldset>
    </section>
  );
}

interface PropsCampo {
  campo: CampoPagina;
  inicial: ValorPagina | undefined;
  edicao: Edicao;
}

/** Salva um patch da página pela fila de edição; devolve a mensagem de erro (ou undefined). */
async function salvarPatch(edicao: Edicao, campo: CampoPagina, valor: string | string[] | null) {
  try {
    await edicao.salvar({
      descricao: campo.rotulo,
      valor: valor === null ? undefined : Array.isArray(valor) ? valor.join("\n\n") : valor,
      executar: () => projetosApi.atualizarPagina(edicao.slug, { [campo.chave]: valor }),
      aplicar: aplicarPagina,
    });
    return undefined;
  } catch (e) {
    return mensagemDeErro(e);
  }
}

function Restaurar({ onClick }: { onClick: () => void }) {
  return (
    <Button type="button" size="sm" variant="ghost" onClick={onClick}>
      <RotateCcw data-icon="inline-start" />
      Restaurar padrão
    </Button>
  );
}

function CampoTextoPagina({ campo, inicial, edicao }: PropsCampo) {
  const [valor, setValor] = useState(typeof inicial === "string" ? inicial : "");
  const salvo = useRef(valor);
  const [erro, setErro] = useState<string>();

  const salvar = async (novo: string | null) => {
    const anterior = salvo.current;
    salvo.current = novo ?? "";
    const falha = await salvarPatch(edicao, campo, novo);
    if (falha) salvo.current = anterior; // o próximo blur reenvia
    setErro(falha);
  };

  return (
    <div className="flex flex-col gap-2">
      <CampoTexto
        rotulo={campo.rotulo}
        value={valor}
        maxLength={campo.max}
        erro={erro}
        ajuda={campo.ajuda}
        placeholder="Texto padrão da revista"
        onChange={(e) => setValor(e.target.value)}
        onBlur={() => {
          if (valor !== salvo.current) void salvar(valor);
        }}
      />
      <div className="flex">
        <Restaurar
          onClick={() => {
            setValor("");
            void salvar(null);
          }}
        />
      </div>
    </div>
  );
}

interface Paragrafo {
  id: string;
  texto: string;
}

const novoParagrafo = (texto: string): Paragrafo => ({ id: crypto.randomUUID(), texto });

function CampoParagrafos({ campo, inicial, edicao }: PropsCampo) {
  const [itens, setItens] = useState<Paragrafo[]>(() =>
    (Array.isArray(inicial) ? inicial : []).map(novoParagrafo),
  );
  const salvo = useRef(JSON.stringify(itens.map((p) => p.texto)));
  const [erro, setErro] = useState<string>();

  const salvar = async (lista: Paragrafo[] | null) => {
    const textos = lista?.map((p) => p.texto) ?? null;
    const anterior = salvo.current;
    salvo.current = JSON.stringify(textos ?? []);
    const falha = await salvarPatch(edicao, campo, textos);
    if (falha) salvo.current = anterior; // o próximo blur reenvia
    setErro(falha);
  };
  const salvarSeMudou = (lista: Paragrafo[]) => {
    if (JSON.stringify(lista.map((p) => p.texto)) !== salvo.current) void salvar(lista);
  };

  return (
    <FieldSet>
      <FieldLegend variant="label">{campo.rotulo}</FieldLegend>
      {campo.ajuda && <FieldDescription>{campo.ajuda}</FieldDescription>}
      {itens.length === 0 && (
        <FieldDescription>Sem parágrafos: a revista usa o texto padrão.</FieldDescription>
      )}
      {itens.map((p, i) => (
        <div key={p.id} className="flex animate-entra items-start gap-2">
          <div className="min-w-0 flex-1">
            <AreaTexto
              rotulo={`Parágrafo ${i + 1}`}
              value={p.texto}
              maxLength={campo.max}
              rows={4}
              onChange={(e) =>
                setItens((l) => l.map((x) => (x.id === p.id ? { ...x, texto: e.target.value } : x)))
              }
              onBlur={() => salvarSeMudou(itens)}
            />
          </div>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                size="icon-sm"
                variant="ghost"
                className="mt-7"
                aria-label={`Remover parágrafo ${i + 1}`}
                onClick={() => {
                  const lista = itens.filter((x) => x.id !== p.id);
                  setItens(lista);
                  salvarSeMudou(lista);
                }}
              >
                <X />
              </Button>
            </TooltipTrigger>
            <TooltipContent>Remover e salvar</TooltipContent>
          </Tooltip>
        </div>
      ))}
      {erro && <FieldError>{erro}</FieldError>}
      <div className="flex flex-wrap gap-2">
        <Button
          type="button"
          size="sm"
          variant="outline"
          onClick={() => setItens((l) => [...l, novoParagrafo("")])}
        >
          + parágrafo
        </Button>
        <Restaurar
          onClick={() => {
            setItens([]);
            void salvar(null);
          }}
        />
      </div>
    </FieldSet>
  );
}

function CampoImagem({
  campo,
  valor,
  edicao,
}: {
  campo: CampoPagina;
  valor: ValorPagina | undefined;
  edicao: Edicao;
}) {
  const [erro, setErro] = useState<string>();
  const entrada = useRef<HTMLInputElement>(null);
  const imagem = ehImagem(valor) ? valor : null;
  const idEntrada = `imagem-${campo.chave}`;

  const executar = async (descricao: string, escrita: () => Promise<Pagina>) => {
    setErro(undefined);
    try {
      await edicao.salvar({ descricao, executar: escrita, aplicar: aplicarPagina });
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  };

  const enviar = (arquivo: File | undefined) => {
    if (entrada.current) entrada.current.value = "";
    if (!arquivo) return;
    if (!(IMAGEM_MIMES as readonly string[]).includes(arquivo.type))
      return setErro("Envie PNG, JPEG ou WebP.");
    if (arquivo.size > IMAGEM_MAX_BYTES) return setErro("A imagem passa de 5 MB.");
    void executar(campo.rotulo, () => projetosApi.enviarImagem(edicao.slug, campo.chave, arquivo));
  };

  return (
    <Field data-invalid={erro ? true : undefined}>
      <FieldLabel htmlFor={idEntrada}>{campo.rotulo}</FieldLabel>
      <div className="flex flex-wrap items-start gap-4">
        <div className="flex aspect-[3/2] w-48 shrink-0 items-center justify-center overflow-hidden rounded-md border border-border bg-muted">
          {imagem ? (
            <img
              src={projetosApi.urlImagem(
                edicao.slug,
                campo.chave,
                `${imagem.tamanho}-${imagem.nome}`,
              )}
              alt={`${campo.rotulo} atual`}
              className="size-full object-cover"
            />
          ) : (
            <span className="px-3 text-center text-xs text-muted-foreground">
              Imagem padrão da revista
            </span>
          )}
        </div>
        <div className="flex min-w-0 flex-1 flex-col gap-2">
          <Input
            ref={entrada}
            id={idEntrada}
            type="file"
            accept={IMAGEM_MIMES.join(",")}
            aria-invalid={Boolean(erro)}
            aria-describedby={`${idEntrada}-ajuda`}
            onChange={(e) => enviar(e.target.files?.[0])}
            className="max-w-sm"
          />
          <FieldDescription id={`${idEntrada}-ajuda`}>
            {campo.ajuda ?? "PNG, JPEG ou WebP, até 5 MB."}
            {imagem && <span className="ml-1 break-all">{imagem.nome}</span>}
          </FieldDescription>
          {imagem && (
            <div className="flex">
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() =>
                  void executar(`Remover ${campo.rotulo}`, () =>
                    projetosApi.removerImagem(edicao.slug, campo.chave),
                  )
                }
              >
                Remover imagem (usar padrão)
              </Button>
            </div>
          )}
          {erro && <FieldError>{erro}</FieldError>}
        </div>
      </div>
    </Field>
  );
}
