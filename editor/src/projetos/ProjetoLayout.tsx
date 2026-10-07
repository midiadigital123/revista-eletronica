import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, NavLink, Outlet, useLocation, useMatch, useNavigate, useParams } from "react-router";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import { Check, Download, ExternalLink, FileJson, Pencil, Trash2 } from "lucide-react";
import { rotuloAno, rotuloCaderno, Slug, type Caderno, type Projeto } from "../contrato/schemas";
import { Aviso, Botao, CampoTexto, Confirmacao, Dialogo } from "../ui";
import { Badge } from "@/components/ui/badge";
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Button } from "@/components/ui/button";
import { FieldError, FieldGroup } from "@/components/ui/field";
import { Skeleton } from "@/components/ui/skeleton";
import { Spinner } from "@/components/ui/spinner";
import { cn } from "@/lib/utils";
import { BotaoNovoAno } from "./ano/BotaoNovoAno";
import { projetosApi } from "./api";
import { useProjeto } from "./consultas";
import { EdicaoContext, type Edicao } from "./edicao";
import { horaCurta, mensagemDeErro } from "./formato";
import { useTituloPagina } from "../layout/useTituloPagina";
import { useEdicaoProjeto, type NaoSalvo } from "./useEdicaoProjeto";

/** /projetos/:slug — cabeçalho, ações, faixas de bloqueio, abas e provedor de edição. */
export function ProjetoLayout() {
  const { slug = "" } = useParams();
  const consulta = useProjeto(slug);
  const { edicao, inativo, tentarEditar, naoSalvos, descartarNaoSalvo, repetir } =
    useEdicaoProjeto(slug);
  // O layout não vê os params das rotas filhas; o caderno aberto vem da URL.
  const rotaCaderno = useMatch("/projetos/:slug/:caderno/ano/*");
  const naoEncontrado = consulta.isError && ehErroApi(consulta.error, 404);
  // Só no erro: com o projeto aberto, o título vem da aba (Página, ano, descritor).
  useTituloPagina(
    consulta.isError ? (naoEncontrado ? "Projeto não encontrado" : "Erro ao abrir projeto") : null,
  );

  if (consulta.isPending)
    return (
      <div role="status" className="flex flex-col gap-4 py-8">
        <span className="sr-only">Carregando…</span>
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-9 w-80 max-w-full" />
        <Skeleton className="h-8 w-full max-w-xl" />
        <Skeleton className="mt-4 h-64 w-full" />
      </div>
    );
  if (consulta.isError)
    return (
      <div className="flex flex-col gap-4 py-8">
        <h1 className="text-2xl font-semibold tracking-tight">
          {naoEncontrado ? "Projeto não encontrado" : "Não foi possível abrir o projeto"}
        </h1>
        <Aviso
          tom="erro"
          acao={
            <Button asChild variant="outline" size="sm">
              <Link to="/projetos">Voltar aos projetos</Link>
            </Button>
          }
        >
          {naoEncontrado
            ? "Confira o endereço ou volte à lista de projetos."
            : mensagemDeErro(consulta.error)}
        </Aviso>
      </div>
    );

  const projeto = consulta.data;
  const cadernoAberto = projeto.cadernos.find((c) => c.id === rotaCaderno?.params.caderno);
  return (
    <EdicaoContext value={edicao}>
      <div className="flex flex-col pb-16">
        <Cabecalho
          projeto={projeto}
          edicao={edicao}
          repetir={repetir}
          caderno={cadernoAberto?.id ?? projeto.cadernos[0]?.id}
        />

        <div className="mt-4 flex flex-col gap-3">
          {/* Região viva sempre montada: a faixa que entra é anunciada. */}
          <div role="status" className="empty:hidden">
            <FaixaModo edicao={edicao} inativo={inativo} tentarEditar={tentarEditar} />
          </div>
          {naoSalvos.length > 0 && <NaoSalvos itens={naoSalvos} descartar={descartarNaoSalvo} />}
        </div>

        {/* Dois níveis: Página e cadernos em cima; anos do caderno aberto embaixo. Muitos itens: rola na horizontal. */}
        <nav
          aria-label="Seções do projeto"
          className="mt-6 flex items-center gap-1 overflow-x-auto border-b border-border [scrollbar-width:thin] [scrollbar-color:var(--border)_transparent]"
        >
          <Aba to="." end>
            Página
          </Aba>
          {projeto.cadernos.map((c) => (
            <Aba
              key={c.id}
              to={c.anos[0] ? `${c.id}/ano/${c.anos[0].ano}` : "."}
              ativa={cadernoAberto?.id === c.id}
            >
              {rotuloCaderno(c.id)}
            </Aba>
          ))}
        </nav>

        {cadernoAberto && (
          <nav
            aria-label={`Anos de ${rotuloCaderno(cadernoAberto.id)}`}
            className="mt-4 flex flex-wrap items-center gap-3"
          >
            <div className="flex items-center gap-0.5 rounded-lg bg-muted p-1">
              {cadernoAberto.anos.map((a) => (
                <NavLink
                  key={a.ano}
                  to={`${cadernoAberto.id}/ano/${a.ano}`}
                  className={({ isActive }) =>
                    cn(
                      "rounded-md px-3 py-1 text-sm font-medium whitespace-nowrap tabular-nums transition-colors duration-150 ease-saida outline-none focus-visible:ring-3 focus-visible:ring-ring",
                      isActive
                        ? "bg-background text-foreground shadow-[0_1px_2px_oklch(0_0_0/0.08)]"
                        : "text-muted-foreground hover:text-foreground",
                    )
                  }
                >
                  {rotuloAno(a.ano)}
                </NavLink>
              ))}
            </div>
            <BotaoNovoAno caderno={cadernoAberto} />
          </nav>
        )}

        <div className="pt-8">
          <Outlet />
        </div>
      </div>
    </EdicaoContext>
  );
}

