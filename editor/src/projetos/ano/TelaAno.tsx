import { useState } from "react";
import { Outlet, useNavigate } from "react-router";
import { ROTULO_ANO, type AnoProjeto } from "../../contrato/schemas";
import { Aviso, Botao, Confirmacao } from "../../ui";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import { caminhoProjeto, mensagemDeErro, trocarAnos, useAnoAtual } from "./dados";
import { FaixaCortes } from "./FaixaCortes";
import { ListaDescritores } from "./ListaDescritores";

/** Aba de um ano: faixa e cortes, lista de descritores e o descritor aberto (Outlet). */
export function TelaAno() {
  const { consulta, projeto, anoProjeto, codigo } = useAnoAtual();

  if (consulta.isPending) return <p className="p-6 text-tinta-suave">Carregando…</p>;
  if (consulta.isError) return <div className="p-6"><Aviso tom="erro">{mensagemDeErro(consulta.error)}</Aviso></div>;
  if (!projeto || !anoProjeto)
    return (
      <section className="p-6">
        <h1 className="text-2xl">Ano não encontrado</h1>
        <p className="mt-2 text-tinta-suave">Este ano não existe neste projeto.</p>
      </section>
    );

  return (
    <section aria-labelledby="titulo-ano" className="flex flex-col gap-6 p-6">
      <header className="flex flex-col gap-4 border-b border-linha pb-5">
        <div className="flex items-baseline justify-between gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-tinta-suave">Ano escolar</p>
            <h1 id="titulo-ano" className="text-4xl leading-tight">
              {ROTULO_ANO[anoProjeto.ano]}
            </h1>
          </div>
          <ExcluirAno ano={anoProjeto} unico={projeto.anos.length === 1} />
        </div>
        <FieldsetEdicao legenda="Faixa da escala e cortes dos padrões">
          <FaixaCortes key={anoProjeto.ano} ano={anoProjeto} />
        </FieldsetEdicao>
      </header>

      <div className="grid items-start gap-6 lg:grid-cols-[20rem_1fr]">
        <ListaDescritores ano={anoProjeto} codigoAtual={codigo} />
        <div className="min-w-0">
          <Outlet />
        </div>
      </div>
    </section>
  );
}

/** Tela índice do ano, sem descritor selecionado. */
export function SemDescritor() {
  return (
    <p className="rounded-md border border-dashed border-linha p-8 text-center text-tinta-suave">
      Escolha um descritor na lista ou crie um novo.
    </p>
  );
}

/** <fieldset disabled> nativo: fora do modo edição, desabilita todos os controles de dentro. */
export function FieldsetEdicao({ legenda, children }: { legenda: string; children: React.ReactNode }) {
  const { modo } = useEdicao();
  return (
    <fieldset disabled={modo !== "edicao"} className="min-w-0">
      <legend className="mb-2 text-sm font-semibold text-tinta-suave">{legenda}</legend>
      {children}
    </fieldset>
  );
}

function ExcluirAno({ ano, unico }: { ano: AnoProjeto; unico: boolean }) {
  const { slug, modo, salvar } = useEdicao();
  const navigate = useNavigate();
  const [confirmando, setConfirmando] = useState(false);
  const [erro, setErro] = useState<string>();
  const rotulo = ROTULO_ANO[ano.ano];

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
      <Botao
        variante="perigo"
        tamanho="sm"
        disabled={modo !== "edicao" || unico}
        title={unico ? "O projeto precisa ter ao menos um ano" : undefined}
        onClick={() => setConfirmando(true)}
      >
        Excluir ano
      </Botao>
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
