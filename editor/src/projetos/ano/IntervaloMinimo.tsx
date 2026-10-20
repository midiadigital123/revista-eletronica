import { useId, useState } from "react";
import { Plus } from "lucide-react";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import {
  linhasVaziasDoPasso,
  PADROES,
  problemasDoPasso,
  type AnoProjeto,
  type Caderno,
} from "../../contrato/schemas";
import { ehErroApi } from "../../api/client";
import { Aviso, Botao, Confirmacao } from "../../ui";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import { mensagemDeErro, rotuloAnoCaderno, trocarAno } from "./dados";

const plural = (n: number, um: string, varios: string) => `${n} ${n === 1 ? um : varios}`;

/** Linhas que faltam para completar a grade do passo: total e quantos descritores ganham ao menos uma. */
function contarLinhas(ano: AnoProjeto) {
  let linhas = 0;
  let descritores = 0;
  for (const d of ano.descritores) {
    const nova = linhasVaziasDoPasso(ano, d.scale);
    const criadas = PADROES.reduce((s, p) => s + nova[p].length - d.scale[p].length, 0);
    linhas += criadas;
    if (criadas > 0) descritores++;
  }
  return { linhas, descritores };
}

/** Intervalo mínimo (passo) do ano e geração das linhas vazias da grade. Salva ao sair do campo. */
export function IntervaloMinimo({ caderno, ano }: { caderno: Caderno; ano: AnoProjeto }) {
  const { slug, salvar } = useEdicao();
  const id = useId();
  const [valor, setValor] = useState(ano.passo === undefined ? "" : String(ano.passo));
  const [erro, setErro] = useState<string>();
  // Contagem fixada ao abrir: o ano muda durante a geração e o título não pode piscar "0 linhas".
  const [confirmando, setConfirmando] = useState<{ linhas: number; descritores: number } | null>(
    null,
  );
  const [pendente, setPendente] = useState(false);
  const [falha, setFalha] = useState<string>();

  async function confirmar(textoInvalido: boolean) {
    // input number com texto inválido reporta value "": não é "limpar o passo".
    if (textoInvalido) return setErro("Use um número inteiro");
    const texto = valor.trim();
    const passo = texto === "" ? undefined : Number(texto);
    if (passo !== undefined && (!Number.isInteger(passo) || passo < 1))
      return setErro("Use um número inteiro");
    const problema = problemasDoPasso(passo, ano.scaleRange)[0];
    if (problema) return setErro(problema.erro);
    setErro(undefined);
    if (passo === ano.passo) return;

    try {
      await salvar({
        descricao: `Intervalo mínimo do ${rotuloAnoCaderno(caderno, ano.ano)}`,
        valor: String(passo ?? ""),
        executar: () => projetosApi.atualizarAno(slug, caderno, ano.ano, { passo: passo ?? null }),
        aplicar: (p, resposta) => trocarAno(p, caderno, ano.ano, () => resposta),
      });
    } catch (e) {
      if (ehErroApi(e, 400) && e.campo === "passo") setErro(e.message);
      else setErro(mensagemDeErro(e));
    }
  }

  async function gerar() {
    setPendente(true);
    setFalha(undefined);
    try {
      await salvar({
        descricao: `Linhas vazias do ${rotuloAnoCaderno(caderno, ano.ano)}`,
        executar: () => projetosApi.gerarLinhas(slug, caderno, ano.ano),
        aplicar: (p, resposta) => trocarAno(p, caderno, ano.ano, () => resposta),
      });
    } catch (e) {
      setFalha(mensagemDeErro(e));
    } finally {
      setPendente(false);
      setConfirmando(null);
    }
  }

  const { linhas, descritores } =
    ano.passo === undefined ? { linhas: 0, descritores: 0 } : contarLinhas(ano);
  const idErro = `${id}-erro`;

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-end gap-3">
        <Field data-invalid={erro ? true : undefined} className="w-40 gap-1.5">
          <FieldLabel htmlFor={id}>Intervalo mínimo</FieldLabel>
          <Input
            id={id}
            type="number"
            step={1}
            min={1}
            inputMode="numeric"
            className="tabular-nums"
            aria-invalid={Boolean(erro)}
            aria-describedby={erro ? idErro : undefined}
            value={valor}
            onChange={(e) => setValor(e.target.value)}
            onBlur={(e) => void confirmar(e.currentTarget.validity.badInput)}
          />
        </Field>
        <Botao
          disabled={ano.passo === undefined || linhas === 0}
          onClick={() => setConfirmando({ linhas, descritores })}
        >
          <Plus data-icon="inline-start" />
          Gerar linhas vazias
        </Botao>
        {ano.passo !== undefined && linhas === 0 && (
          <p className="pb-2 text-sm text-muted-foreground">Nenhuma linha a criar</p>
        )}
      </div>
      {erro && <FieldError id={idErro}>{erro}</FieldError>}
      {falha && <Aviso tom="erro">{falha}</Aviso>}
      <Confirmacao
        aberto={confirmando !== null}
        titulo={`Criar ${plural(confirmando?.linhas ?? linhas, "linha vazia", "linhas vazias")} em ${plural(confirmando?.descritores ?? descritores, "descritor", "descritores")}?`}
        mensagem="As linhas existentes não são alteradas."
        rotuloConfirmar="Criar linhas"
        pendente={pendente}
        aoCancelar={() => setConfirmando(null)}
        aoConfirmar={() => void gerar()}
      />
    </div>
  );
}
