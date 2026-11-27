"""Converte o Word "Avaliação e Currículo" da Pedagógica no seed de um infográfico do F2 (D-298).

Uso: python3 scripts/docx_infografico.py <docx> [lp|mt] <alfa|outras> <pasta_saida>   (componente padrão: lp)
Gera <pasta_saida>/<cc>-<tipo>.json e <cc>-<tipo>-item-<n>.png. Os nomes dos campos são os de
`nucleo/infografico.py`; os textos ricos saem em Markdown (parágrafo e negrito, sem título #).
Para com erro se o Word fugir do formato esperado (12 etapas, marcas iguais nas duas tabelas,
4 itens com imagem e análise, 3 textos de clique). Pillow só para empilhar item com 2 imagens.
"""

import io
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
ETAPAS = {  # nucleo.models.revista.EtapaReferencial (código: rótulo)
    "1EF": "1º ano do Ensino Fundamental", "2EF": "2º ano do Ensino Fundamental",
    "3EF": "3º ano do Ensino Fundamental", "4EF": "4º ano do Ensino Fundamental",
    "5EF": "5º ano do Ensino Fundamental", "6EF": "6º ano do Ensino Fundamental",
    "7EF": "7º ano do Ensino Fundamental", "8EF": "8º ano do Ensino Fundamental",
    "9EF": "9º ano do Ensino Fundamental", "1EM": "1ª série do Ensino Médio",
    "2EM": "2ª série do Ensino Médio", "3EM": "3ª série do Ensino Médio",
}  # fmt: skip
POR_ROTULO = {v: k for k, v in ETAPAS.items()}
ROTULO_ANO = re.compile(r"^(\d[ºª].*(Ensino Fundamental|Ensino Médio)|Ensino Médio)$")
CODIGO = re.compile(r"^\((\w+)\)\s*(.*)$", re.S)


def erro(msg):
    sys.exit(f"erro: {msg}")


def _ligado(rpr, tag):
    el = rpr.find(W + tag) if rpr is not None else None
    return el is not None and el.get(W + "val", "1") not in ("0", "false")


def paragrafo(p, rels):
    """(texto puro, texto Markdown, [imagens]) do parágrafo."""
    puro, md, imgs = "", "", []
    for r in p.iter(W + "r"):
        t = "".join(x.text or "" for x in r.iter(W + "t"))
        for blip in r.iter("{http://schemas.openxmlformats.org/drawingml/2006/main}blip"):
            imgs.append(rels[blip.get(R + "embed")])
        if not t:
            continue
        puro += t
        nucleo = t.strip()
        if nucleo and _ligado(r.find(W + "rPr"), "b"):
            t = t.replace(nucleo, f"**{nucleo}**")
        elif nucleo and _ligado(r.find(W + "rPr"), "i"):
            t = t.replace(nucleo, f"*{nucleo}*")
        md += t
    return puro.strip(), md.replace("****", "").strip(), imgs


def tabela(tbl):
    """Linhas [[(texto, continua_mescla)]] da tabela."""
    linhas = []
    for tr in tbl.iter(W + "tr"):
        celulas = []
        for tc in tr.iter(W + "tc"):
            vm = tc.find(f"{W}tcPr/{W}vMerge")
            continua = vm is not None and vm.get(W + "val") in (None, "continue")
            celulas.append(("".join(x.text or "" for x in tc.iter(W + "t")).strip(), continua))
        linhas.append(celulas)
    return linhas


def ler(docx):
    z = zipfile.ZipFile(docx)
    rels = {
        r.get("Id"): "word/" + r.get("Target")
        for r in ET.fromstring(z.read("word/_rels/document.xml.rels"))
    }
    corpo = ET.fromstring(z.read("word/document.xml")).find(W + "body")
    blocos = []  # ("p", puro, md, imgs) ou ("tbl", linhas), na ordem do documento
    for el in corpo:
        if el.tag == W + "p":
            puro, md, imgs = paragrafo(el, rels)
            if puro or imgs:
                blocos.append(("p", puro, md, imgs))
        elif el.tag == W + "tbl":
            blocos.append(("tbl", tabela(el)))
    return z, blocos


