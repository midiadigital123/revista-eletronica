"""Extrai os descritores da seção "INTERPRETAÇÃO PEDAGÓGICA DA ESCALA" da revista (PDF).

Cópia de `scripts/extrair_descritores.py` (o original segue servindo a API antiga até o S17),
sem a exigência de 3 cortes e sem `padrao_do_nivel` (D-059): a matriz guarda só o intervalo
de cada tarefa; os cortes impressos no PDF são descartados.

Requer pdftotext (poppler-utils). Lê as palavras com coordenadas (-bbox) porque
prerrequisitos têm 2 colunas e régua/BNCC dependem da posição na página.
"""
import html
import logging
import re
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Colunas (x, em pt) da página de descritor.
X_CORTE = 110  # números de corte (350, 400, 500) ficam à esquerda disto
X_TICK = 140  # níveis da régua (782, 732...) entre X_CORTE e isto
X_FAIXA = 170  # 1000/500 e 0 (limites da escala) entre X_TICK e isto; texto das faixas à direita
X_ROTULO_BNCC = 165

PALAVRA = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')
MARCADOR = re.compile("^[\x80-\x9f\ue000-\uf8ff\u25aa\u2022\u25a0]$")  # a fonte do PDF exporta o marcador como U+0083
NUMERO = re.compile(r"^\d+$")
CODIGO = re.compile(r"^D\d{2}$")
SO_CODIGOS = re.compile(r"^(EF\d{2}[A-Z]{2}\d{2}[,\s]*)+$")


def juntar(partes):
    return re.sub(r"\s+", " ", " ".join(partes)).strip()


def habilidades(partes):
    """Nova habilidade quando a linha anterior termina em "." e a atual começa com maiúscula."""
    hs = []
    for t in partes:
        if not hs or (hs[-1].endswith(".") and t[:1].isupper()):
            hs.append(t)
        else:
            hs[-1] = juntar([hs[-1], t])
    return hs or ["---"]


