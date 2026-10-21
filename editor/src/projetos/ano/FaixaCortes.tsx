import { useId, useState } from "react";
import { Field, FieldError } from "@/components/ui/field";
import {
  Padrao,
  PADROES_COM_CORTE,
  problemasDosCortes,
  ScaleRange,
  type AnoProjeto,
  type Caderno,
  type AtualizarAnoEntrada,
  type Cortes,
  type Problema,
} from "../../contrato/schemas";
import { ehErroApi } from "../../api/client";
import { Aviso } from "../../ui";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import { mensagemDeErro, rotuloPadrao, trocarAno, rotuloAnoCaderno } from "./dados";
import { EntradaComOperador } from "./EditorEscala";

const CAMPOS = [
  { chave: "scaleRange.min" },
  { chave: "cortes.padrao-1" },
  { chave: "cortes.padrao-2" },
  { chave: "cortes.padrao-3" },
  { chave: "scaleRange.max" },
] as const;

type Chave = (typeof CAMPOS)[number]["chave"];

/** Cada padrão vai de `inicio` (≥) a `fim` (<; ≤ no 04). O fim de um é o início do próximo: mesma chave. */
const BLOCOS = [
  { padrao: "padrao-1", cor: "bg-padrao-1", inicio: "scaleRange.min", fim: "cortes.padrao-1" },
  { padrao: "padrao-2", cor: "bg-padrao-2", inicio: "cortes.padrao-1", fim: "cortes.padrao-2" },
  { padrao: "padrao-3", cor: "bg-padrao-3", inicio: "cortes.padrao-2", fim: "cortes.padrao-3" },
  { padrao: "padrao-4", cor: "bg-padrao-4", inicio: "cortes.padrao-3", fim: "scaleRange.max" },
] as const satisfies readonly { padrao: Padrao; cor: string; inicio: Chave; fim: Chave }[];
type Valores = Record<Chave, string>;
type Erros = Partial<Record<Chave, string>>;

const ehChave = (campo: string): campo is Chave => CAMPOS.some((c) => c.chave === campo);

const valoresDoAno = (a: AnoProjeto): Valores => ({
  "scaleRange.min": String(a.scaleRange.min),
  "scaleRange.max": String(a.scaleRange.max),
  "cortes.padrao-1": String(a.cortes["padrao-1"]),
  "cortes.padrao-2": String(a.cortes["padrao-2"]),
  "cortes.padrao-3": String(a.cortes["padrao-3"]),
});

/** Converte os textos e aplica as regras do contrato. Sem problemas → faixa e cortes. */
function validar(v: Valores): { problemas: Problema[]; faixa?: ScaleRange; cortes?: Cortes } {
  const n = (c: Chave) => (v[c].trim() === "" ? NaN : Number(v[c]));
  const naoInteiros = CAMPOS.filter((c) => !Number.isInteger(n(c.chave))).map((c) => ({
    campo: c.chave,
    erro: "Use um número inteiro",
  }));
  if (naoInteiros.length) return { problemas: naoInteiros };

  const faixa = { min: n("scaleRange.min"), max: n("scaleRange.max") };
  const cortes = {
    "padrao-1": n("cortes.padrao-1"),
    "padrao-2": n("cortes.padrao-2"),
    "padrao-3": n("cortes.padrao-3"),
  };
  const f = ScaleRange.safeParse(faixa);
  if (!f.success)
    return {
      problemas: f.error.issues.map((i) => ({
        campo: `scaleRange.${i.path.join(".")}`,
        erro: i.message,
      })),
    };
  return { problemas: problemasDosCortes(cortes, faixa), faixa, cortes };
}

/** "descritores.D03.scale.padrao-2.0.level" → "D03, Padrão 02: <erro>". */
function descreverProblema({ campo, erro }: Problema) {
  const m = /^descritores\.(D\d{2})(?:\.scale\.(padrao-\d))?/.exec(campo);
  if (!m) return erro;
  const padrao = Padrao.safeParse(m[2]).data;
  return `${m[1]}${padrao ? `, ${rotuloPadrao(padrao)}` : ""}: ${erro}`;
}