def converter(docx, tipo):
    z, blocos = ler(docx)
    tabelas = [b[1] for b in blocos if b[0] == "tbl"]
    paras = [b[1:] for b in blocos if b[0] == "p"]
    if len(tabelas) != 2:
        erro(f"esperava 2 tabelas (descrição e progressão), achei {len(tabelas)}")

    # Progressão: linha 1 = etapas, linha 2 = marcas.
    cab, marcas = [c[0] for c in tabelas[1][0]], [c[0] for c in tabelas[1][1]]
    if cab != list(ETAPAS):
        erro(f"tabela de progressão com etapas {cab}")
    marca = dict(zip(cab, marcas))

    # Descrição: etapa | marca | (código) texto; continuação de mescla do Word = junta com a de cima (D-301).
    etapas = {}
    for linha in tabelas[0]:
        if len(linha) != 3:
            erro(f"linha da tabela de descrição com {len(linha)} células: {linha}")
        (etapa, _), (m, m_cont), (ct, ct_cont) = linha
        if etapa not in ETAPAS:
            erro(f"etapa desconhecida na tabela de descrição: {etapa!r}")
        if m and not m_cont and m != marca[etapa]:
            erro(f"{etapa}: marca {m} na descrição e {marca[etapa]} na progressão")
        codigo = texto = ""
        if ct and not ct_cont:
            achado = CODIGO.match(ct)
            if not achado:
                erro(f"{etapa}: célula sem '(código) texto': {ct[:40]!r}")
            codigo, texto = achado[1], achado[2].strip()
        etapas[etapa] = {"marca": marca[etapa], "codigo": codigo, "texto": texto,
                         "junta_marca": bool(etapas and m_cont), "junta_habilidade": bool(etapas and ct_cont)}
    if list(etapas) != list(ETAPAS):
        erro(f"tabela de descrição com etapas {list(etapas)}")

    puros = [p[0] for p in paras]
    habilidade = next((p.split(":", 1)[1].strip() for p in puros if p.startswith("❶Descritor:")), "")

    # Lista do ❹ (1º "❹TAREFAS"): "D05 – 2º ano do Ensino Fundamental".
    tarefas = [i for i, p in enumerate(puros) if p.startswith("❹TAREFAS")]
    if len(tarefas) != 2:
        erro(f"esperava 2 títulos '❹TAREFAS', achei {len(tarefas)}")
    itens = []
    for p in puros[tarefas[0] + 1 :]:
        achado = re.match(r"^(\S+)\s*[–-]\s*(.+)$", p)
        if not achado or achado[2] not in POR_ROTULO:
            break
        itens.append({"posicao": len(itens) + 1, "etapa": POR_ROTULO[achado[2]], "descritor": achado[1], "habilidade": ""})
    if len(itens) != 4:
        erro(f"esperava 4 itens na lista do ❹, achei {len(itens)}")

    # Textos dos cliques: de "TEXTOS DOS CLIQUES:" ao 2º "❹TAREFAS", cortados em ❶ ❷ ❸.
    inicio = puros.index("TEXTOS DOS CLIQUES:") + 1
    textos, atual = {}, None
    for puro, md, _ in paras[inicio : tarefas[1]]:
        if puro[:1] in "❶❷❸":
            atual = {"❶": "texto_descritor", "❷": "texto_progressao", "❸": "texto_habilidades"}[puro[0]]
            md = md.lstrip("*").removeprefix(puro[0]).strip()  # o marcador sai; negrito em volta dele também
            puro = puro[1:].strip()
        if atual is None:
            continue
        if atual == "texto_habilidades" and ROTULO_ANO.match(puro):
            md = f"**{puro}**"
        textos.setdefault(atual, []).append(md)
    for campo in ("texto_descritor", "texto_progressao", "texto_habilidades"):
        if not textos.get(campo):
            erro(f"texto do clique vazio: {campo}")

    # Itens (2º "❹TAREFAS"): rótulo da etapa, códigos P…, imagem(ns), análise.
    blocos_item, atual = {}, None
    for puro, md, imgs in paras[tarefas[1] + 1 :]:
        if puro in POR_ROTULO:
            atual = blocos_item.setdefault(POR_ROTULO[puro], {"imgs": [], "analise": []})
        elif atual is None:
            continue  # "Aqui, apresentamos…": é texto do template F2
        elif imgs:
            atual["imgs"] += imgs
        elif re.fullmatch(r"P\w+", puro):
            continue  # código do item e do suporte: rótulo do design
        else:
            atual["analise"].append(md)
    imagens = {}
    for item in itens:
        bloco = blocos_item.get(item["etapa"])
        if not bloco or not bloco["imgs"] or not bloco["analise"]:
            erro(f"item {item['posicao']} ({item['etapa']}) sem imagem ou sem análise")
        item["analise"] = "\n\n".join(bloco["analise"])
        suporte = re.search(r"utiliza como suporte (.+?)(?:,|\.(?:\s|$))", item["analise"].replace("**", ""))
        rotulo = ETAPAS[item["etapa"]]
        artigo = "da" if "série" in rotulo else "do"
        item["texto_alternativo"] = f"Item {artigo} {rotulo}" + (f": {suporte[1]}." if suporte else ".")
        item["imagem"] = f"lp-{tipo}-item-{item['posicao']}.png"
        imagens[item["imagem"]] = [z.read(n) for n in bloco["imgs"]]

    seed = {
        "fonte": Path(docx).name, "componente": "LP", "tipo": tipo, "habilidade": habilidade,
        **{c: "\n\n".join(v) for c, v in textos.items()},
        "etapas": etapas, "itens": itens,
    }  # fmt: skip
    if not habilidade:
        erro("falta '❶Descritor: …' (habilidade destacada)")
    return seed, imagens


