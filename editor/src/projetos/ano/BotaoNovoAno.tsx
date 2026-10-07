import { useId, useState, type FormEvent } from "react";
import { useNavigate } from "react-router";
import { Ano, ANOS_PADRAO, rotuloAno, type Projeto } from "../../contrato/schemas";
import { Aviso, Botao, Dialogo } from "../../ui";
import { Button } from "@/components/ui/button";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { NativeSelect, NativeSelectOption } from "@/components/ui/native-select";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import { caminhoAno, mensagemDeErro, trocarAnos } from "./dados";

/**
 * Botão "+ Ano" na barra de abas do projeto (renderizado por A6a no
 * ProjetoLayout). Atalhos para as etapas padrão que faltam e um formulário
 * para qualquer etapa (número + EF/EM); cria com faixa e cortes padrão.
 */
export function BotaoNovoAno({ projeto }: { projeto: Projeto }) {
  const { slug, modo, salvar } = useEdicao();
  const navigate = useNavigate();
  const id = useId();
  const [aberto, setAberto] = useState(false);
  const [erro, setErro] = useState<string>();
  const [numero, setNumero] = useState("");
  const [nivel, setNivel] = useState<"ef" | "em">("ef");
  const [erroEtapa, setErroEtapa] = useState<string>();
  const existe = (ano: string) => projeto.anos.some((p) => p.ano === ano);
  const faltam = ANOS_PADRAO.filter((a) => !existe(a));
  const chave = `${numero.trim()}${nivel}`;
  const previa = Ano.safeParse(chave).success ? rotuloAno(chave) : null;

  async function criar(ano: Ano) {
    try {
      await salvar({
        descricao: `Criar ano ${rotuloAno(ano)}`,
        executar: () => projetosApi.criarAno(slug, { ano }),
        aplicar: (p, novo) => trocarAnos(p, (anos) => [...anos, novo]),
      });
      setAberto(false);
      navigate(caminhoAno(slug, ano));
    } catch (e) {
      setErro(mensagemDeErro(e));
    }
  }

  function enviar(e: FormEvent) {
    e.preventDefault();
    const r = Ano.safeParse(chave);
    const problema = !numero.trim()
      ? "Informe o número da etapa"
      : !r.success
        ? r.error.issues[0]?.message
        : existe(r.data)
          ? "Esta etapa já existe no projeto"
          : undefined;
    setErroEtapa(problema);
    if (!problema && r.success) void criar(r.data);
  }

  return (
    <>
      <Button
        type="button"
        size="sm"
        variant="ghost"
        disabled={modo !== "edicao"}
        onClick={() => {
          setErro(undefined);
          setErroEtapa(undefined);
          setNumero("");
          setNivel("ef");
          setAberto(true);
        }}
      >
        + Ano
      </Button>
      <Dialogo
        aberto={aberto}
        aoFechar={() => setAberto(false)}
        titulo="Novo ano"
        acoes={<Botao onClick={() => setAberto(false)}>Cancelar</Botao>}
      >
        <div className="flex flex-col gap-4">
          <p className="text-sm text-muted-foreground">
            O ano começa sem descritores, com a faixa e os cortes padrão. Dá para ajustar depois.
          </p>
          {faltam.length > 0 && (
            /* Grade que cresce com o catálogo de etapas (N anos), sem largura fixa. */
            <ul className="grid grid-cols-[repeat(auto-fill,minmax(7rem,1fr))] gap-2">
              {faltam.map((ano) => (
                <li key={ano}>
                  <Button
                    type="button"
                    variant="outline"
                    className="w-full"
                    onClick={() => void criar(ano)}
                  >
                    {rotuloAno(ano)}
                  </Button>
                </li>
              ))}
            </ul>
          )}
          <form noValidate onSubmit={enviar} className="flex flex-col gap-3">
            <p className="text-sm font-medium">Outra etapa</p>
            <div className="flex items-end gap-2">
              <Field data-invalid={erroEtapa ? true : undefined} className="w-24">
                <FieldLabel htmlFor={`${id}-numero`}>Número</FieldLabel>
                <Input
                  id={`${id}-numero`}
                  type="number"
                  inputMode="numeric"
                  min={1}
                  max={nivel === "em" ? 3 : 9}
                  value={numero}
                  onChange={(e) => setNumero(e.target.value)}
                  aria-invalid={Boolean(erroEtapa)}
                  aria-describedby={erroEtapa ? `${id}-erro` : `${id}-previa`}
                />
              </Field>
              <Field className="w-32">
                <FieldLabel htmlFor={`${id}-nivel`}>Segmento</FieldLabel>
                <NativeSelect
                  id={`${id}-nivel`}
                  className="w-full"
                  value={nivel}
                  onChange={(e) => setNivel(e.target.value as "ef" | "em")}
                >
                  <NativeSelectOption value="ef">EF</NativeSelectOption>
                  <NativeSelectOption value="em">EM</NativeSelectOption>
                </NativeSelect>
              </Field>
              <Button type="submit">Criar</Button>
            </div>
            <p id={`${id}-previa`} className="text-sm text-muted-foreground" aria-live="polite">
              {previa
                ? `Será criado: ${previa}`
                : "Ensino Fundamental: 1 a 9 · Ensino Médio: 1 a 3"}
            </p>
            {erroEtapa && <FieldError id={`${id}-erro`}>{erroEtapa}</FieldError>}
          </form>
          {erro && <Aviso tom="erro">{erro}</Aviso>}
        </div>
      </Dialogo>
    </>
  );
}
