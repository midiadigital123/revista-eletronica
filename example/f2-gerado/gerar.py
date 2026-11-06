#!/usr/bin/env python3
"""Protótipo (fase 0): gera o F2 como SVG a partir de dados.json, dentro da página do svg-tour.

    python3 gerar.py                                   # escreve index.html
    python3 gerar.py -o index-sem-habilidades.html --desligar habilidades
    python3 gerar.py --check                           # único teste do gerador

Só stdlib. Tudo em px fixos dentro do SVG (o <style> vai DENTRO do <svg>: é o que chega ao minimapa).
"""
import argparse
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
VIEWBOX = "0 0 1190.6 793.7"
PASSOS = ["descritor", "habilidades", "progressao", "tarefas"]  # ordem do tour
# Geometria do SVG real (x, y, largura, altura).
CAIXA = {
    "cabecalho": (43, 85, 335, 56),
    "descritor": (252, 196, 164, 164),
    "habilidades": (661, 69, 468, 480),
    "progressao": (661, 589, 455, 162),
    "tarefas": (64, 463, 436, 254),
}
# Reflow: por coluna, os blocos ligados empilham a partir do primeiro y, com o gap do desenho original.
COLUNAS = {"esquerda": (["descritor", "tarefas"], 103), "direita": (["habilidades", "progressao"], 40)}
CORES_MARCA = {"I": "#4f9bd9", "A": "#ff8d43", "C": "#3cb371", "R": "#a66bbe"}
LEGENDA = {"I": "Introduzir", "A": "Aprofundar", "C": "Consolidar", "R": "Retomar"}
FONTE = '"Proxima Nova", -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif'
XHTML = 'xmlns="http://www.w3.org/1999/xhtml"'
CSP = ("default-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
       "img-src 'self' data: blob:; base-uri 'none'; form-action 'none'")

e = html.escape


def layout(ligados):
    """Posição de cada bloco ligado: empilha por coluna mantendo o gap original."""
    pos = {"cabecalho": CAIXA["cabecalho"]}
    for nomes, gap in COLUNAS.values():
        y = CAIXA[nomes[0]][1]
        for nome in nomes:
            if nome not in ligados:
                continue
            x, _, w, h = CAIXA[nome]
            pos[nome] = (x, y, w, h)
            y += h + gap
    return pos


def paragrafos(lista):
    """Markdown mínimo (só **negrito**) → <p>."""
    return "\n".join(
        "<p>" + re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", e(p)) + "</p>" for p in lista
    )


def botao_mais(sufixo, cx, cy):
    # Classe f2-st20: o hover laranja vem de revista.css ([id^="f2-btn-action-"]:hover .f2-st20).
    return (f'<g id="f2-btn-action-{sufixo}" class="f2g-mais">'
            f'<circle class="f2-st20" cx="{cx}" cy="{cy}" r="7.8"/>'
            f'<text x="{cx}" y="{cy + 4}" text-anchor="middle">+</text></g>')


# ---------------------------------------------------------------- blocos (coordenadas locais: translate)

def svg_cabecalho(d, c):
    x, y, w, h = c
    return (f'<g id="f2-cabecalho" transform="translate({x},{y})">'
            f'<text class="f2g-h1" x="0" y="26">Avaliação e currículo</text>'
            f'<text class="f2g-h2" x="0" y="50">{e(d["componente"])}</text></g>')


def svg_descritor(d, c):
    x, y, w, h = c
    desc = d["descritor"]
    return (f'<g id="f2-descritor" transform="translate({x},{y})">'
            f'<rect class="f2g-cartao" x="0" y="0" width="{w}" height="{h}" rx="10"/>'
            f'<text class="f2g-rotulo" x="14" y="24">Descritor</text>'
            f'<text class="f2g-codigo" x="14" y="68">{e(desc["codigo"])}</text>'
            f'<foreignObject x="10" y="80" width="{w - 20}" height="{h - 88}">'
            f'<div {XHTML} class="f2g-desc">{e(desc["descricao"])}</div></foreignObject></g>')


