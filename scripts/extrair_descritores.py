#!/usr/bin/env python3
"""Extrai os descritores da seção "INTERPRETAÇÃO PEDAGÓGICA DA ESCALA" da revista (PDF)
e grava um JSON por disciplina no formato do descritores.json.

Uso: python3 scripts/extrair_descritores.py <revista.pdf> [pasta-saida]
     python3 scripts/extrair_descritores.py <revista.pdf> --stdout
       (imprime {disciplina: {ano: ...}} em uma linha e não grava arquivos; usado pela API)

Requer pdftotext (poppler-utils). Lê as palavras com coordenadas (-bbox) porque
prerrequisitos têm 2 colunas e régua/BNCC dependem da posição na página.
"""
import html
import json
import re
import subprocess
import sys
from pathlib import Path

# Colunas (x, em pt) da página de descritor.
X_CORTE = 110  # números de corte (350, 400, 500) ficam à esquerda disto
X_TICK = 140  # níveis da régua (782, 732...) entre X_CORTE e isto
X_FAIXA = 170  # 1000/500 e 0 (limites da escala) entre X_TICK e isto; texto das faixas à direita
X_ROTULO_BNCC = 165

# ponytail: nos 5º anos a revista não imprime os números de corte (só as linhas coloridas).
# Valores do Saeb; confirmar e atualizar aqui se a revista usar outros.
CORTES_SEM_NUMERO = {
    "lingua-portuguesa": {"5ef": [150, 200, 250]},
    "matematica": {"5ef": [175, 225, 275]},
}

PALAVRA = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')
MARCADOR = re.compile("^[\x80-\x9f\ue000-\uf8ff\u25aa\u2022\u25a0]$")  # a fonte do PDF exporta o marcador como U+0083
NUMERO = re.compile(r"^\d+$")
CODIGO = re.compile(r"^D\d{2}$")
SO_CODIGOS = re.compile(r"^(EF\d{2}[A-Z]{2}\d{2}[,\s]*)+$")


def juntar(partes):
    return re.sub(r"\s+", " ", " ".join(partes)).strip()


