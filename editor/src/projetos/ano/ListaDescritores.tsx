import { useRef, useState, type FormEvent, type ReactNode } from "react";
import { Copy, Search, SearchX, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Empty, EmptyDescription, EmptyHeader, EmptyMedia } from "@/components/ui/empty";
import { InputGroup, InputGroupAddon, InputGroupInput } from "@/components/ui/input-group";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import { NavLink, useNavigate } from "react-router";
import { Codigo, rotuloAno, type AnoProjeto, type Descritor } from "../../contrato/schemas";
import { Spinner } from "@/components/ui/spinner";
import { Aviso, Botao, CampoTexto, Confirmacao, Dialogo, useUltimo } from "../../ui";
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
  const [excluindoPendente, setExcluindoPendente] = useState(false);
  const [erro, setErro] = useState<string>();
  const exibidoExcluir = useUltimo(excluindo ?? null);
  const campoBusca = useRef<HTMLInputElement>(null);
  const editavel = modo === "edicao";
  const livre = proximoCodigo(ano.descritores);
  const visiveis = ano.descritores.filter((d) => casa(d, busca));

  async function criar() {
    if (!livre) return;
    setErro(undefined);
    try {
      await salvar({
        descricao: `Criar ${livre} no ${rotuloAno(ano.ano)}`,
        executar: () => projetosApi.criarDescritor(slug, ano.ano, { codigo: livre }),
        aplicar: (p, novo) => trocarDescritores(p, ano.ano, (ds) => [...ds, novo]),
      });
      navigate(caminhoDescritor(slug, ano.ano, livre));
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }

  async function excluir(d: Descritor) {
    setErro(undefined);
    setExcluindoPendente(true);
    try {
      await salvar({
        descricao: `Excluir ${d.codigo} do ${rotuloAno(ano.ano)}`,
        executar: () => projetosApi.excluirDescritor(slug, ano.ano, d.codigo),
        aplicar: (p) =>
          trocarDescritores(p, ano.ano, (ds) => ds.filter((x) => x.codigo !== d.codigo)),
      });
      if (codigoAtual === d.codigo) navigate(caminhoAno(slug, ano.ano));
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setExcluindoPendente(false);
      setExcluindo(undefined);
    }
  }

  return (
    <nav aria-label={`Descritores do ${rotuloAno(ano.ano)}`} className="flex flex-col gap-3">
      <div className="flex items-center gap-2">
        <InputGroup className="flex-1">
          <InputGroupAddon>
            <Search />
          </InputGroupAddon>
          <InputGroupInput
            ref={campoBusca}
            aria-label="Buscar descritor"
            type="search"
            placeholder="Código ou texto"
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
          />
        </InputGroup>
        <Button type="button" disabled={!editavel || !livre} onClick={() => void criar()}>
          + Descritor
        </Button>
      </div>
      {erro && <Aviso tom="erro">{erro}</Aviso>}

      <p className="text-xs text-muted-foreground tabular-nums" aria-live="polite">
        {visiveis.length} de {ano.descritores.length} descritores
      </p>
      {visiveis.length === 0 ? (
        <Empty className="border p-6">
          <EmptyHeader>
            <EmptyMedia variant="icon">
              <SearchX />
            </EmptyMedia>
            <EmptyDescription>Nenhum descritor encontrado.</EmptyDescription>
          </EmptyHeader>
        </Empty>
      ) : (
        <ul className="flex flex-col gap-0.5">
          {visiveis.map((d) => (
            <li
              key={d.codigo}
              className="group relative flex animate-entra items-center rounded-md"
            >
              <NavLink
                to={caminhoDescritor(slug, ano.ano, d.codigo)}
                className={({ isActive }) =>
                  cn(
                    "flex min-w-0 flex-1 gap-3 rounded-md px-3 py-2 transition-colors duration-150 ease-saida hover:bg-muted/60",
                    "focus-visible:ring-3 focus-visible:ring-ring focus-visible:outline-none",
                    "before:absolute before:inset-y-2 before:left-0 before:w-px before:rounded-full before:bg-primary before:opacity-0 before:transition-opacity",
                    isActive && "bg-muted before:opacity-100",
                  )
                }
              >
                <span className="text-sm font-semibold tabular-nums">{d.codigo}</span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-sm">{d.description || "Sem descrição"}</span>
                  <span className="block truncate text-xs text-muted-foreground">
                    {d.topic || "Sem tópico"}
                  </span>
                </span>
              </NavLink>
              <div className="flex items-center opacity-0 transition-opacity duration-150 ease-saida group-focus-within:opacity-100 group-hover:opacity-100 [@media(hover:none)]:opacity-100">
                <AcaoItem
                  rotulo={`Duplicar ${d.codigo}`}
                  dica="Duplicar com outro código"
                  disabled={!editavel || !livre}
                  onClick={() => setDuplicando(d)}
                >
                  <Copy />
                </AcaoItem>
                <AcaoItem
                  rotulo={`Excluir ${d.codigo}`}
                  dica="Excluir com a escala"
                  disabled={!editavel}
                  onClick={() => setExcluindo(d)}
                >
                  <Trash2 />
                </AcaoItem>
              </div>
            </li>
          ))}
        </ul>
      )}

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
        titulo={`Excluir ${exibidoExcluir?.codigo ?? ""}?`}
        mensagem="O descritor e toda a sua escala serão removidos deste ano."
        pendente={excluindoPendente}
        focoAoFechar={campoBusca}
        aoCancelar={() => setExcluindo(undefined)}
        aoConfirmar={() => excluindo && void excluir(excluindo)}
      />
    </nav>
  );
}

