import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import {
  ANOS,
  ROTULO_ANO,
  Revista,
  Slug,
  type Ano,
  type OrigemProjeto,
  type ProjetoResumo,
} from "../contrato/schemas";
import { Botao, CampoTexto, Dialogo } from "../ui";
import { projetosApi } from "./api";
import { mensagemDeErro, sugerirSlug } from "./formato";

type TipoOrigem = OrigemProjeto["tipo"];

interface Erros {
  nome?: string;
  slug?: string;
  origem?: string;
  geral?: string;
}

const ORIGENS: { tipo: TipoOrigem; rotulo: string; ajuda: string }[] = [
  { tipo: "vazio", rotulo: "Vazio", ajuda: "Anos sem descritores, escala 0–500." },
  { tipo: "importar", rotulo: "Importar arquivo", ajuda: "Um .json exportado (ou o descritores.json antigo)." },
  { tipo: "copiar", rotulo: "Copiar projeto", ajuda: "Duplica página, anos e imagens." },
];

/** Lê e valida um .json no formato Revista. Devolve a revista ou uma mensagem clara. */
async function lerRevista(arquivo: File): Promise<Revista | string> {
  let dados: unknown;
  try {
    dados = JSON.parse(await arquivo.text());
  } catch {
    return "O arquivo não é um JSON válido.";
  }
  const r = Revista.safeParse(dados);
  if (r.success) return r.data;
  const problemas = r.error.issues
    .slice(0, 3)
    .map((i) => (i.path.length ? `${i.path.join(".")}: ${i.message}` : i.message));
  return `O arquivo não está no formato da revista. ${problemas.join("; ")}`;
}

