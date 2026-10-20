import { useQueryClient } from "@tanstack/react-query";
import { Palette } from "lucide-react";
import { useId, useState, type CSSProperties, type FormEvent } from "react";
import { chaves } from "../api/chaves";
import {
  CORES_PADRAO,
  CorHex,
  mesmasCores,
  type Cores,
  type Projeto,
  type ProjetoResumo,
} from "../contrato/schemas";
import { Botao, CampoTexto, Dialogo } from "../ui";
import { Button } from "@/components/ui/button";
import { Field, FieldDescription, FieldError, FieldGroup, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { Spinner } from "@/components/ui/spinner";
import { projetosApi } from "./api";
import { useEdicao } from "./edicao";
import { mensagemDeErro } from "./formato";
import { useProjetos } from "./consultas";

const PADROES = ["padrao-1", "padrao-2", "padrao-3", "padrao-4"] as const;
const rotuloPadrao = (p: (typeof PADROES)[number]) => `Padrão 0${p.slice(-1)}`;

/** Esquemas distintos (por `mesmasCores`) dos OUTROS projetos; o rótulo lista quem usa cada um. */
export function esquemasDeCores(
  projetos: ProjetoResumo[],
  slugAtual: string,
): { rotulo: string; cores: Cores }[] {
  const esquemas: { nomes: string[]; cores: Cores }[] = [];
  for (const p of projetos) {
    if (p.slug === slugAtual || !p.cores) continue;
    const existente = esquemas.find((e) => mesmasCores(e.cores, p.cores));
    if (existente) existente.nomes.push(p.nome);
    else esquemas.push({ nomes: [p.nome], cores: p.cores });
  }
  return esquemas.map((e) => ({ rotulo: e.nomes.join(", "), cores: e.cores }));
}

/** Variáveis CSS que as tarjas `bg-padrao-N` do editor leem; o `-bg` é a cor a 10% (regra da revista). */
export function estiloCores(cores: Cores | null): CSSProperties {
  if (!cores) return {};
  const estilo: Record<string, string> = {};
  for (const p of PADROES) {
    const hex = cores[p];
    const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));
    estilo[`--color-${p}`] = hex;
    estilo[`--color-${p}-bg`] = `rgba(${r}, ${g}, ${b}, 0.1)`;
  }
  return estilo;
}

type Campos = Record<(typeof PADROES)[number], string>;
type Erros = Partial<Record<(typeof PADROES)[number] | "geral", string>>;

/** Botão "Cores" do cabeçalho + diálogo para editar as 4 cores dos padrões do projeto. */
export function CoresPadroes({ projeto }: { projeto: Projeto }) {
  const edicao = useEdicao();
  const queryClient = useQueryClient();
  const id = useId();
  const projetos = useProjetos();
  const atuais: Campos = { ...(projeto.cores ?? CORES_PADRAO) };
  const [aberto, setAberto] = useState(false);
  const [campos, setCampos] = useState<Campos>(atuais);
  const [erros, setErros] = useState<Erros>({});
  const [enviando, setEnviando] = useState(false);
  const esquemas = esquemasDeCores(projetos.data ?? [], projeto.slug);

  const abrir = () => {
    setCampos(atuais);
    setErros({});
    setAberto(true);
  };

  const salvar = async (cores: Cores | null) => {
    setEnviando(true);
    try {
      await edicao.salvar({
        descricao: "Cores dos padrões",
        executar: () => projetosApi.atualizar(projeto.slug, { cores }),
        aplicar: (_, resposta) => resposta,
      });
      void queryClient.invalidateQueries({ queryKey: chaves.projetos, exact: true });
      setAberto(false);
    } catch (e) {
      setErros({ geral: mensagemDeErro(e) });
    } finally {
      setEnviando(false);
    }
  };

  const enviar = (evento: FormEvent) => {
    evento.preventDefault();
    const novos: Erros = {};
    for (const p of PADROES) {
      const r = CorHex.safeParse(campos[p]);
      if (!r.success) novos[p] = r.error.issues[0]?.message;
    }
    setErros(novos);
    if (Object.keys(novos).length) return;
    void salvar(campos);
  };

  const mudar = (p: (typeof PADROES)[number], valor: string) => {
    setCampos((c) => ({ ...c, [p]: valor }));
    setErros((e) => ({ ...e, [p]: undefined }));
  };

  return (
    <>
      <Button
        type="button"
        variant="outline"
        size="sm"
        disabled={edicao.modo !== "edicao"}
        onClick={abrir}
      >
        <Palette data-icon="inline-start" />
        Cores
      </Button>
      <Dialogo
        aberto={aberto}
        aoFechar={() => setAberto(false)}
        titulo="Cores dos padrões"
        bloqueado={enviando}
        acoes={
          <>
            <Botao onClick={() => void salvar(null)} disabled={enviando}>
              Restaurar padrão
            </Botao>
            <Botao onClick={() => setAberto(false)} disabled={enviando}>
              Cancelar
            </Botao>
            <Botao type="submit" form={`${id}-form`} variante="primario" disabled={enviando}>
              {enviando && <Spinner data-icon="inline-start" />}
              Salvar
            </Botao>
          </>
        }
      >
        <form id={`${id}-form`} noValidate onSubmit={enviar}>
          <FieldGroup>
            {esquemas.length > 0 && (
              <Field>
                <FieldLabel htmlFor={`${id}-esquema`}>Usar esquema de…</FieldLabel>
                <NativeSelect
                  id={`${id}-esquema`}
                  className="w-full"
                  value=""
                  onChange={(e) => {
                    const esquema = esquemas.find((x) => x.rotulo === e.target.value);
                    if (esquema) {
                      setCampos({ ...esquema.cores });
                      setErros({});
                    }
                  }}
                >
                  <NativeSelectOption value="">Escolha…</NativeSelectOption>
                  {esquemas.map((x) => (
                    <NativeSelectOption key={x.rotulo} value={x.rotulo}>
                      {x.rotulo}
                    </NativeSelectOption>
                  ))}
                </NativeSelect>
                <FieldDescription>
                  Copia as 4 cores de outro projeto para os campos.
                </FieldDescription>
              </Field>
            )}
            {PADROES.map((p) => (
              <div key={p} className="flex items-end gap-3">
                <Input
                  type="color"
                  aria-label={`${rotuloPadrao(p)} (seletor)`}
                  className="h-9 w-12 shrink-0 cursor-pointer p-1"
                  value={CorHex.safeParse(campos[p]).success ? campos[p].toLowerCase() : "#000000"}
                  onChange={(e) => mudar(p, e.target.value)}
                />
                <div className="min-w-0 flex-1">
                  <CampoTexto
                    rotulo={rotuloPadrao(p)}
                    value={campos[p]}
                    erro={erros[p]}
                    spellCheck={false}
                    onChange={(e) => mudar(p, e.target.value)}
                  />
                </div>
              </div>
            ))}
            {erros.geral && <FieldError>{erros.geral}</FieldError>}
          </FieldGroup>
        </form>
      </Dialogo>
    </>
  );
}