/** `ativa` sobrepõe o NavLink: a aba do caderno aponta para um ano, mas vale para todos os anos dele. */
function Aba({
  to,
  end,
  ativa,
  children,
}: {
  to: string;
  end?: boolean;
  ativa?: boolean;
  children: React.ReactNode;
}) {
  return (
    <NavLink
      to={to}
      end={end}
      aria-current={ativa ? "page" : undefined}
      className={({ isActive }) =>
        cn(
          "shrink-0 border-b-2 px-3 py-2.5 text-sm font-medium whitespace-nowrap transition-colors duration-150 ease-saida outline-none focus-visible:rounded-sm focus-visible:ring-3 focus-visible:ring-ring",
          (ativa ?? isActive)
            ? "border-primary text-foreground"
            : "border-transparent text-muted-foreground hover:text-foreground",
        )
      }
    >
      {children}
    </NavLink>
  );
}

function Cabecalho({
  projeto,
  edicao,
  repetir,
  caderno,
}: {
  projeto: Projeto;
  edicao: Edicao;
  repetir: (() => void) | null;
  /** Caderno da aba aberta (na aba Página, o primeiro): o Preview abre direto nele. */
  caderno: Caderno | undefined;
}) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [dialogo, setDialogo] = useState<"renomear" | "excluir" | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);
  const podeEditar = edicao.modo === "edicao";
  const { slug } = projeto;

  // Um arquivo só, no formato de `origem.cadernos` da importação: {caderno: Revista}.
  const exportar = async () => {
    setErroAcao(null);
    try {
      const revistas = await Promise.all(
        projeto.cadernos.map(async (c) => [c.id, await projetosApi.exportar(slug, c.id)] as const),
      );
      const url = URL.createObjectURL(
        new Blob([JSON.stringify(Object.fromEntries(revistas), null, 2)], {
          type: "application/json",
        }),
      );
      const link = document.createElement("a");
      link.href = url;
      link.download = `${slug}.json`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      setErroAcao(`Exportar JSON: ${mensagemDeErro(e)}`);
    }
  };

  const excluir = async () => {
    setDialogo(null);
    try {
      // `aplicar` identidade: sem refetch de um projeto que deixou de existir.
      await edicao.salvar({
        descricao: "Excluir projeto",
        executar: () => projetosApi.excluir(slug),
        aplicar: (p) => p,
      });
      void queryClient.invalidateQueries({ queryKey: chaves.projetos, exact: true });
      navigate("/projetos", { replace: true });
    } catch (e) {
      setErroAcao(`Excluir: ${mensagemDeErro(e)}`);
    }
  };

  return (
    <header className="flex flex-col gap-4 border-b border-border pt-6 pb-5">
      <Breadcrumb>
        <BreadcrumbList>
          <BreadcrumbItem>
            <BreadcrumbLink asChild>
              <Link to="/projetos">Projetos</Link>
            </BreadcrumbLink>
          </BreadcrumbItem>
          <BreadcrumbSeparator />
          <BreadcrumbItem>
            <BreadcrumbPage>{projeto.nome}</BreadcrumbPage>
          </BreadcrumbItem>
        </BreadcrumbList>
      </Breadcrumb>
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <h1 className="min-w-0 text-3xl font-semibold tracking-tight">{projeto.nome}</h1>
        <IndicadorSalvamento edicao={edicao} repetir={repetir} />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <Button asChild size="sm">
          <a href={projetosApi.urlPacote(slug)} download={`${slug}.zip`}>
            <Download data-icon="inline-start" />
            Gerar pacote .zip
          </a>
        </Button>
        {caderno && (
          <Button asChild variant="outline" size="sm">
            <a href={projetosApi.urlPreview(slug, caderno)} target="_blank" rel="noopener">
              Preview
              <ExternalLink data-icon="inline-end" />
            </a>
          </Button>
        )}
        <Button type="button" variant="outline" size="sm" onClick={() => void exportar()}>
          <FileJson data-icon="inline-start" />
          Exportar JSON
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!podeEditar}
          onClick={() => setDialogo("renomear")}
        >
          <Pencil data-icon="inline-start" />
          Renomear
        </Button>
        <Button
          type="button"
          variant="destructive"
          size="sm"
          className="ml-auto"
          disabled={!podeEditar}
          onClick={() => setDialogo("excluir")}
        >
          <Trash2 data-icon="inline-start" />
          Excluir
        </Button>
      </div>
      {erroAcao && <Aviso tom="erro">{erroAcao}</Aviso>}

      <Renomear
        aberto={dialogo === "renomear"}
        aoFechar={() => setDialogo(null)}
        projeto={projeto}
        edicao={edicao}
      />
      <Confirmacao
        aberto={dialogo === "excluir"}
        titulo="Excluir projeto"
        mensagem={`Excluir “${projeto.nome}”? O projeto sai da lista e o identificador fica livre para reuso.`}
        aoConfirmar={() => void excluir()}
        aoCancelar={() => setDialogo(null)}
      />
    </header>
  );
}

