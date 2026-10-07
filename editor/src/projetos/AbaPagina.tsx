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
import { AreaTexto, Aviso, Botao, CampoTexto } from "../ui";
import { projetosApi } from "./api";
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
  const campos = useQuery({
    queryKey: chaves.camposPagina,
    queryFn: projetosApi.camposPagina,
    staleTime: Infinity,
  });

  if (campos.isPending || !projeto) return <p className="text-tinta-suave">Carregando campos…</p>;
  if (campos.isError)
    return (
      <Aviso tom="erro">Não foi possível carregar os campos: {mensagemDeErro(campos.error)}</Aviso>
    );

  const somenteLeitura = edicao.modo !== "edicao";
  return (
    <section aria-labelledby="titulo-pagina" className="max-w-4xl">
      <h2 id="titulo-pagina" className="text-2xl">
        Página da revista
      </h2>
      <p className="mt-1 text-sm text-tinta-suave">
        {somenteLeitura
          ? "Modo leitura: os campos estão bloqueados enquanto você não detém a edição."
          : "As alterações são salvas ao sair de cada campo. Campo vazio usa o texto padrão da revista."}
      </p>
      {/* Só desabilita ao trocar de modo (não remonta): texto ainda não salvo continua no campo. */}
      <fieldset
        disabled={somenteLeitura}
        className="mt-6 divide-y divide-linha border-y border-linha"
      >
        {campos.data.map((campo) => (
          <div key={campo.chave} className="py-6">
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
    <Botao tamanho="sm" variante="fantasma" onClick={onClick}>
      Restaurar padrão
    </Botao>
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
      <div>
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
    <fieldset className="flex flex-col gap-3">
      <legend className="text-sm font-semibold">{campo.rotulo}</legend>
      {campo.ajuda && <p className="text-xs text-tinta-suave">{campo.ajuda}</p>}
      {itens.length === 0 && (
        <p className="text-sm text-tinta-suave">Sem parágrafos: a revista usa o texto padrão.</p>
      )}
      {itens.map((p, i) => (
        <div key={p.id} className="flex items-start gap-2">
          <div className="flex-1">
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
          <Botao
            tamanho="sm"
            variante="fantasma"
            className="mt-6"
            aria-label={`Remover parágrafo ${i + 1}`}
            onClick={() => {
              const lista = itens.filter((x) => x.id !== p.id);
              setItens(lista);
              salvarSeMudou(lista);
            }}
          >
            ×
          </Botao>
        </div>
      ))}
      {erro && (
        <p role="alert" className="text-xs text-erro">
          {erro}
        </p>
      )}
      <div className="flex gap-2">
        <Botao tamanho="sm" onClick={() => setItens((l) => [...l, novoParagrafo("")])}>
          + parágrafo
        </Botao>
        <Restaurar
          onClick={() => {
            setItens([]);
            void salvar(null);
          }}
        />
      </div>
    </fieldset>
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
    <div className="flex flex-col gap-3">
      <label htmlFor={idEntrada} className="text-sm font-semibold">
        {campo.rotulo}
      </label>
      <div className="flex flex-wrap items-start gap-4">
        <div className="flex h-32 w-48 items-center justify-center overflow-hidden rounded-md border border-linha bg-papel">
          {imagem ? (
            <img
              src={projetosApi.urlImagem(
                edicao.slug,
                campo.chave,
                `${imagem.tamanho}-${imagem.nome}`,
              )}
              alt={`${campo.rotulo} atual`}
              className="h-full w-full object-cover"
            />
          ) : (
            <span className="px-3 text-center text-xs text-tinta-suave">
              Imagem padrão da revista
            </span>
          )}
        </div>
        <div className="flex flex-col gap-2">
          <input
            ref={entrada}
            id={idEntrada}
            type="file"
            accept={IMAGEM_MIMES.join(",")}
            aria-describedby={`${idEntrada}-ajuda`}
            onChange={(e) => enviar(e.target.files?.[0])}
            className="text-sm file:mr-3 file:rounded-md file:border file:border-linha file:bg-superficie file:px-3 file:py-1.5 file:font-medium"
          />
          <p id={`${idEntrada}-ajuda`} className="text-xs text-tinta-suave">
            {campo.ajuda ?? "PNG, JPEG ou WebP, até 5 MB."}
            {imagem && <span className="ml-1 font-mono">{imagem.nome}</span>}
          </p>
          {imagem && (
            <div>
              <Botao
                tamanho="sm"
                variante="fantasma"
                onClick={() =>
                  void executar(`Remover ${campo.rotulo}`, () =>
                    projetosApi.removerImagem(edicao.slug, campo.chave),
                  )
                }
              >
                Remover imagem (usar padrão)
              </Botao>
            </div>
          )}
          {erro && (
            <p role="alert" className="text-xs text-erro">
              {erro}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
