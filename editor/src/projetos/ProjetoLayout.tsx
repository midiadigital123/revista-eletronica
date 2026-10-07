import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate, useParams } from "react-router";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import { ROTULO_ANO, Slug, type Projeto } from "../contrato/schemas";
import { Aviso, Botao, CampoTexto, Confirmacao, Dialogo } from "../ui";
import { BotaoNovoAno } from "./ano/BotaoNovoAno";
import { projetosApi } from "./api";
import { useProjeto } from "./consultas";
import { EdicaoContext, type Edicao } from "./edicao";
import { horaCurta, mensagemDeErro } from "./formato";
import { Cadeado } from "./ListaProjetos";
import { useEdicaoProjeto, type NaoSalvo } from "./useEdicaoProjeto";

/** /projetos/:slug — cabeçalho, ações, faixas de bloqueio, abas e provedor de edição. */
export function ProjetoLayout() {
  const { slug = "" } = useParams();
  const consulta = useProjeto(slug);
  const { edicao, inativo, tentarEditar, naoSalvos, descartarNaoSalvo, repetir } = useEdicaoProjeto(slug);

  if (consulta.isPending) return <p className="mx-auto max-w-6xl px-6 py-10 text-tinta-suave">Carregando projeto…</p>;
  if (consulta.isError)
    return (
      <div className="mx-auto max-w-6xl px-6 py-10">
        <Aviso tom="erro" acao={<Link to="/projetos" className="underline">Voltar aos projetos</Link>}>
          {ehErroApi(consulta.error, 404) ? "Projeto não encontrado." : mensagemDeErro(consulta.error)}
        </Aviso>
      </div>
    );

  const projeto = consulta.data;
  return (
    <EdicaoContext value={edicao}>
      <div className="mx-auto w-full max-w-6xl px-6 pb-16">
        <Cabecalho projeto={projeto} edicao={edicao} repetir={repetir} />

        <div className="mt-4 flex flex-col gap-3">
          <FaixaModo edicao={edicao} inativo={inativo} tentarEditar={tentarEditar} />
          {naoSalvos.length > 0 && <NaoSalvos itens={naoSalvos} descartar={descartarNaoSalvo} />}
        </div>

        <nav aria-label="Seções do projeto" className="mt-6 flex flex-wrap items-center gap-x-1 border-b border-linha">
          <Aba to="." end>
            Página
          </Aba>
          {projeto.anos.map((a) => (
            <Aba key={a.ano} to={`ano/${a.ano}`}>
              <span className="font-mono">{ROTULO_ANO[a.ano]}</span>
            </Aba>
          ))}
          <div className="ml-1 py-1">
            <BotaoNovoAno projeto={projeto} />
          </div>
        </nav>

        <div className="pt-8">
          <Outlet />
        </div>
      </div>
    </EdicaoContext>
  );
}

function Aba({ to, end, children }: { to: string; end?: boolean; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end={end}
      className={({ isActive }) =>
        `-mb-px border-b-2 px-3 py-2.5 text-sm font-medium transition-colors ${
          isActive ? "border-acento text-tinta" : "border-transparent text-tinta-suave hover:text-tinta"
        }`
      }
    >
      {children}
    </NavLink>
  );
}