/** Faixa (min/max) e os 3 cortes do ano. Valida inline; salva ao sair do campo. */
export function FaixaCortes({ caderno, ano }: { caderno: Caderno; ano: AnoProjeto }) {
  const { slug, salvar } = useEdicao();
  const id = useId();
  const [valores, setValores] = useState(() => valoresDoAno(ano));
  const [erros, setErros] = useState<Erros>({});
  const [geral, setGeral] = useState<string[]>([]);

  function mostrar(problemas: readonly Problema[]) {
    const porCampo: Erros = {};
    const outros: string[] = [];
    for (const p of problemas) {
      if (ehChave(p.campo)) porCampo[p.campo] ??= p.erro;
      else outros.push(descreverProblema(p));
    }
    setErros(porCampo);
    setGeral(outros);
  }

  async function confirmar() {
    const { problemas, faixa, cortes } = validar(valores);
    if (!faixa || !cortes || problemas.length) return mostrar(problemas);

    const dados: AtualizarAnoEntrada = {};
    if (faixa.min !== ano.scaleRange.min || faixa.max !== ano.scaleRange.max)
      dados.scaleRange = faixa;
    if (PADROES_COM_CORTE.some((p) => cortes[p] !== ano.cortes[p])) dados.cortes = cortes;
    mostrar([]);
    if (!dados.scaleRange && !dados.cortes) return;

    try {
      await salvar({
        descricao: `Faixa e cortes do ${rotuloAnoCaderno(caderno, ano.ano)}`,
        valor: JSON.stringify(dados),
        executar: () => projetosApi.atualizarAno(slug, caderno, ano.ano, dados),
        aplicar: (p, resposta) => trocarAno(p, caderno, ano.ano, () => resposta),
      });
    } catch (e) {
      if (ehErroApi(e, 400) && e.corpo.detalhes?.length) mostrar(e.corpo.detalhes);
      else if (ehErroApi(e, 400) && e.campo) mostrar([{ campo: e.campo, erro: e.message }]);
      else setGeral([mensagemDeErro(e)]);
    }
  }

  /** Erro de cada chave aparece uma vez: no campo de início (ou no máximo); os dois campos o referenciam. */
  const idErro = (c: Chave) => `${id}-${c}-erro`;

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {BLOCOS.map((b) => {
          const ultimo = b.padrao === "padrao-4";
          const lados = [
            { chave: b.inicio, operador: ">=", texto: "início (maior ou igual a)" },
            ultimo
              ? ({ chave: b.fim, operador: "<=", texto: "fim (menor ou igual a)" } as const)
              : ({ chave: b.fim, operador: "<", texto: "fim (menor que)" } as const),
          ] as const;
          return (
            <div key={b.padrao} className="flex flex-col gap-3 rounded-lg border p-3">
              <div className="flex flex-col gap-2">
                <span aria-hidden className={`h-1.5 rounded-full ${b.cor}`} />
                <p className="text-sm font-medium whitespace-nowrap">{rotuloPadrao(b.padrao)}</p>
              </div>
              {lados.map(({ chave, operador, texto }) => {
                const erro = erros[chave];
                const mostraErro = chave === b.inicio || chave === "scaleRange.max";
                return (
                  <Field key={operador} data-invalid={erro ? true : undefined} className="gap-1.5">
                    <EntradaComOperador
                      operador={operador}
                      aria-label={`${rotuloPadrao(b.padrao)} — ${texto}`}
                      className="tabular-nums"
                      step={1}
                      aria-invalid={Boolean(erro)}
                      aria-describedby={erro ? idErro(chave) : undefined}
                      value={valores[chave]}
                      onChange={(e) => setValores((v) => ({ ...v, [chave]: e.target.value }))}
                      onBlur={() => void confirmar()}
                    />
                    {erro && mostraErro && <FieldError id={idErro(chave)}>{erro}</FieldError>}
                  </Field>
                );
              })}
            </div>
          );
        })}
      </div>
      {geral.length > 0 && (
        <Aviso tom="erro">
          <p>Não foi possível salvar a faixa e os cortes:</p>
          <ul className="mt-1 list-disc pl-5">
            {geral.map((g, i) => (
              <li key={i}>{g}</li>
            ))}
          </ul>
        </Aviso>
      )}
    </div>
  );
}