const MODO = {
  edicao: { rotulo: "Editando", variante: "default" },
  leitura: { rotulo: "Somente leitura", variante: "secondary" },
  carregando: { rotulo: "Conectando…", variante: "outline" },
} as const;

function IndicadorSalvamento({
  edicao,
  repetir,
}: {
  edicao: Edicao;
  repetir: (() => void) | null;
}) {
  const { salvamento, modo } = edicao;
  const erro = salvamento.status === "erro";
  return (
    <div className="flex min-h-6 flex-wrap items-center gap-x-3 gap-y-1 text-sm">
      <Badge variant={MODO[modo].variante}>{MODO[modo].rotulo}</Badge>
      <span
        role="status"
        aria-live="polite"
        className={erro ? "text-destructive" : "text-muted-foreground"}
      >
        {/* key por estado: cada troca remonta o texto e o @starting-style faz o fade (uma vez, sem loop). */}
        <span
          key={salvamento.status}
          className="inline-flex items-center gap-1.5 transition-opacity duration-180 ease-saida starting:opacity-0"
        >
          {salvamento.status === "salvando" && (
            <>
              <Spinner aria-hidden="true" className="size-3.5" />
              Salvando…
            </>
          )}
          {salvamento.status === "salvo" && salvamento.salvoEm && (
            <>
              <Check aria-hidden="true" className="size-3.5" />
              {`Salvo às ${horaCurta(salvamento.salvoEm)}`}
            </>
          )}
          {erro && `Erro: ${salvamento.erro ?? "falha ao salvar"}`}
        </span>
      </span>
      {erro && repetir && (
        <Button type="button" variant="link" size="sm" className="h-auto px-0" onClick={repetir}>
          tentar de novo
        </Button>
      )}
    </div>
  );
}