function Cabecalho({ projeto, edicao, repetir }: { projeto: Projeto; edicao: Edicao; repetir: (() => void) | null }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [dialogo, setDialogo] = useState<"renomear" | "excluir" | null>(null);
  const [erroAcao, setErroAcao] = useState<string | null>(null);
  const podeEditar = edicao.modo === "edicao";
  const { slug } = projeto;

  const exportar = async () => {
    setErroAcao(null);
    try {
      const revista = await projetosApi.exportar(slug);
      const url = URL.createObjectURL(new Blob([JSON.stringify(revista, null, 2)], { type: "application/json" }));
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
      await edicao.salvar({ descricao: "Excluir projeto", executar: () => projetosApi.excluir(slug), aplicar: (p) => p });
      void queryClient.invalidateQueries({ queryKey: chaves.projetos, exact: true });
      navigate("/projetos", { replace: true });
    } catch (e) {
      setErroAcao(`Excluir: ${mensagemDeErro(e)}`);
    }
  };

  return (
    <header className="border-b border-tinta pt-8 pb-5">
      <p className="text-sm text-tinta-suave">
        <Link to="/projetos" className="hover:text-tinta hover:underline">
          Projetos
        </Link>
        <span aria-hidden="true"> / </span>
        <span className="font-mono text-xs">{slug}</span>
      </p>
      <div className="mt-2 flex flex-wrap items-end justify-between gap-x-6 gap-y-4">
        <div className="min-w-0">
          <h1 className="text-4xl font-medium tracking-tight">{projeto.nome}</h1>
          <IndicadorSalvamento edicao={edicao} repetir={repetir} />
        </div>
        <div className="flex flex-wrap gap-2">
          <Botao tamanho="sm" disabled={!podeEditar} onClick={() => setDialogo("renomear")}>
            Renomear
          </Botao>
          <a
            href={projetosApi.urlPreview(slug)}
            target="_blank"
            rel="noopener"
            className="inline-flex h-8 items-center rounded-md border border-linha bg-superficie px-3 text-sm font-medium hover:bg-papel"
          >
            Preview ↗
          </a>
          <a
            href={projetosApi.urlPacote(slug)}
            download={`${slug}.zip`}
            className="inline-flex h-8 items-center rounded-md border border-linha bg-superficie px-3 text-sm font-medium hover:bg-papel"
          >
            Gerar pacote .zip
          </a>
          <Botao tamanho="sm" onClick={() => void exportar()}>
            Exportar JSON
          </Botao>
          <Botao tamanho="sm" variante="fantasma" className="text-erro hover:text-erro" disabled={!podeEditar} onClick={() => setDialogo("excluir")}>
            Excluir
          </Botao>
        </div>
      </div>
      {erroAcao && (
        <div className="mt-3">
          <Aviso tom="erro">{erroAcao}</Aviso>
        </div>
      )}

      <Renomear aberto={dialogo === "renomear"} aoFechar={() => setDialogo(null)} projeto={projeto} edicao={edicao} />
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

function IndicadorSalvamento({ edicao, repetir }: { edicao: Edicao; repetir: (() => void) | null }) {
  const { salvamento, modo } = edicao;
  return (
    <div className="mt-1 flex min-h-6 items-center gap-3 text-sm">
      <span
        className={`rounded-sm px-1.5 font-mono text-[11px] uppercase tracking-wider ${
          modo === "edicao" ? "bg-acento-claro text-acento" : "bg-linha/60 text-tinta-suave"
        }`}
      >
        {modo === "edicao" ? "Editando" : modo === "leitura" ? "Somente leitura" : "Conectando…"}
      </span>
      <span role="status" aria-live="polite" className={salvamento.status === "erro" ? "text-erro" : "text-tinta-suave"}>
        {salvamento.status === "salvando" && "Salvando…"}
        {salvamento.status === "salvo" && salvamento.salvoEm && `Salvo às ${horaCurta(salvamento.salvoEm)}`}
        {salvamento.status === "erro" && `Erro: ${salvamento.erro ?? "falha ao salvar"}`}
      </span>
      {salvamento.status === "erro" && repetir && (
        <button type="button" onClick={repetir} className="text-sm font-medium text-acento underline">
          tentar de novo
        </button>
      )}
    </div>
  );
}

function FaixaModo({ edicao, inativo, tentarEditar }: { edicao: Edicao; inativo: boolean; tentarEditar: () => Promise<void> }) {
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
      <Aviso tom="info" acao={botao("Voltar a editar")}>
        Você saiu da edição por inatividade. Os campos estão em modo leitura.
      </Aviso>
    );
  const { bloqueio } = edicao;
  return (
    <Aviso tom="alerta" acao={botao("Tentar editar")}>
      <span className="inline-flex items-center gap-2">
        <Cadeado />
        {bloqueio
          ? `Em edição por ${bloqueio.nome} desde ${horaCurta(bloqueio.desde)}. Você está em modo leitura.`
          : "Você não está editando este projeto. Modo leitura."}
      </span>
    </Aviso>
  );
}

function NaoSalvos({ itens, descartar }: { itens: NaoSalvo[]; descartar: (id: number) => void }) {
  return (
    <Aviso tom="erro">
      <p className="font-semibold">Estas alterações não foram salvas (outra pessoa assumiu a edição):</p>
      <ul className="mt-2 flex flex-col gap-2">
        {itens.map((n) => (
          <li key={n.id} className="flex flex-wrap items-start gap-2">
            <span className="font-medium">{n.descricao}</span>
            {n.valor !== undefined && (
              <>
                <span className="max-w-xl truncate font-mono text-xs text-tinta-suave">{n.valor}</span>
                <Botao tamanho="sm" onClick={() => void navigator.clipboard.writeText(n.valor ?? "")}>
                  Copiar
                </Botao>
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

function Renomear({ aberto, aoFechar, projeto, edicao }: { aberto: boolean; aoFechar: () => void; projeto: Projeto; edicao: Edicao }) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const [nome, setNome] = useState(projeto.nome);
  const [slug, setSlug] = useState(projeto.slug);
  const [erros, setErros] = useState<{ nome?: string; slug?: string; geral?: string }>({});

  const fechar = () => {
    setNome(projeto.nome);
    setSlug(projeto.slug);
    setErros({});
    aoFechar();
  };

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
        navigate(pathname.replace(`/projetos/${projeto.slug}`, `/projetos/${novo.slug}`), { replace: true });
      }
    } catch (e) {
      if (ehErroApi(e) && e.campo === "slug") setErros({ slug: e.message });
      else setErros({ geral: mensagemDeErro(e) });
    }
  };

  return (
    <Dialogo
      aberto={aberto}
      aoFechar={fechar}
      titulo="Renomear projeto"
      acoes={
        <>
          <Botao onClick={fechar}>Cancelar</Botao>
          <Botao type="submit" form="form-renomear" variante="primario">
            Salvar
          </Botao>
        </>
      }
    >
      <form id="form-renomear" noValidate onSubmit={enviar} className="flex flex-col gap-4">
        <CampoTexto rotulo="Nome" value={nome} erro={erros.nome} onChange={(e) => setNome(e.target.value)} />
        <CampoTexto
          rotulo="Identificador (slug)"
          value={slug}
          erro={erros.slug}
          ajuda="Mudar o identificador muda a URL do projeto."
          onChange={(e) => setSlug(e.target.value)}
        />
        {erros.geral && (
          <p role="alert" className="text-sm text-erro">
            {erros.geral}
          </p>
        )}
      </form>
    </Dialogo>
  );
}
