import { useQueryClient } from "@tanstack/react-query";
import { useId, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { chaves } from "../api/chaves";
import { ehErroApi } from "../api/client";
import {
  ANOS_PADRAO,
  compararAnos,
  DISCIPLINAS,
  ETAPAS,
  PDF_MAX_BYTES,
  rotuloAno,
  rotuloDisciplina,
  Slug,
  type Ano,
  type Caderno,
  type Disciplina,
  type OrigemProjeto,
  type ProjetoResumo,
  type ResultadoExtracao,
  type Revista,
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
  disciplinas?: string;
  origem?: string;
  geral?: string;
}

const ORIGENS: { tipo: TipoOrigem; rotulo: string; ajuda: string }[] = [
  { tipo: "vazio", rotulo: "Vazio", ajuda: "Anos sem descritores, escala de 0 a 500." },
  { tipo: "copiar", rotulo: "Copiar projeto", ajuda: "Duplica página, imagens e as disciplinas." },
  { tipo: "importar", rotulo: "Importar PDF", ajuda: "Lê os descritores do PDF da revista." },
];

const LISTA_DISCIPLINAS = Object.keys(DISCIPLINAS) as Disciplina[];

/** Disciplina do extrator que preenche cada caderno (Alfabetização usa as duas do mesmo PDF). */
const FONTE: Record<Caderno, keyof ResultadoExtracao["disciplinas"]> = {
  "lingua-portuguesa": "lingua-portuguesa",
  matematica: "matematica",
  "alfabetizacao-lp": "lingua-portuguesa",
  "alfabetizacao-mat": "matematica",
};

/** PDF lido por disciplina. `arquivo` descarta respostas de um arquivo que já foi trocado. */
type Extracao = { arquivo: File } & (
  | { status: "lendo" }
  | { status: "erro"; erro: string }
  | { status: "ok"; cadernos: Partial<Record<Caderno, Revista>>; anos: Ano[]; avisos: string[] }
);

/** Resultado do extrator → cadernos da disciplina, ou a mensagem do que falta no PDF. */
function cadernosDaExtracao(disciplina: Disciplina, r: ResultadoExtracao) {
  const ids = DISCIPLINAS[disciplina];
  const faltam = [...new Set(ids.map((c) => FONTE[c]).filter((f) => !r.disciplinas[f]))];
  if (faltam.length) return `Este PDF não traz ${faltam.map(rotuloDisciplina).join(" nem ")}`;
  const cadernos: Partial<Record<Caderno, Revista>> = {};
  for (const c of ids) cadernos[c] = r.disciplinas[FONTE[c]];
  const anos = new Set(
    Object.values(cadernos).flatMap((rev) => Object.keys(rev).filter((k) => k !== "pagina")),
  );
  return { cadernos, anos: [...anos].sort(compararAnos) };
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
  const [disciplinas, setDisciplinas] = useState<Disciplina[]>([]);
  const [tipo, setTipo] = useState<TipoOrigem>("vazio");
  const [anos, setAnos] = useState<Ano[]>([...ANOS_PADRAO]);
  const [extracoes, setExtracoes] = useState<Partial<Record<Disciplina, Extracao>>>({});
  const [de, setDe] = useState("");
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);
  const lendo = tipo === "importar" && Object.values(extracoes).some((e) => e?.status === "lendo");

  // Zera o formulário ao REABRIR: ao fechar, o conteúdo fica intacto durante a animação de saída.
  const [abertoAntes, setAbertoAntes] = useState(aberto);
  if (aberto !== abertoAntes) {
    setAbertoAntes(aberto);
    if (aberto) {
      setNome("");
      setSlug("");
      setSlugEditado(false);
      setDisciplinas([]);
      setTipo("vazio");
      setAnos([...ANOS_PADRAO]);
      setExtracoes({});
      setDe("");
      setErros({});
    }
  }
  const fechar = aoFechar;

  const marcarDisciplina = (d: Disciplina, marcado: boolean) => {
    setDisciplinas((atual) =>
      marcado
        ? LISTA_DISCIPLINAS.filter((x) => x === d || atual.includes(x))
        : atual.filter((x) => x !== d),
    );
    // Desmarcar descarta o PDF lido (e uma leitura em andamento vira resposta ignorada).
    if (!marcado)
      setExtracoes((x) => Object.fromEntries(Object.entries(x).filter(([k]) => k !== d)));
    setErros((e) => ({ ...e, disciplinas: undefined }));
  };

  const lerPdf = async (d: Disciplina, arquivo: File | undefined) => {
    if (!arquivo) return setExtracoes((x) => ({ ...x, [d]: undefined }));
    if (arquivo.size > PDF_MAX_BYTES)
      return setExtracoes((x) => ({
        ...x,
        [d]: { arquivo, status: "erro", erro: "O PDF passa de 50 MB." },
      }));
    setExtracoes((x) => ({ ...x, [d]: { arquivo, status: "lendo" } }));
    let nova: Extracao;
    try {
      const resultado = await projetosApi.extrairPdf(arquivo);
      const r = cadernosDaExtracao(d, resultado);
      nova =
        typeof r === "string"
          ? { arquivo, status: "erro", erro: r }
          : { arquivo, status: "ok", ...r, avisos: resultado.avisos };
    } catch (e) {
      nova = { arquivo, status: "erro", erro: mensagemDeErro(e) };
    }
    setExtracoes((x) => (x[d]?.arquivo === arquivo ? { ...x, [d]: nova } : x));
    setErros((e) => ({ ...e, origem: undefined }));
  };

  const origem = (): OrigemProjeto | string => {
    if (tipo === "vazio") return anos.length ? { tipo, anos } : "Escolha ao menos um ano.";
    if (tipo === "copiar") return de ? { tipo, de } : "Escolha o projeto a copiar.";
    const cadernos: Partial<Record<Caderno, Revista>> = {};
    for (const d of disciplinas) {
      const e = extracoes[d];
      if (e?.status !== "ok") return `Escolha um PDF válido para ${rotuloDisciplina(d)}.`;
      Object.assign(cadernos, e.cadernos);
    }
    return { tipo, cadernos };
  };

  const enviar = async (evento: FormEvent) => {
    evento.preventDefault();
    if (lendo) return;
    const novos: Erros = {};
    if (!nome.trim()) novos.nome = "Informe o nome";
    const slugValido = Slug.safeParse(slug);
    if (!slugValido.success)
      novos.slug = slugValido.error.issues[0]?.message ?? "Identificador inválido";
    if (!disciplinas.length) novos.disciplinas = "Escolha ao menos uma disciplina";
    const o = origem();
    if (typeof o === "string") novos.origem = o;
    setErros(novos);
    if (Object.keys(novos).length || typeof o === "string") return;

    setEnviando(true);
    try {
      const projeto = await projetosApi.criar({ nome: nome.trim(), slug, disciplinas, origem: o });
      queryClient.setQueryData(chaves.projeto(projeto.slug), projeto);
      void queryClient.invalidateQueries({ queryKey: chaves.projetos, exact: true });
      fechar();
      navigate(`/projetos/${projeto.slug}`);
    } catch (e) {
      const campo = ehErroApi(e) ? (e.campo ?? "") : "";
      if (campo === "slug") setErros({ slug: mensagemDeErro(e) });
      else if (campo.startsWith("origem.cadernos") || campo.startsWith("disciplinas"))
        setErros({ origem: mensagemDeErro(e) });
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
          <Botao
            type="submit"
            form="form-novo-projeto"
            variante="primario"
            disabled={enviando || lendo}
          >
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

          <FieldSet data-invalid={erros.disciplinas ? true : undefined}>
            <FieldLegend variant="label">Disciplinas</FieldLegend>
            <FieldGroup
              data-slot="checkbox-group"
              className="flex flex-row flex-wrap gap-x-6 gap-y-3"
            >
              {LISTA_DISCIPLINAS.map((d) => (
                <Field key={d} orientation="horizontal" className="w-auto">
                  <Checkbox
                    id={`${id}-disciplina-${d}`}
                    checked={disciplinas.includes(d)}
                    aria-invalid={erros.disciplinas ? true : undefined}
                    aria-describedby={erros.disciplinas ? `${id}-disciplinas-erro` : undefined}
                    onCheckedChange={(marcado) => marcarDisciplina(d, marcado === true)}
                  />
                  <FieldLabel htmlFor={`${id}-disciplina-${d}`} className="font-normal">
                    {rotuloDisciplina(d)}
                  </FieldLabel>
                </Field>
              ))}
            </FieldGroup>
            {erros.disciplinas && (
              <FieldError id={`${id}-disciplinas-erro`}>{erros.disciplinas}</FieldError>
            )}
          </FieldSet>

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
                <FieldGroup data-slot="checkbox-group" className="grid grid-cols-3 gap-3">
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
            {tipo === "importar" &&
              (disciplinas.length ? (
                disciplinas.map((d) => (
                  <CampoPdf
                    key={d}
                    id={`${id}-${d}`}
                    disciplina={d}
                    extracao={extracoes[d]}
                    aoEscolher={(arquivo) => void lerPdf(d, arquivo)}
                  />
                ))
              ) : (
                <FieldDescription>Marque as disciplinas para escolher os PDFs.</FieldDescription>
              ))}
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

/** Um PDF por disciplina: lê ao escolher e mostra os anos achados e os avisos do extrator. */
function CampoPdf({
  id,
  disciplina,
  extracao,
  aoEscolher,
}: {
  id: string;
  disciplina: Disciplina;
  extracao?: Extracao;
  aoEscolher: (arquivo: File | undefined) => void;
}) {
  const rotulo = rotuloDisciplina(disciplina);
  const erro = extracao?.status === "erro" ? extracao.erro : undefined;
  return (
    <div className="flex flex-col gap-3">
      <Field data-invalid={erro ? true : undefined}>
        <FieldLabel htmlFor={`${id}-pdf`}>PDF — {rotulo}</FieldLabel>
        <div className="flex items-center gap-2">
          <Input
            id={`${id}-pdf`}
            type="file"
            accept="application/pdf,.pdf"
            aria-invalid={erro ? true : undefined}
            aria-describedby={erro ? `${id}-pdf-erro` : undefined}
            onChange={(e) => aoEscolher(e.target.files?.[0])}
          />
          {extracao?.status === "lendo" && <Spinner aria-label={`Lendo o PDF de ${rotulo}`} />}
        </div>
        {erro && <FieldError id={`${id}-pdf-erro`}>{erro}</FieldError>}
      </Field>
      {extracao?.status === "ok" && (
        <FieldSet>
          <FieldLegend variant="label">Anos</FieldLegend>
          <FieldGroup data-slot="checkbox-group" className="grid grid-cols-3 gap-3">
            {extracao.anos.map((ano) => (
              <Field key={ano} orientation="horizontal">
                <Checkbox id={`${id}-ano-${ano}`} checked disabled />
                <FieldLabel htmlFor={`${id}-ano-${ano}`} className="font-normal">
                  {rotuloAno(ano)}
                </FieldLabel>
              </Field>
            ))}
          </FieldGroup>
          {extracao.avisos.length > 0 && (
            <ul
              aria-label={`Avisos da leitura de ${rotulo}`}
              className="flex list-disc flex-col gap-1 pl-4 text-xs text-muted-foreground"
            >
              {extracao.avisos.map((aviso, i) => (
                <li key={i}>{aviso}</li>
              ))}
            </ul>
          )}
        </FieldSet>
      )}
    </div>
  );
}
