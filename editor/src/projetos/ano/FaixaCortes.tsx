import { useState } from "react";
import {
  Padrao,
  PADROES_COM_CORTE,
  problemasDosCortes,
  ROTULO_ANO,
  ScaleRange,
  type AnoProjeto,
  type AtualizarAnoEntrada,
  type Cortes,
  type Problema,
} from "../../contrato/schemas";
import { ehErroApi } from "../../api/client";
import { Aviso, CampoTexto } from "../../ui";
import { projetosApi } from "../api";
import { useEdicao } from "../edicao";
import { mensagemDeErro, rotuloPadrao, trocarAno } from "./dados";

const CAMPOS = [
  { chave: "scaleRange.min", rotulo: "Mínimo", ajuda: "Base da escala" },
  { chave: "cortes.padrao-1", rotulo: "Corte 01 → 02", ajuda: "Início do Padrão 02" },
  { chave: "cortes.padrao-2", rotulo: "Corte 02 → 03", ajuda: "Início do Padrão 03" },
  { chave: "cortes.padrao-3", rotulo: "Corte 03 → 04", ajuda: "Início do Padrão 04" },
  { chave: "scaleRange.max", rotulo: "Máximo", ajuda: "Topo da escala" },
] as const;

type Chave = (typeof CAMPOS)[number]["chave"];
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
      problemas: f.error.issues.map((i) => ({ campo: `scaleRange.${i.path.join(".")}`, erro: i.message })),
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
export function FaixaCortes({ ano }: { ano: AnoProjeto }) {
  const { slug, salvar } = useEdicao();
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
    if (faixa.min !== ano.scaleRange.min || faixa.max !== ano.scaleRange.max) dados.scaleRange = faixa;
    if (PADROES_COM_CORTE.some((p) => cortes[p] !== ano.cortes[p])) dados.cortes = cortes;
    mostrar([]);
    if (!dados.scaleRange && !dados.cortes) return;

    try {
      await salvar({
        descricao: `Faixa e cortes do ${ROTULO_ANO[ano.ano]}`,
        valor: JSON.stringify(dados),
        executar: () => projetosApi.atualizarAno(slug, ano.ano, dados),
        aplicar: (p, resposta) => trocarAno(p, ano.ano, () => resposta),
      });
    } catch (e) {
      if (ehErroApi(e, 400) && e.corpo.detalhes?.length) mostrar(e.corpo.detalhes);
      else if (ehErroApi(e, 400) && e.campo) mostrar([{ campo: e.campo, erro: e.message }]);
      else setGeral([mensagemDeErro(e)]);
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5 [&_input]:font-mono [&_input]:tabular-nums">
        {CAMPOS.map((c) => (
          <CampoTexto
            key={c.chave}
            rotulo={c.rotulo}
            ajuda={c.ajuda}
            erro={erros[c.chave]}
            type="number"
            step={1}
            inputMode="numeric"
            value={valores[c.chave]}
            onChange={(e) => setValores((v) => ({ ...v, [c.chave]: e.target.value }))}
            onBlur={() => void confirmar()}
          />
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