def ler_paginas(pdf):
    """Palavras de cada página: [{x, x2, y, t}]."""
    saida = subprocess.run(
        ["pdftotext", "-bbox", str(Path(pdf).resolve()), "-"],
        capture_output=True, encoding="utf-8", check=True, timeout=120,
    ).stdout
    return [
        [
            {"x": float(m[1]), "y": float(m[2]), "x2": float(m[3]), "h": float(m[4]) - float(m[2]),
             "t": html.unescape(m[5])}
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
    """Cada linha de texto pertence ao nível (tick) logo abaixo dela; "–" vira "---".
    fim = tick logo acima (na faixa do topo, o máximo da escala)."""
    topo, base = limites_escala(ls)
    numeros = [
        w for l in ls for w in l["w"]
        if NUMERO.match(w["t"]) and w["x"] < X_FAIXA and topo["y"] <= w["y"] <= base["y"]
    ]
    # Os cortes impressos (à esquerda da régua ou em negrito na coluna dos ticks) entram como
    # ticks comuns ou ficam de fora: são do parceiro, não da matriz (D-059).
    ticks = sorted((w for w in numeros if X_CORTE <= w["x"] < X_TICK), key=lambda w: w["y"])

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
        if t.rstrip(".") in ("–", "-"):
            continue
        tick = next((t for t in ticks if t["y"] > l["y"]), base)  # abaixo do último tick: vai até o mínimo
        conteudo.setdefault(int(tick["t"]), []).append(t)
    valores = [int(t["t"]) for t in ticks]
    fim = dict(zip(valores + [int(base["t"])], [int(topo["t"])] + valores))
    niveis = [{"level": n, "fim": fim[n], "content": h} for n, p in conteudo.items() for h in habilidades(p)]
    return {"scaleRange": {"min": int(base["t"]), "max": int(topo["t"])}, "niveis": niveis}


def bncc(ls):
    """Linhas de valor viram blocos (entrelinha ~11pt; entre blocos ~15pt) e cada bloco vai para o
    rótulo mais próximo do seu centro (rótulos ficam centralizados no valor). Linha a linha, a 1ª
    linha de um valor longo caía no rótulo de cima."""
    # Coluna dos valores: 1ª palavra depois de "Rótulo:" (varia por revista: 154 a 171 pt).
    x_valor = min(
        (l["w"][i + 1]["x"] for l in ls for i, w in enumerate(l["w"][:-1]) if w["t"].endswith(":")),
        default=X_ROTULO_BNCC,
    ) - 1
    rotulos = [{"y": l["y"], "t": texto([w for w in l["w"] if w["x"] < x_valor])} for l in ls]
    rotulos = [r for r in rotulos if r["t"].endswith(":")]
    valores = {r["t"]: [] for r in rotulos}
    blocos = []
    for l in ls:
        ws = [w for w in l["w"] if w["x"] >= x_valor]
        if not ws:
            continue
        if blocos and l["y"] - blocos[-1][-1]["y"] < 13:
            blocos[-1].append({"y": l["y"], "t": texto(ws)})
        else:
            blocos.append([{"y": l["y"], "t": texto(ws)}])
    for b in blocos:
        if rotulos:
            centro = (b[0]["y"] + b[-1]["y"]) / 2
            valores[mais_proxima(rotulos, centro)["t"]].extend(x["t"] for x in b)

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

    cab = linha_de(r"^\d+(º ANO DO ENSINO FUNDAMENTAL|ª SÉRIE DO ENSINO MÉDIO)$")
    pre = linha_de(r"^Pré-requisitos")
    codigo = next(w["t"] for w in palavras if CODIGO.match(w["t"]) and cab["y"] < w["y"] < pre["y"])
    ano = re.match(r"^\d+", texto(cab["w"]))[0] + ("ef" if "º" in texto(cab["w"]) else "em")
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


CC_DA_DISCIPLINA = {"lingua-portuguesa": "LP", "matematica": "MT"}


def tarefas(niveis):
    """Níveis da régua → tarefas, de cima para baixo. As linhas "---" não viram Tarefa: as
    linhas vazias saem do `passo` da matriz × etapa × CC (D-091), calculadas na renderização."""
    return [
        {"inicio": n["level"], "fim": n["fim"], "texto": n["content"]}
        for n in sorted(niveis, key=lambda n: -n["level"])
        if n["content"] != "---"
    ]


def extrair(pdf):
    """{(cc, etapa): {"escala": {min, max}, "descritores": [...]}}, com cc "LP"/"MT" e
    etapa "2EF"/"5EF"/"9EF"/"3EM"; cada descritor traz os campos de `Descritor` e "tarefas"."""
    paginas = ler_paginas(pdf)
    # A última ocorrência é o título da seção (a primeira é o sumário).
    achadas = [
        i for i, p in enumerate(paginas)
        if re.search(r"INTERPRETAÇÃO\s+PEDAGÓGICA\s+DA\s+ESCALA", texto_pagina(p))
    ]
    if not achadas:
        raise ValueError('"INTERPRETAÇÃO PEDAGÓGICA DA ESCALA" não encontrado no PDF')
    inicio = achadas[-1]

    brutos = {}  # (cc, etapa) → [descritor]
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
        brutos.setdefault((CC_DA_DISCIPLINA[disciplina], d["ano"].upper()), []).append(d)

    saida = {}
    for (cc, etapa), ds in brutos.items():
        escala = ds[0]["regua"]["scaleRange"]
        por_codigo = {}
        for d in sorted(ds, key=lambda d: d["codigo"]):
            onde = f"{cc} {etapa} {d['codigo']}"
            if d["regua"]["scaleRange"] != escala:
                logger.warning("%s: escala %s, etapa usa %s", onde, d["regua"]["scaleRange"], escala)
            rel, corr = d["bncc"]["relacionadas"], d["bncc"]["correspondente"]
            if SO_CODIGOS.match(corr) and not SO_CODIGOS.match(rel):
                logger.warning('%s: "Habilidades relacionadas" e "correspondente" trocadas no PDF; destrocadas', onde)
                rel, corr = corr, rel
            novo = {
                "codigo": d["codigo"],
                "descricao": d["description"],
                "prerequisitos": d["prerequisites"],
                "praticas": d["bncc"]["practices"],
                "conhecimento": d["bncc"]["knowledge"],
                "habilidades_relacionadas": rel,
                "habilidade_correspondente": corr,
                "tarefas": tarefas(d["regua"]["niveis"]),
            }
            # Página repetida idêntica: fica uma. Mesmo código com conteúdo diferente: recusa.
            if por_codigo.setdefault(d["codigo"], novo) != novo:
                raise ValueError(f"{onde} aparece duas vezes no PDF com conteúdo diferente")
        saida[(cc, etapa)] = {"escala": escala, "descritores": list(por_codigo.values())}
    return saida


