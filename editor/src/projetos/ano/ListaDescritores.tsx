import { useState, type FormEvent } from "react";
import { NavLink, useNavigate } from "react-router";
import { Codigo, ROTULO_ANO, type AnoProjeto, type Descritor } from "../../contrato/schemas";
import { Aviso, Botao, CampoTexto, Confirmacao, Dialogo } from "../../ui";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import {
  caminhoAno,
  caminhoDescritor,
  mensagemDeErro,
  proximoCodigo,
  trocarDescritores,
} from "./dados";

const normalizar = (s: string) =>
  s
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();

const casa = (d: Descritor, busca: string) =>
  normalizar(`${d.codigo} ${d.topic} ${d.description}`).includes(normalizar(busca.trim()));

/** Lista de descritores do ano: busca, criar, duplicar e excluir. */
export function ListaDescritores({ ano, codigoAtual }: { ano: AnoProjeto; codigoAtual?: string }) {
  const { slug, modo, salvar } = useEdicao();
  const navigate = useNavigate();
  const [busca, setBusca] = useState("");
  const [duplicando, setDuplicando] = useState<Descritor>();
  const [excluindo, setExcluindo] = useState<Descritor>();
  const [erro, setErro] = useState<string>();
  const editavel = modo === "edicao";
  const livre = proximoCodigo(ano.descritores);
  const visiveis = ano.descritores.filter((d) => casa(d, busca));

  async function criar() {
    if (!livre) return;
    setErro(undefined);
    try {
      await salvar({
        descricao: `Criar ${livre} no ${ROTULO_ANO[ano.ano]}`,
        executar: () => projetosApi.criarDescritor(slug, ano.ano, { codigo: livre }),
        aplicar: (p, novo) => trocarDescritores(p, ano.ano, (ds) => [...ds, novo]),
      });
      navigate(caminhoDescritor(slug, ano.ano, livre));
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }

  async function excluir(d: Descritor) {
    setExcluindo(undefined);
    setErro(undefined);
    try {
      await salvar({
        descricao: `Excluir ${d.codigo} do ${ROTULO_ANO[ano.ano]}`,
        executar: () => projetosApi.excluirDescritor(slug, ano.ano, d.codigo),
        aplicar: (p) =>
          trocarDescritores(p, ano.ano, (ds) => ds.filter((x) => x.codigo !== d.codigo)),
      });
      if (codigoAtual === d.codigo) navigate(caminhoAno(slug, ano.ano));
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }

  return (
    <nav aria-label={`Descritores do ${ROTULO_ANO[ano.ano]}`} className="flex flex-col gap-3">
      <div className="flex items-end gap-2">
        <div className="flex-1">
          <CampoTexto
            rotulo="Buscar descritor"
            type="search"
            placeholder="Código, tópico ou descrição"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
        </div>
        <Botao variante="primario" disabled={!editavel || !livre} onClick={() => void criar()}>
          + Descritor
        </Botao>
      </div>
      {erro && <Aviso tom="erro">{erro}</Aviso>}

      <p className="text-xs text-tinta-suave" aria-live="polite">
        {visiveis.length} de {ano.descritores.length} descritores
      </p>
      <ul className="flex flex-col divide-y divide-linha overflow-hidden rounded-md border border-linha bg-superficie">
        {visiveis.map((d) => (
          <li key={d.codigo} className="group flex items-stretch">
            <NavLink
              to={caminhoDescritor(slug, ano.ano, d.codigo)}
              className={({ isActive }) =>
                `flex min-w-0 flex-1 gap-3 px-3 py-2 hover:bg-papel ${isActive ? "bg-acento-claro" : ""}`
              }
            >
              <span className="font-mono text-sm font-semibold text-acento">{d.codigo}</span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm">{d.description || "Sem descrição"}</span>
                <span className="block truncate text-xs text-tinta-suave">
                  {d.topic || "Sem tópico"}
                </span>
              </span>
            </NavLink>
            <div className="flex items-center pr-1">
              <Botao
                tamanho="sm"
                variante="fantasma"
                aria-label={`Duplicar ${d.codigo}`}
                title="Duplicar"
                disabled={!editavel || !livre}
                onClick={() => setDuplicando(d)}
              >
                ⧉
              </Botao>
              <Botao
                tamanho="sm"
                variante="fantasma"
                aria-label={`Excluir ${d.codigo}`}
                title="Excluir"
                disabled={!editavel}
                onClick={() => setExcluindo(d)}
              >
                ×
              </Botao>
            </div>
          </li>
        ))}
        {visiveis.length === 0 && (
          <li className="px-3 py-4 text-sm text-tinta-suave">Nenhum descritor encontrado.</li>
        )}
      </ul>

      {duplicando && (
        <DialogoDuplicar
          key={duplicando.codigo}
          ano={ano}
          origem={duplicando}
          sugestao={livre ?? ""}
          aoFechar={() => setDuplicando(undefined)}
        />
      )}
      <Confirmacao
        aberto={Boolean(excluindo)}
        titulo={`Excluir ${excluindo?.codigo ?? ""}?`}
        mensagem="O descritor e toda a sua escala serão removidos deste ano."
        aoCancelar={() => setExcluindo(undefined)}
        aoConfirmar={() => excluindo && void excluir(excluindo)}
      />
    </nav>
  );
}

function DialogoDuplicar(props: {
  ano: AnoProjeto;
  origem: Descritor;
  sugestao: string;
  aoFechar: () => void;
}) {
  const { ano, origem, aoFechar } = props;
  const { slug, salvar } = useEdicao();
  const navigate = useNavigate();
  const [codigo, setCodigo] = useState(props.sugestao);
  const [erro, setErro] = useState<string>();

  async function enviar(e: FormEvent) {
    e.preventDefault();
    const novo = codigo.trim().toUpperCase();
    const valido = Codigo.safeParse(novo);
    if (!valido.success) return setErro(valido.error.issues[0]?.message);
    if (ano.descritores.some((d) => d.codigo === novo))
      return setErro("Esse código já existe neste ano");
    try {
      await salvar({
        descricao: `Duplicar ${origem.codigo} como ${novo} no ${ROTULO_ANO[ano.ano]}`,
        executar: () => projetosApi.criarDescritor(slug, ano.ano, { ...origem, codigo: novo }),
        aplicar: (p, criado) => trocarDescritores(p, ano.ano, (ds) => [...ds, criado]),
      });
      aoFechar();
      navigate(caminhoDescritor(slug, ano.ano, novo));
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }

  return (
    <Dialogo
      aberto
      aoFechar={aoFechar}
      titulo={`Duplicar ${origem.codigo}`}
      acoes={
        <>
          <Botao onClick={aoFechar}>Cancelar</Botao>
          <Botao variante="primario" type="submit" form="form-duplicar">
            Duplicar
          </Botao>
        </>
      }
    >
      <form
        id="form-duplicar"
        onSubmit={(e) => void enviar(e)}
        className="flex flex-col gap-2 [&_input]:font-mono"
      >
        <p className="text-sm text-tinta-suave">
          A cópia leva tópico, descrição, pré-requisitos, BNCC e a escala inteira.
        </p>
        <CampoTexto
          rotulo="Novo código"
          value={codigo}
          erro={erro}
          autoFocus
          onChange={(e) => setCodigo(e.target.value)}
        />
      </form>
    </Dialogo>
  );
}
