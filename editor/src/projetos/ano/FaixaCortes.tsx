import { useId, useState } from "react";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
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

const CAMPOS = [
  { chave: "scaleRange.min", rotulo: "Mínimo" },
  { chave: "cortes.padrao-1", rotulo: "Corte 01 → 02" },
  { chave: "cortes.padrao-2", rotulo: "Corte 02 → 03" },
  { chave: "cortes.padrao-3", rotulo: "Corte 03 → 04" },
  { chave: "scaleRange.max", rotulo: "Máximo" },
] as const;

type Chave = (typeof CAMPOS)[number]["chave"];

/** Cada padrão: campos que moram no bloco (o corte fica no padrão que ele inicia) e de onde vem a faixa. */
const BLOCOS = [
  {
    padrao: "padrao-1",
    cor: "bg-padrao-1",
    campos: [0],
    inicio: "scaleRange.min",
    fim: "cortes.padrao-1",
  },
  {
    padrao: "padrao-2",
    cor: "bg-padrao-2",
    campos: [1],
    inicio: "cortes.padrao-1",
    fim: "cortes.padrao-2",
  },
  {
    padrao: "padrao-3",
    cor: "bg-padrao-3",
    campos: [2],
    inicio: "cortes.padrao-2",
    fim: "cortes.padrao-3",
  },
  {
    padrao: "padrao-4",
    cor: "bg-padrao-4",
    campos: [3, 4],
    inicio: "cortes.padrao-3",
    fim: "scaleRange.max",
  },
] as const satisfies readonly {
  padrao: Padrao;
  cor: string;
  campos: readonly number[];
  inicio: Chave;
  fim: Chave;
}[];
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

  /** "125 a 249": o fim é exclusivo (é o próximo corte), exceto no Padrão 04, que vai até o máximo. */
  function faixaDoBloco(b: (typeof BLOCOS)[number]) {
    const n = (c: Chave) => (valores[c].trim() === "" ? NaN : Number(valores[c]));
    const inicio = n(b.inicio);
    const fim = n(b.fim) - (b.padrao === "padrao-4" ? 0 : 1);
    return Number.isInteger(inicio) && Number.isInteger(fim) ? `${inicio} a ${fim}` : "…";
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
        {BLOCOS.map((b) => (
          <div key={b.padrao} className="flex flex-col gap-3 rounded-lg border p-3">
            <div className="flex flex-col gap-2">
              <span aria-hidden className={`h-1.5 rounded-full ${b.cor}`} />
              <div className="flex flex-wrap items-baseline justify-between gap-x-2">
                <p className="text-sm font-medium whitespace-nowrap">{rotuloPadrao(b.padrao)}</p>
                <p className="text-sm whitespace-nowrap text-muted-foreground tabular-nums">
                  {faixaDoBloco(b)}
                </p>
              </div>
            </div>
            {b.campos.map((i) => {
              const c = CAMPOS[i];
              const campoId = `${id}-${i}`;
              const erro = erros[c.chave];
              return (
                <Field key={c.chave} data-invalid={erro ? true : undefined}>
                  <FieldLabel htmlFor={campoId}>{c.rotulo}</FieldLabel>
                  <Input
                    id={campoId}
                    className="tabular-nums"
                    type="number"
                    step={1}
                    inputMode="numeric"
                    aria-invalid={Boolean(erro)}
                    aria-describedby={erro ? `${campoId}-erro` : undefined}
                    value={valores[c.chave]}
                    onChange={(e) => setValores((v) => ({ ...v, [c.chave]: e.target.value }))}
                    onBlur={() => void confirmar()}
                  />
                  {erro && <FieldError id={`${campoId}-erro`}>{erro}</FieldError>}
                </Field>
              );
            })}
          </div>
        ))}
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