def converter_mt(docx, tipo):
    """Word "Currículo e Avaliação" de MT (D-311): um "TEXTO DO CLIQUE:" por passo, descrição só até onde a
    BNCC tem habilidade (as etapas seguintes ficam só com a marca da progressão) e itens por nível (D-305)."""
    z, blocos = ler(docx)
    tabelas = [b[1] for b in blocos if b[0] == "tbl"]
    paras = [b[1:] for b in blocos if b[0] == "p"]
    puros = [p[0] for p in paras]
    if len(tabelas) != 2:
        erro(f"esperava 2 tabelas (progressão e descrição), achei {len(tabelas)}")

    # Progressão (1ª tabela): linha 1 = etapas, linha 2 = marcas.
    cab, marcas = [c[0] for c in tabelas[0][0]], [c[0] for c in tabelas[0][1]]
    if cab != list(ETAPAS):
        erro(f"tabela de progressão com etapas {cab}")
    etapas = {e: {"marca": m, "codigo": "", "texto": "", "junta_marca": False, "junta_habilidade": False}
              for e, m in zip(cab, marcas)}  # fmt: skip

    # Descrição (2ª tabela): etapa | marca | (código) texto; pode parar antes do 3EM e ter célula vazia.
    for linha in tabelas[1]:
        if len(linha) != 3:
            erro(f"linha da tabela de descrição com {len(linha)} células: {linha}")
        (etapa, _), (m, _), (ct, _) = linha
        if etapa not in ETAPAS:
            erro(f"etapa desconhecida na tabela de descrição: {etapa!r}")
        if m != etapas[etapa]["marca"]:
            erro(f"{etapa}: marca {m} na descrição e {etapas[etapa]['marca']} na progressão")
        if ct:
            achado = CODIGO.match(ct)
            if not achado:
                erro(f"{etapa}: célula sem '(código) texto': {ct[:40]!r}")
            # Dois códigos na célula (6EF): o 1º vai para o campo, o 2º fica no texto como no Word.
            etapas[etapa].update(codigo=achado[1], texto=re.sub(r"\.\(", ". (", achado[2].strip()))

    habilidade = next((p.split(":", 1)[1].strip() for p in puros if re.match(r"^❶\s*Descritor:", p)), "")
    if not habilidade:
        erro("falta '❶ Descritor: …' (habilidade destacada)")

    # Textos dos cliques: cada "TEXTO DO CLIQUE:" vai até o próximo título numerado (❷ ❸ ❹) ou "LEGENDA:".
    cliques = [i for i, p in enumerate(puros) if p.endswith("TEXTO DO CLIQUE:")]
    textos = {}
    for i, campo in zip(cliques, ("texto_descritor", "texto_progressao", "texto_habilidades")):
        fim = next(j for j in range(i + 1, len(puros)) if puros[j][:1] in "❶❷❸❹" or puros[j] == "LEGENDA:")
        textos[campo] = "\n\n".join(paras[j][1] for j in range(i + 1, fim))
        if not textos[campo]:
            erro(f"texto do clique vazio: {campo}")
    if len(textos) != 3:
        erro(f"esperava 3 textos de clique antes do ❹, achei {len(textos)}")

    # Lista do ❹ (1º "❹ TAREFAS"): "1 – <habilidade do item>".
    tarefas = [i for i, p in enumerate(puros) if re.match(r"^❹\s*TAREFAS", p)]
    if len(tarefas) != 2:
        erro(f"esperava 2 títulos '❹ TAREFAS', achei {len(tarefas)}")
    itens = []
    for p in puros[tarefas[0] + 1 :]:
        achado = re.match(r"^(\d)\s*[–-]\s*(.+)$", p)
        if not achado:
            break
        n = int(achado[1])
        itens.append({"posicao": n, "etapa": "", "descritor": "", "habilidade": achado[2],
                      "texto_alternativo": f"Item do nível {n}: {achado[2]}"})  # fmt: skip
    if [i["posicao"] for i in itens] != [1, 2, 3, 4]:
        erro(f"esperava os níveis 1 a 4 na lista do ❹, achei {[i['posicao'] for i in itens]}")

    # Itens (2º "❹ TAREFAS"): "N (M…)" (código do design, ignorado), imagem, análise; até "AGORA É COM VOCÊ".
    blocos_item, atual = {}, None
    for puro, md, imgs in paras[tarefas[1] + 1 :]:
        if puro.replace(" ", "").upper().startswith("AGORAÉCOMVOCÊ"):
            break  # fechamento: é texto do template F2
        if achado := re.match(r"^(\d)\s*\(M\w+\)$", puro):
            atual = blocos_item.setdefault(int(achado[1]), {"imgs": [], "analise": []})
            atual["imgs"] += imgs
        elif atual is None:
            continue
        elif imgs:
            atual["imgs"] += imgs
        elif puro:
            atual["analise"].append(md)
    imagens = {}
    for item in itens:
        bloco = blocos_item.get(item["posicao"])
        if not bloco or not bloco["imgs"] or not bloco["analise"]:
            erro(f"item {item['posicao']} sem imagem ou sem análise")
        item["analise"] = "\n\n".join(bloco["analise"])
        item["imagem"] = f"mt-{tipo}-item-{item['posicao']}.png"
        imagens[item["imagem"]] = [z.read(n) for n in bloco["imgs"]]

    seed = {
        "fonte": Path(docx).name, "componente": "MT", "tipo": tipo, "habilidade": habilidade,
        **textos, "etapas": etapas, "itens": itens,
    }  # fmt: skip
    return seed, imagens