def svg_habilidades(d, c):
    x, y, w, h = c
    linhas = "".join(
        f'<div class="f2g-lin"><span class="f2g-etapa">{e(r["etapa"])}</span>'
        f'<span><i class="f2g-marca" style="background:{CORES_MARCA[r["marca"]]}">{e(r["marca"])}</i></span>'
        f'<span class="f2g-cod">{e(r["codigo"])}</span>'
        f'<span class="f2g-txt">{e(r["texto"])}</span></div>'
        for r in d["habilidades"]
    )
    legenda = "".join(
        f'<circle cx="{18 + i * 110}" cy="{h - 18}" r="6" fill="{CORES_MARCA[m]}"/>'
        f'<text class="f2g-leg" x="{30 + i * 110}" y="{h - 14}">{m} — {LEGENDA[m]}</text>'
        for i, m in enumerate("IACR")
    )
    return (f'<g id="f2-habilidades" transform="translate({x},{y})">'
            f'<rect class="f2g-bloco" x="0" y="0" width="{w}" height="{h}" rx="10"/>'
            f'<text class="f2g-titulo" x="36" y="36">Descrição das habilidades no referencial curricular</text>'
            f'{botao_mais("habilidades", 19, 31)}'
            f'<foreignObject x="8" y="50" width="{w - 16}" height="{h - 90}">'
            f'<div {XHTML} class="f2g-tabela">{linhas}</div></foreignObject>'
            f'{legenda}</g>')


def svg_progressao(d, c):
    x, y, w, h = c
    hab = d["habilidades"]
    x0, x1, yl = 40, w - 40, 95
    passo = (x1 - x0) / (len(hab) - 1)
    pontos = "".join(
        f'<circle cx="{x0 + i * passo:.1f}" cy="{yl}" r="11" fill="{CORES_MARCA[r["marca"]]}"/>'
        f'<text class="f2g-ponto" x="{x0 + i * passo:.1f}" y="{yl + 4}" text-anchor="middle">{e(r["marca"])}</text>'
        f'<text class="f2g-leg" x="{x0 + i * passo:.1f}" y="{yl + 28}" text-anchor="middle">{e(r["etapa"])}</text>'
        for i, r in enumerate(hab)
    )
    return (f'<g id="f2-progressao" transform="translate({x},{y})">'
            f'<rect class="f2g-bloco" x="0" y="0" width="{w}" height="{h}" rx="10"/>'
            f'<text class="f2g-titulo" x="36" y="36">Progressão da habilidade</text>'
            f'{botao_mais("progressao", 19, 31)}'
            f'<line class="f2g-eixo" x1="{x0}" y1="{yl}" x2="{x1}" y2="{yl}"/>{pontos}</g>')


def svg_tarefas(d, c):
    x, y, w, h = c
    larg, alt, gap = 90, 150, 12
    minis = "".join(
        f'<g transform="translate({20 + i * (larg + gap)},60)">'
        f'<rect class="f2g-mini" x="0" y="0" width="{larg}" height="{alt}" rx="6"/>'
        f'<text class="f2g-rotulo" x="10" y="22">{e(t["rotulo"])}</text>'
        f'<text class="f2g-mini-etapa" x="10" y="56">{e(t["etapa"])}</text>'
        f'<text class="f2g-leg" x="10" y="74">{e(t["descritor"])}</text>'
        f'{botao_mais(f"tarefa-{i + 1}", larg - 16, alt - 16)}</g>'
        for i, t in enumerate(d["tarefas"])
    )
    return (f'<g id="f2-tarefas" transform="translate({x},{y})">'
            f'<rect class="f2g-bloco" x="0" y="0" width="{w}" height="{h}" rx="10"/>'
            f'<text class="f2g-titulo" x="20" y="36">Tarefas por nível de complexidade</text>{minis}</g>')


def svg_linhas(pos):
    """Um <line> do cartão do descritor até cada bloco ligado (mesma coluna: por baixo; outra: pela direita)."""
    dx, dy, dw, dh = pos["descritor"]
    linhas = []
    for nome in ("habilidades", "progressao", "tarefas"):
        if nome not in pos:
            continue
        x, y, w, h = pos[nome]
        if x > dx + dw:  # coluna da direita: sai do meio da borda direita do cartão
            y1 = dy + dh / 2
            y2 = y1 if y <= y1 <= y + h else y + h / 2
            linhas.append(f'<line x1="{dx + dw}" y1="{y1}" x2="{x}" y2="{y2}"/>')
        else:  # mesma coluna: desce do meio da borda inferior
            linhas.append(f'<line x1="{dx + dw / 2}" y1="{dy + dh}" x2="{dx + dw / 2}" y2="{y}"/>')
    return f'<g id="f2-linhas" class="f2g-linhas">{"".join(linhas)}</g>'