function FaixaModo({
  edicao,
  inativo,
  tentarEditar,
}: {
  edicao: Edicao;
  inativo: boolean;
  tentarEditar: () => Promise<void>;
}) {
  const [tentando, setTentando] = useState(false);
  if (edicao.modo !== "leitura") return null;
  const tentar = async () => {
    setTentando(true);
    await tentarEditar();
    setTentando(false);
  };
  const botao = (rotulo: string) => (
    <Botao tamanho="sm" variante="primario" disabled={tentando} onClick={() => void tentar()}>
      {rotulo}
    </Botao>
  );
  if (inativo)
    return (
      <Aviso tom="info" semRole acao={botao("Voltar a editar")}>
        Você saiu da edição por inatividade. Os campos estão em modo leitura.
      </Aviso>
    );
  const { bloqueio } = edicao;
  return (
    <Aviso tom="alerta" semRole acao={botao("Tentar editar")}>
      {bloqueio
        ? `Em edição por ${bloqueio.nome} desde ${horaCurta(bloqueio.desde)}. Você está em modo leitura.`
        : "Você não está editando este projeto. Modo leitura."}
    </Aviso>
  );
}

/**
 * navigator.clipboard só existe em contexto seguro (HTTPS/localhost). Pela rede em http,
 * cai no execCommand("copy") com um textarea temporário. Devolve se copiou.
 */
async function copiarTexto(texto: string): Promise<boolean> {
  if (navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(texto);
      return true;
    } catch {
      // permissão negada: tenta o caminho antigo
    }
  }
  const area = document.createElement("textarea");
  area.value = texto;
  area.setAttribute("readonly", "");
  area.style.position = "fixed";
  area.style.opacity = "0";
  document.body.append(area);
  area.select();
  try {
    return document.execCommand("copy");
  } catch {
    return false;
  } finally {
    area.remove();
  }
}

function NaoSalvos({ itens, descartar }: { itens: NaoSalvo[]; descartar: (id: number) => void }) {
  const [copiado, setCopiado] = useState<{ id: number; ok: boolean } | null>(null);
  const copiar = async (n: NaoSalvo) =>
    setCopiado({ id: n.id, ok: await copiarTexto(n.valor ?? "") });
  return (
    <Aviso tom="erro">
      <p className="font-semibold">
        Estas alterações não foram salvas (outra pessoa assumiu a edição):
      </p>
      <ul className="mt-2 flex flex-col gap-2">
        {itens.map((n) => (
          <li key={n.id} className="flex flex-wrap items-center gap-2">
            <span className="font-medium">{n.descricao}</span>
            {n.valor !== undefined && (
              <>
                <span className="max-w-xl truncate text-muted-foreground">{n.valor}</span>
                <Botao tamanho="sm" onClick={() => void copiar(n)}>
                  {copiado?.id === n.id && copiado.ok ? "Copiado" : "Copiar"}
                </Botao>
                {copiado?.id === n.id && !copiado.ok && (
                  <span className="text-sm">Não foi possível copiar.</span>
                )}
              </>
            )}
            <Botao tamanho="sm" variante="fantasma" onClick={() => descartar(n.id)}>
              Dispensar
            </Botao>
          </li>
        ))}
      </ul>
    </Aviso>
  );
}

