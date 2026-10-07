import { useQueryClient } from "@tanstack/react-query";
import { useId, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import {
  ANOS_PADRAO,
  ETAPAS,
  rotuloAno,
  Revista,
  Slug,
  type Ano,
  type OrigemProjeto,
  type ProjetoResumo,
} from "../contrato/schemas";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Field,
  FieldContent,
  FieldDescription,
  FieldError,
  FieldGroup,
  FieldLabel,
  FieldLegend,
  FieldSet,
  FieldTitle,
} from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Spinner } from "@/components/ui/spinner";
import { Aviso, Botao, CampoTexto, Dialogo } from "../ui";
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
  { tipo: "vazio", rotulo: "Vazio", ajuda: "Anos sem descritores, escala de 0 a 500." },
  {
    tipo: "importar",
    rotulo: "Importar arquivo",
    ajuda: "Um .json exportado (ou o descritores.json antigo).",
  },
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
  const id = useId();
  const [nome, setNome] = useState("");
  const [slug, setSlug] = useState("");
  const [slugEditado, setSlugEditado] = useState(false);
  const [tipo, setTipo] = useState<TipoOrigem>("vazio");
  const [anos, setAnos] = useState<Ano[]>([...ANOS_PADRAO]);
  const [revista, setRevista] = useState<Revista | null>(null);
  const [de, setDe] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);

  // Zera o formulário ao REABRIR: ao fechar, o conteúdo fica intacto durante a animação de saída.
  const [abertoAntes, setAbertoAntes] = useState(aberto);
  if (aberto !== abertoAntes) {
    setAbertoAntes(aberto);
    if (aberto) {
      setNome("");
      setSlug("");
      setSlugEditado(false);
      setTipo("vazio");
      setAnos([...ANOS_PADRAO]);
      setRevista(null);
      setDe("");
      setErros({});
    }
  }
  const fechar = aoFechar;

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
    if (tipo === "importar")
      return revista ? { tipo, revista } : (erros.origem ?? "Escolha um arquivo .json.");
    return de ? { tipo, de } : "Escolha o projeto a copiar.";
  };

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault();
    const novos: Erros = {};
    if (!nome.trim()) novos.nome = "Informe o nome";
    const slugValido = Slug.safeParse(slug);
    if (!slugValido.success)
      novos.slug = slugValido.error.issues[0]?.message ?? "Identificador inválido";
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
      bloqueado={enviando}
      acoes={
        <>
          <Botao onClick={fechar} disabled={enviando}>
            Cancelar
          </Botao>
          <Botao type="submit" form="form-novo-projeto" variante="primario" disabled={enviando}>
            {enviando && <Spinner data-icon="inline-start" aria-label="Criando" />}
            Criar projeto
          </Botao>
        </>
      }
    >
      <form id="form-novo-projeto" noValidate onSubmit={enviar}>
        <FieldGroup>
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

          <FieldSet data-invalid={erros.origem ? true : undefined}>
            <FieldLegend id={`${id}-origem`} variant="label">
              Origem
            </FieldLegend>
            <RadioGroup
              aria-labelledby={`${id}-origem`}
              aria-invalid={erros.origem ? true : undefined}
              aria-describedby={erros.origem ? `${id}-origem-erro` : undefined}
              value={tipo}
              onValueChange={(v) => {
                setTipo(v as TipoOrigem);
                setErros((e) => ({ ...e, origem: undefined }));
              }}
              className="grid-cols-[repeat(auto-fit,minmax(10rem,1fr))] gap-2"
            >
              {ORIGENS.map((op) => (
                <FieldLabel key={op.tipo} htmlFor={`${id}-${op.tipo}`}>
                  <Field orientation="horizontal">
                    <RadioGroupItem value={op.tipo} id={`${id}-${op.tipo}`} />
                    <FieldContent>
                      <FieldTitle>{op.rotulo}</FieldTitle>
                      <FieldDescription>{op.ajuda}</FieldDescription>
                    </FieldContent>
                  </Field>
                </FieldLabel>
              ))}
            </RadioGroup>

            {tipo === "vazio" && (
              <FieldSet>
                <FieldLegend variant="label">Anos</FieldLegend>
                <FieldGroup
                  data-slot="checkbox-group"
                  className="grid grid-cols-3 gap-3"
                >
                  {ETAPAS.map((ano) => (
                    <Field key={ano} orientation="horizontal">
                      <Checkbox
                        id={`${id}-ano-${ano}`}
                        checked={anos.includes(ano)}
                        onCheckedChange={(marcado) =>
                          setAnos((atual) =>
                            marcado === true
                              ? ETAPAS.filter((a) => a === ano || atual.includes(a))
                              : atual.filter((a) => a !== ano),
                          )
                        }
                      />
                      <FieldLabel htmlFor={`${id}-ano-${ano}`} className="font-normal">
                        {rotuloAno(ano)}
                      </FieldLabel>
                    </Field>
                  ))}
                </FieldGroup>
              </FieldSet>
            )}
            {tipo === "importar" && (
              <Field>
                <FieldLabel htmlFor={`${id}-arquivo`}>Arquivo .json</FieldLabel>
                <Input
                  id={`${id}-arquivo`}
                  type="file"
                  accept="application/json,.json"
                  onChange={(e) => void escolherArquivo(e.target.files?.[0])}
                />
                {revista && <FieldDescription>Arquivo válido.</FieldDescription>}
              </Field>
            )}
            {tipo === "copiar" && (
              <Field>
                <FieldLabel htmlFor={`${id}-de`}>Projeto de origem</FieldLabel>
                <NativeSelect
                  id={`${id}-de`}
                  className="w-full"
                  value={de}
                  onChange={(e) => setDe(e.target.value)}
                >
                  <NativeSelectOption value="">Escolha…</NativeSelectOption>
                  {projetos.map((p) => (
                    <NativeSelectOption key={p.slug} value={p.slug}>
                      {p.nome} ({p.slug})
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
              </Field>
            )}
            {erros.origem && <FieldError id={`${id}-origem-erro`}>{erros.origem}</FieldError>}
          </FieldSet>

          {erros.geral && <Aviso tom="erro">{erros.geral}</Aviso>}
        </FieldGroup>
      </form>
    </Dialogo>
  );
}