# Sem ">" nem "&" no CSS (o minimapa reserializa o SVG com XMLSerializer) e sem seletor pela classe do
# <svg> raiz (o minimapa a remove, svg-tour.js:559). user-select:text libera a seleção do texto HTML
# (o stage do svg-tour usa user-select:none); o arrasto continua movendo a vista sem selecionar.
ESTILO = f"""
text{{font-family:{FONTE};fill:#000}}
.f2g-h1{{font-size:28px;font-weight:700}}
.f2g-h2{{font-size:16px;font-weight:400}}
.f2g-titulo{{font-size:14px;font-weight:700}}
.f2g-rotulo{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px}}
.f2g-codigo{{font-size:38px;font-weight:700}}
.f2g-leg{{font-size:9px}}
.f2g-ponto{{font-size:11px;font-weight:700;fill:#fff}}
.f2g-mini-etapa{{font-size:16px;font-weight:700}}
.f2g-cartao{{fill:#ffeb00}}
.f2g-bloco{{fill:#fff;stroke:#dee2e6;stroke-width:1}}
.f2g-mini{{fill:#f8f9fa;stroke:#dee2e6;stroke-width:1}}
.f2g-eixo{{stroke:#000;stroke-width:1.5}}
.f2g-linhas line{{stroke:#000;stroke-width:1.2;fill:none}}
.f2g-mais circle{{fill:#ffeb00;stroke:#000;stroke-width:.8}}
.f2g-mais text{{font-size:12px;font-weight:700;pointer-events:none}}
.f2g-desc{{font:11px/1.35 {FONTE};color:#000;user-select:text}}
.f2g-tabela{{font:8.5px/1.2 {FONTE};color:#000;user-select:text;display:grid;grid-template-columns:28px 18px 62px 1fr;grid-auto-rows:32px;column-gap:6px}}
.f2g-lin{{display:contents}}
.f2g-etapa{{font-weight:700}}
.f2g-marca{{display:inline-block;width:14px;height:14px;border-radius:50%;color:#fff;font-style:normal;font-weight:700;text-align:center;line-height:14px}}
.f2g-cod{{font-weight:700}}
.f2g-lin span{{border-bottom:1px solid #ebebeb;height:32px;box-sizing:border-box;padding-top:1px}}
.f2g-txt{{display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
"""

GERADORES = {"descritor": svg_descritor, "habilidades": svg_habilidades,
             "progressao": svg_progressao, "tarefas": svg_tarefas}


def gerar_svg(d, ligados):
    pos = layout(ligados)
    partes = [
        f'<svg class="f2g" viewBox="{VIEWBOX}" xmlns="http://www.w3.org/2000/svg">',
        f"<style>{ESTILO}</style>",
        '<rect width="100%" height="100%" fill="#fafafa"/>',
        '<ellipse cx="120" cy="720" rx="190" ry="110" fill="#ffeb00" opacity=".35"/>',
        '<ellipse cx="1100" cy="40" rx="150" ry="80" fill="#ffeb00" opacity=".35"/>',
        svg_cabecalho(d, pos["cabecalho"]),
        svg_linhas(pos),
    ]
    partes += [GERADORES[n](d, pos[n]) for n in PASSOS if n in ligados]
    partes.append("</svg>")
    return "\n".join(partes)


def dialog(sufixo, titulo, corpo):
    return (f'<dialog id="dlg-{sufixo}" aria-labelledby="dlgTitle-{sufixo}"><div class="modal-body">'
            f'<form method="dialog" class="modal-close-row"><button type="submit" aria-label="Fechar">&times;</button></form>'
            f'<h3 id="dlgTitle-{sufixo}">{e(titulo)}</h3>{corpo}</div></dialog>')