function Renomear({
  aberto,
  aoFechar,
  projeto,
  edicao,
}: {
  aberto: boolean;
  aoFechar: () => void;
  projeto: Projeto;
  edicao: Edicao;
}) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [nome, setNome] = useState(projeto.nome);
  const [slug, setSlug] = useState(projeto.slug);
  const [erros, setErros] = useState<{ nome?: string; slug?: string; geral?: string }>({});
  const [enviando, setEnviando] = useState(false);

  // Zera ao REABRIR: ao fechar, o conteúdo fica intacto durante a animação de saída.
  const [abertoAntes, setAbertoAntes] = useState(aberto);
  if (aberto !== abertoAntes) {
    setAbertoAntes(aberto);
    if (aberto) {
      setNome(projeto.nome);
      setSlug(projeto.slug);
      setErros({});
    }
  }
  const fechar = aoFechar;

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault();
    const novos: typeof erros = {};
    if (!nome.trim()) novos.nome = "Informe o nome";
    const s = Slug.safeParse(slug);
    if (!s.success) novos.slug = s.error.issues[0]?.message ?? "Identificador inválido";
    setErros(novos);
    if (Object.keys(novos).length) return;

    const dados = {
      ...(nome.trim() !== projeto.nome && { nome: nome.trim() }),
      ...(slug !== projeto.slug && { slug }),
    };
    if (!Object.keys(dados).length) return fechar();
    setEnviando(true);
    try {
      const novo = await edicao.salvar({
        descricao: "Renomear projeto",
        valor: `${dados.nome ?? projeto.nome} (${dados.slug ?? projeto.slug})`,
        executar: () => projetosApi.atualizar(projeto.slug, dados),
        aplicar: (_, resposta) => resposta,
      });
      void queryClient.invalidateQueries({ queryKey: chaves.projetos, exact: true });
      aoFechar();
      if (novo.slug !== projeto.slug) {
        queryClient.setQueryData(chaves.projeto(novo.slug), novo);
        navigate(pathname.replace(`/projetos/${projeto.slug}`, `/projetos/${novo.slug}`), {
          replace: true,
        });
      }
    } catch (e) {
      if (ehErroApi(e) && e.campo === "slug") setErros({ slug: e.message });
      else setErros({ geral: mensagemDeErro(e) });
    } finally {
      setEnviando(false);
    }
  };

  return (
    <Dialogo
      aberto={aberto}
      aoFechar={fechar}
      titulo="Renomear projeto"
      bloqueado={enviando}
      acoes={
        <>
          <Botao onClick={fechar} disabled={enviando}>
            Cancelar
          </Botao>
          <Botao type="submit" form="form-renomear" variante="primario" disabled={enviando}>
            {enviando && <Spinner data-icon="inline-start" />}
            Salvar
          </Botao>
        </>
      }
    >
      <form id="form-renomear" noValidate onSubmit={enviar}>
        <FieldGroup>
          <CampoTexto
            rotulo="Nome"
            value={nome}
            erro={erros.nome}
            onChange={(e) => setNome(e.target.value)}
          />
          <CampoTexto
            rotulo="Identificador (slug)"
            value={slug}
            erro={erros.slug}
            ajuda="Mudar o identificador muda a URL do projeto."
            onChange={(e) => setSlug(e.target.value)}
          />
          {erros.geral && <FieldError>{erros.geral}</FieldError>}
        </FieldGroup>
      </form>
    </Dialogo>
  );
}