def ler_paginas(pdf):
    """Palavras de cada página: [{x, x2, y, t}]."""
    saida = subprocess.run(
        ["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True, check=True
    ).stdout
    return [
        [
            {"x": float(m[1]), "y": float(m[2]), "x2": float(m[3]), "t": html.unescape(m[5])}
            for m in PALAVRA.finditer(pagina)
        ]
        for pagina in saida.split("<page ")[1:]
    ]


def linhas(palavras):
    """Agrupa palavras em linhas (mesmo y ± 2pt), de cima para baixo e da esquerda para a direita."""
    ls = []
    for w in sorted(palavras, key=lambda w: (w["y"], w["x"])):
        alvo = next((l for l in ls if abs(l["y"] - w["y"]) < 2), None)
        if alvo:
            alvo["w"].append(w)
        else:
            ls.append({"y": w["y"], "w": [w]})
    for l in ls:
        l["w"].sort(key=lambda w: w["x"])
    return ls


def texto(ws):
    """Texto das palavras, sem espaço entre glifos colados (ex.: "/" "ʒ" "/" → "/ʒ/")."""
    s, fim = "", float("-inf")
    for w in sorted(ws, key=lambda w: w["x"]):
        s += (" " if s and w["x"] - fim > 0.8 else "") + w["t"]
        fim = w["x2"]
    return s.strip()


def texto_pagina(palavras):
    return " ".join(texto(l["w"]) for l in linhas(palavras))


def mais_proxima(itens, y):
    return min(itens, key=lambda i: abs(i["y"] - y))


def prerrequisitos(ls):
    """2 colunas: marcador abre item; linha sem marcador continua o item da mesma coluna."""
    xs = [w["x"] for l in ls for w in l["w"] if MARCADOR.match(w["t"]) and w["x"] > 200]
    x_direita = min(xs) - 5 if xs else float("inf")
    colunas = [[], []]
    for l in ls:
        for i, ws in enumerate(
            ([w for w in l["w"] if w["x"] < x_direita], [w for w in l["w"] if w["x"] >= x_direita])
        ):
            if not ws:
                continue
            novo = bool(MARCADOR.match(ws[0]["t"]))
            t = texto(ws[1:] if novo else ws)
            if novo or not colunas[i]:
                colunas[i].append(t)
            else:
                colunas[i][-1] = juntar([colunas[i][-1], t])
    return [t for t in colunas[0] + colunas[1] if t]


def limites_escala(ls):
    """Máximo (1000/500) e mínimo (0) da régua: números sozinhos na linha, na coluna dos limites."""
    ws = [
        l["w"][0] for l in ls
        if len(l["w"]) == 1 and NUMERO.match(l["w"][0]["t"]) and X_TICK <= l["w"][0]["x"] < X_FAIXA
    ]
    return ws[0], ws[-1]


def regua(ls):
    """Cada linha de texto pertence ao nível (tick) logo abaixo dela; "–" vira "---"."""
    topo, base = limites_escala(ls)
    numeros = [
        w for l in ls for w in l["w"]
        if NUMERO.match(w["t"]) and w["x"] < X_FAIXA and topo["y"] <= w["y"] <= base["y"]
    ]
    ticks = sorted((w for w in numeros if X_CORTE <= w["x"] < X_TICK), key=lambda w: w["y"])
    cortes = [int(w["t"]) for w in numeros if w["x"] < X_CORTE]

    # Fragmentos deslocados (ex.: glifo "ʒ" um pouco acima da linha) entram na linha mais próxima.
    faixa = [
        {"y": l["y"], "w": [w for w in l["w"] if w["x"] >= X_FAIXA]}
        for l in ls
        if topo["y"] < l["y"] < base["y"]
    ]
    faixa = [l for l in faixa if l["w"]]
    inteiras = [l for l in faixa if l["w"][0]["x"] < 190]
    for frag in (l for l in faixa if l["w"][0]["x"] >= 190):
        mais_proxima(inteiras, frag["y"])["w"].extend(frag["w"])

    conteudo = {int(t["t"]): [] for t in ticks}
    for l in inteiras:
        t = texto(l["w"])
        if t in ("–", "-"):
            continue
        tick = next((t for t in ticks if t["y"] > l["y"]), base)  # abaixo do último tick: vai até o mínimo
        conteudo.setdefault(int(tick["t"]), []).append(t)
    niveis = [{"level": n, "content": juntar(p) or "---"} for n, p in conteudo.items()]
    return {"scaleRange": {"min": int(base["t"]), "max": int(topo["t"])}, "cortes": cortes, "niveis": niveis}


def bncc(ls):
    """Cada linha de valor vai para o rótulo mais próximo em y (rótulos ficam centralizados no valor)."""
    rotulos = [{"y": l["y"], "t": texto([w for w in l["w"] if w["x"] < X_ROTULO_BNCC])} for l in ls]
    rotulos = [r for r in rotulos if r["t"].endswith(":")]
    valores = {r["t"]: [] for r in rotulos}
    for l in ls:
        ws = [w for w in l["w"] if w["x"] >= X_ROTULO_BNCC]
        if ws and rotulos:
            valores[mais_proxima(rotulos, l["y"])["t"]].append(texto(ws))

    def campo(padrao):
        return juntar(next((v for k, v in valores.items() if re.search(padrao, k, re.I)), []))

    return {
        "practices": campo(r"^Pr[aá]ticas|^Eixo"),
        "knowledge": campo(r"^Objeto|^Unidade"),
        "relacionadas": campo(r"relacionadas"),
        "correspondente": campo(r"correspondente"),
    }


def descritor(palavras):
    ls = linhas(palavras)

    def linha_de(padrao):
        return next(l for l in ls if re.search(padrao, texto(l["w"])))

    cab = linha_de(r"^\d+º ANO DO ENSINO FUNDAMENTAL$")
    pre = linha_de(r"^Pré-requisitos")
    codigo = next(w["t"] for w in palavras if CODIGO.match(w["t"]) and cab["y"] < w["y"] < pre["y"])
    ano = re.match(r"^(\d+)º", texto(cab["w"]))[1] + "ef"
    topo_regua = limites_escala([l for l in ls if l["y"] > pre["y"]])[0]["y"]
    y_bncc = next(w["y"] for w in palavras if w["t"] == "BNCC" and w["y"] > topo_regua)

    def entre(a, b):
        return [l for l in ls if a < l["y"] < b]

    return {
        "ano": ano,
        "codigo": codigo,
        "description": juntar(
            texto([w for w in l["w"] if w["t"] != codigo]) for l in entre(cab["y"], pre["y"])
        ),
        "prerequisites": prerrequisitos(entre(pre["y"], topo_regua)),
        "regua": regua(entre(pre["y"], y_bncc)),
        "bncc": bncc(entre(y_bncc, float("inf"))),
    }


def padrao_do_nivel(level, c):
    if level >= c["padrao-3"]:
        return "padrao-4"
    if level >= c["padrao-2"]:
        return "padrao-3"
    if level >= c["padrao-1"]:
        return "padrao-2"
    return "padrao-1"


def avisar(msg):
    print(f"aviso: {msg}", file=sys.stderr)


def extrair(pdf):
    """{disciplina: {ano: {scaleRange, cortes, Dxx: {...}}}}"""
    paginas = ler_paginas(pdf)
    # A última ocorrência é o título da seção (a primeira é o sumário).
    achadas = [
        i for i, p in enumerate(paginas)
        if re.search(r"INTERPRETAÇÃO\s+PEDAGÓGICA\s+DA\s+ESCALA", texto_pagina(p))
    ]
    if not achadas:
        raise ValueError('"INTERPRETAÇÃO PEDAGÓGICA DA ESCALA" não encontrado no PDF')
    inicio = achadas[-1]

    brutos = {}  # disciplina → ano → [descritor]
    disciplina = None
    for n, p in enumerate(paginas[inicio + 1 :], start=inicio + 2):
        t = texto_pagina(p)
        eh_descritor = "Pré-requisitos" in t and "BNCC" in t and any(CODIGO.match(w["t"]) for w in p)
        if not eh_descritor:
            if "MATEMÁTICA" in t:
                disciplina = "matematica"
            elif "LÍNGUA PORTUGUESA" in t:
                disciplina = "lingua-portuguesa"
            continue
        if not disciplina:
            raise ValueError(f"página {n}: descritor antes da abertura de disciplina")
        try:
            d = descritor(p)
        except Exception as e:
            raise ValueError(f"página {n}: {e!r}") from e
        brutos.setdefault(disciplina, {}).setdefault(d["ano"], []).append(d)

    saida = {}
    for disc, anos in brutos.items():
        for ano, ds in anos.items():
            impressos = sorted({c for d in ds for c in d["regua"]["cortes"]})
            valores = impressos if len(impressos) == 3 else CORTES_SEM_NUMERO.get(disc, {}).get(ano)
            if not valores:
                raise ValueError(f"{disc} {ano}: cortes impressos {impressos} e ausentes em CORTES_SEM_NUMERO")
            cortes = {"padrao-1": valores[0], "padrao-2": valores[1], "padrao-3": valores[2]}
            scale_range = ds[0]["regua"]["scaleRange"]
            dados_ano = {"scaleRange": scale_range, "cortes": cortes}
            for d in sorted(ds, key=lambda d: d["codigo"]):
                onde = f"{disc} {ano} {d['codigo']}"
                if d["codigo"] in dados_ano:
                    avisar(f"{onde} repetido; ficou a última ocorrência")
                if d["regua"]["scaleRange"] != scale_range:
                    avisar(f"{onde}: escala {d['regua']['scaleRange']}, ano usa {scale_range}")
                rel, corr = d["bncc"]["relacionadas"], d["bncc"]["correspondente"]
                if SO_CODIGOS.match(corr) and not SO_CODIGOS.match(rel):
                    avisar(f'{onde}: "Habilidades relacionadas" e "correspondente" trocadas no PDF; destrocadas')
                    rel, corr = corr, rel
                scale = {p: [] for p in ("padrao-1", "padrao-2", "padrao-3", "padrao-4")}
                for nivel in sorted(d["regua"]["niveis"], key=lambda n: -n["level"]):
                    scale[padrao_do_nivel(nivel["level"], cortes)].append(nivel)
                dados_ano[d["codigo"]] = {
                    "topic": "",
                    "description": d["description"],
                    "prerequisites": d["prerequisites"],
                    "bncc": {
                        "practices": d["bncc"]["practices"],
                        "knowledge": d["bncc"]["knowledge"],
                        "skills": [s for s in (rel, corr) if s],
                    },
                    "scale": scale,
                }
            saida.setdefault(disc, {})[ano] = dados_ano
    return saida


def main(argv):
    stdout = "--stdout" in argv
    argv = [a for a in argv if a != "--stdout"]
    if not argv:
        sys.exit("Uso: python3 scripts/extrair_descritores.py <revista.pdf> [pasta-saida] [--stdout]")
    if stdout:
        print(json.dumps(extrair(argv[0]), ensure_ascii=False))
        return
    pasta = Path(argv[1] if len(argv) > 1 else ".")
    pasta.mkdir(parents=True, exist_ok=True)
    for disc, anos in extrair(argv[0]).items():
        arquivo = pasta / f"{disc}.json"
        arquivo.write_text(json.dumps(anos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        resumo = ", ".join(f"{a}: {len(d) - 2} descritores" for a, d in anos.items())
        print(f"{arquivo} — {resumo}")


if __name__ == "__main__":
    main(sys.argv[1:])