def gerar_html(d, ligados):
    dialogs, modais = [], []
    if "habilidades" in ligados:
        m = d["modais"]["habilidades"]
        tabela = "".join(
            f'<tr><th>{e(r["etapa"])}</th><td><span class="marca" style="background:{CORES_MARCA[r["marca"]]}">{e(r["marca"])}</span></td>'
            f'<td>{e(r["codigo"])}</td><td>{e(r["texto"])}</td></tr>' for r in d["habilidades"])
        dialogs.append(dialog("habilidades", m["titulo"],
                              f'<table class="habilidades"><tbody>{tabela}</tbody></table>' + paragrafos(m["paragrafos"])))
        modais.append("dlg-habilidades")
    if "progressao" in ligados:
        m = d["modais"]["progressao"]
        dialogs.append(dialog("progressao", m["titulo"], paragrafos(m["paragrafos"])))
        modais.append("dlg-progressao")
    if "tarefas" in ligados:
        for i, t in enumerate(d["tarefas"], 1):
            dialogs.append(dialog(f"tarefa-{i}", t["rotulo"],
                                  f'<p>Aqui abre o arquivo da tarefa {e(t["etapa"])} {e(t["descritor"])}.</p>'))
            modais.append(f"dlg-tarefa-{i}")
    tour = {
        "label": "Infográfico: tour guiado",
        "intro": {"title": d["abertura"]["titulo"], "text": d["abertura"]["texto"]},
        "steps": [{"target": f"f2-{n}", "title": d["passos"][n]["titulo"], "text": d["passos"][n]["texto"]}
                  for n in PASSOS if n in ligados],
        "modais": modais,
    }
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<title>F2 gerado a partir de dados (protótipo)</title>
<link rel="stylesheet" href="../f2-animado-tour/f2/revista.css">
<style>
table.habilidades{{border-collapse:collapse;font-size:.9rem;margin-bottom:1rem}}
table.habilidades th,table.habilidades td{{border-bottom:1px solid #dee2e6;padding:.35rem .5rem;vertical-align:top;text-align:left}}
table.habilidades .marca{{display:inline-block;width:1.4em;height:1.4em;border-radius:50%;color:#fff;text-align:center;line-height:1.4em;font-weight:700}}
</style>
</head>
<body>
<main class="f2-section">
<h2 id="f2-titulo">Infográfico</h2>
<div id="revista">{gerar_svg(d, ligados)}</div>
</main>
{"".join(dialogs)}
<script id="dados-tour" type="application/json">{json.dumps(tour, ensure_ascii=False).replace("</", "<\\/")}</script>
<script src="../f2-animado-tour/f2/svg-tour.js"></script>
<script src="../f2-animado-tour/f2/svg-tour-modal.js"></script>
<script src="../f2-animado-tour/f2/f2-init.js"></script>
</body>
</html>
"""


def check(d):
    def svg_de(doc):
        return re.search(r"<svg.*?</svg>", doc, re.S).group(0)

    completo = gerar_html(d, set(PASSOS))
    svg = svg_de(completo)
    ET.fromstring(svg)  # XML bem formado (foreignObject incluso)
    for i in ("f2-cabecalho", "f2-descritor", "f2-habilidades", "f2-progressao", "f2-tarefas", "f2-linhas",
              "f2-btn-action-habilidades", "f2-btn-action-progressao", "f2-btn-action-tarefa-1"):
        assert f'id="{i}"' in svg, i
    assert 'id="f2-titulo"' not in svg
    assert completo.count("<dialog ") == 6

    sem = gerar_html(d, set(PASSOS) - {"habilidades"})
    svg = svg_de(sem)
    ET.fromstring(svg)
    tour = json.loads(re.search(r'id="dados-tour" type="application/json">(.*?)</script>', sem, re.S).group(1))
    assert len(tour["steps"]) == 3, tour["steps"]
    assert "f2-habilidades" not in sem and "dlg-habilidades" not in sem
    assert 'id="f2-progressao" transform="translate(661,69)"' in svg
    assert svg.count("<line") == 3  # eixo da progressão + 2 conectores
    print("OK")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", default="index.html")
    ap.add_argument("--desligar", default="", help="passos separados por vírgula (descritor nunca desliga)")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    d = json.loads((AQUI / "dados.json").read_text(encoding="utf-8"))
    if a.check:
        return check(d)
    desligados = {p.strip() for p in a.desligar.split(",") if p.strip()} - {"descritor"}
    assert desligados <= set(PASSOS), desligados - set(PASSOS)
    (AQUI / a.o).write_text(gerar_html(d, set(PASSOS) - desligados), encoding="utf-8")
    print(a.o)


if __name__ == "__main__":
    main()