/** Diálogo "Novo projeto": cria e já entra no projeto com o bloqueio de edição. */
export function NovoProjeto({
  aberto,
  aoFechar,
  projetos,
}: {
  aberto: boolean;
  aoFechar: () => void;
  projetos: ProjetoResumo[];
}) {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [nome, setNome] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEditado, setSlugEditado] = useState(false);
  const [tipo, setTipo] = useState<TipoOrigem>("vazio");
  const [anos, setAnos] = useState<Ano[]>([...ANOS]);
  const [revista, setRevista] = useState<Revista | null>(null);
  const [de, setDe] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);

  const fechar = () => {
    setNome("");
    setSlug("");
    setSlugEditado(false);
    setTipo("vazio");
    setAnos([...ANOS]);
    setRevista(null);
    setDe("");
    setErros({});
    aoFechar();
  };

  const escolherArquivo = async (arquivo: File | undefined) => {
    setRevista(null);
    if (!arquivo) return;
    const lida = await lerRevista(arquivo);
    if (typeof lida === "string") setErros((e) => ({ ...e, origem: lida }));
    else {
      setRevista(lida);
      setErros((e) => ({ ...e, origem: undefined }));
    }
  };

  const origem = (): OrigemProjeto | string => {
    if (tipo === "vazio") return anos.length ? { tipo, anos } : "Escolha ao menos um ano.";
    if (tipo === "importar") return revista ? { tipo, revista } : (erros.origem ?? "Escolha um arquivo .json.");
    return de ? { tipo, de } : "Escolha o projeto a copiar.";
  };

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault();
    const novos: Erros = {};
    if (!nome.trim()) novos.nome = "Informe o nome";
    const slugValido = Slug.safeParse(slug);
    if (!slugValido.success) novos.slug = slugValido.error.issues[0]?.message ?? "Identificador inválido";
    const o = origem();
    if (typeof o === "string") novos.origem = o;
    setErros(novos);
    if (Object.keys(novos).length || typeof o === "string") return;

    setEnviando(true);
    try {
      const projeto = await projetosApi.criar({ nome: nome.trim(), slug, origem: o });
      queryClient.setQueryData(chaves.projeto(projeto.slug), projeto);
      void queryClient.invalidateQueries({ queryKey: chaves.projetos, exact: true });
      fechar();
      navigate(`/projetos/${projeto.slug}`);
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
      titulo="Novo projeto"
      acoes={
        <>
          <Botao onClick={fechar}>Cancelar</Botao>
          <Botao type="submit" form="form-novo-projeto" variante="primario" disabled={enviando}>
            {enviando ? "Criando…" : "Criar projeto"}
          </Botao>
        </>
      }
    >
      <form id="form-novo-projeto" noValidate onSubmit={enviar} className="flex flex-col gap-4">
        <CampoTexto
          rotulo="Nome"
          value={nome}
          erro={erros.nome}
          autoFocus
          onChange={(e) => {
            setNome(e.target.value);
            if (!slugEditado) setSlug(sugerirSlug(e.target.value));
          }}
        />
        <CampoTexto
          rotulo="Identificador (slug)"
          value={slug}
          erro={erros.slug}
          ajuda="Aparece na URL. Minúsculas, números e hífen."
          onChange={(e) => {
            setSlug(e.target.value);
            setSlugEditado(true);
          }}
        />

        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-sm font-semibold">Origem</legend>
          <div className="grid gap-2 sm:grid-cols-3">
            {ORIGENS.map((op) => (
              <label
                key={op.tipo}
                className="flex cursor-pointer flex-col gap-0.5 rounded-md border border-linha p-3 text-sm has-[:checked]:border-acento has-[:checked]:bg-acento-claro"
              >
                <span className="flex items-center gap-2 font-medium">
                  <input
                    type="radio"
                    name="origem"
                    value={op.tipo}
                    checked={tipo === op.tipo}
                    onChange={() => {
                      setTipo(op.tipo);
                      setErros((e) => ({ ...e, origem: undefined }));
                    }}
                    className="accent-acento"
                  />
                  {op.rotulo}
                </span>
                <span className="text-xs text-tinta-suave">{op.ajuda}</span>
              </label>
            ))}
          </div>

          {tipo === "vazio" && (
            <div role="group" aria-label="Anos" className="flex flex-wrap gap-4 pt-1">
              {ANOS.map((ano) => (
                <label key={ano} className="flex items-center gap-2 font-mono text-sm">
                  <input
                    type="checkbox"
                    className="accent-acento"
                    checked={anos.includes(ano)}
                    onChange={(e) =>
                      setAnos((atual) =>
                        e.target.checked ? ANOS.filter((a) => a === ano || atual.includes(a)) : atual.filter((a) => a !== ano),
                      )
                    }
                  />
                  {ROTULO_ANO[ano]}
                </label>
              ))}
            </div>
          )}
          {tipo === "importar" && (
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-semibold">Arquivo .json</span>
              <input
                type="file"
                accept="application/json,.json"
                onChange={(e) => void escolherArquivo(e.target.files?.[0])}
                className="text-sm file:mr-3 file:rounded-md file:border file:border-linha file:bg-superficie file:px-3 file:py-1.5"
              />
              {revista && <span className="text-xs text-acento">Arquivo válido.</span>}
            </label>
          )}
          {tipo === "copiar" && (
            <label className="flex flex-col gap-1 text-sm">
              <span className="font-semibold">Projeto de origem</span>
              <select
                value={de}
                onChange={(e) => setDe(e.target.value)}
                className="h-10 rounded-md border border-linha bg-superficie px-3"
              >
                <option value="">Escolha…</option>
                {projetos.map((p) => (
                  <option key={p.slug} value={p.slug}>
                    {p.nome} ({p.slug})
                  </option>
                ))}
              </select>
            </label>
          )}
          {erros.origem && (
            <p role="alert" className="text-xs text-erro">
              {erros.origem}
            </p>
          )}
        </fieldset>

        {erros.geral && (
          <p role="alert" className="text-sm text-erro">
            {erros.geral}
          </p>
        )}
      </form>
    </Dialogo>
  );
}