def png(partes):
    """Uma imagem PNG; com mais de uma parte, empilhadas na ordem do Word, fundo branco (D-232)."""
    if len(partes) == 1 and partes[0][:8] == b"\x89PNG\r\n\x1a\n":
        return partes[0]
    from PIL import Image  # ponytail: Pillow só no host, para o seed; o app não depende dele

    imgs = [Image.open(io.BytesIO(p)).convert("RGB") for p in partes]
    tela = Image.new("RGB", (max(i.width for i in imgs), sum(i.height for i in imgs)), "white")
    y = 0
    for i in imgs:
        tela.paste(i, (0, y))
        y += i.height
    saida = io.BytesIO()
    tela.save(saida, "PNG", optimize=True)
    return saida.getvalue()


def main():
    args = sys.argv[1:]
    if len(args) == 3:
        args.insert(1, "lp")
    if len(args) != 4 or args[1] not in ("lp", "mt") or args[2] not in ("alfa", "outras"):
        sys.exit(__doc__)
    docx, cc, tipo, pasta = args[0], args[1], args[2], Path(args[3])
    seed, imagens = (converter_mt if cc == "mt" else converter)(docx, tipo)
    pasta.mkdir(parents=True, exist_ok=True)
    for nome, partes in imagens.items():
        (pasta / nome).write_bytes(png(partes))
    (pasta / f"{cc}-{tipo}.json").write_text(json.dumps(seed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    juntadas = [n for n, p in imagens.items() if len(p) > 1]
    print(f"{cc}-{tipo}.json: {len(seed['etapas'])} etapas, {len(seed['itens'])} itens; imagens juntadas: {juntadas or 'nenhuma'}")


if __name__ == "__main__":
    main()