/** Botão só com ícone + dica. */
function AcaoItem(props: {
  rotulo: string;
  dica: string;
  disabled: boolean;
  onClick: () => void;
  children: ReactNode;
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          type="button"
          variant="ghost"
          size="icon"
          aria-label={props.rotulo}
          disabled={props.disabled}
          onClick={props.onClick}
        >
          {props.children}
        </Button>
      </TooltipTrigger>
      <TooltipContent>{props.dica}</TooltipContent>
    </Tooltip>
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
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: FormEvent) {
    e.preventDefault();
    const novo = codigo.trim().toUpperCase();
    const valido = Codigo.safeParse(novo);
    if (!valido.success) return setErro(valido.error.issues[0]?.message);
    if (ano.descritores.some((d) => d.codigo === novo))
      return setErro("Esse código já existe neste ano");
    setEnviando(true);
    try {
      await salvar({
        descricao: `Duplicar ${origem.codigo} como ${novo} no ${rotuloAno(ano.ano)}`,
        executar: () => projetosApi.criarDescritor(slug, ano.ano, { ...origem, codigo: novo }),
        aplicar: (p, criado) => trocarDescritores(p, ano.ano, (ds) => [...ds, criado]),
      });
      aoFechar();
      navigate(caminhoDescritor(slug, ano.ano, novo));
    } catch (e) {
      setErro(mensagemDeErro(e));
    } finally {
      setEnviando(false);
    }
  }

  return (
    <Dialogo
      aberto
      aoFechar={aoFechar}
      titulo={`Duplicar ${origem.codigo}`}
      bloqueado={enviando}
      acoes={
        <>
          <Botao onClick={aoFechar} disabled={enviando}>
            Cancelar
          </Botao>
          <Botao variante="primario" type="submit" form="form-duplicar" disabled={enviando}>
            {enviando && <Spinner data-icon="inline-start" />}
            Duplicar
          </Botao>
        </>
      }
    >
      <form id="form-duplicar" onSubmit={(e) => void enviar(e)} className="flex flex-col gap-3">
        <p className="text-sm text-muted-foreground">
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
