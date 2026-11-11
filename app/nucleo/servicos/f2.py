"""Gerador do infográfico do F2: um infográfico resolvido -> SVG, tour e modais (D-239, D-242).

O desenho está em templates/revista/f2.svg (o comentário do topo é o contrato do contexto); aqui
ficam os números medidos no desenho em uso (tests/fixtures/f2-lp.svg), no viewBox 0 0 1190.6 793.7.
"""

import re
from html import unescape
from pathlib import PurePosixPath

from django.template.loader import render_to_string
from django.utils.html import format_html, strip_tags
from django.utils.safestring import mark_safe

from nucleo.models.revista import PASSOS, EtapaReferencial
from nucleo.texto import html_para_texto

# Config do tour (antes em svg-tour/avaliacao-e-curriculo/revista.json); os textos vêm das seções.
ROTULO_TOUR = "Infográfico: tour guiado"

# Caixa de cada bloco (x, y, largura, altura); x e y são o translate do <g id="f2-<bloco>">.
CAIXA = {
    "cabecalho": (43, 85, 335, 56),
    "descritor": (252, 196, 164, 164),
    "habilidades": (661, 69, 468, 480),
    "progressao": (661, 589, 455, 162),
    "tarefas": (64, 463, 436, 254),
}
# Reflow: por coluna, os blocos ligados empilham a partir do primeiro y, com o gap do desenho.
COLUNAS = {"esquerda": (["descritor", "tarefas"], 103), "direita": (["habilidades", "progressao"], 40)}
# I, A, C, R: os azuis da legenda do desenho (do mais claro ao mais escuro).
CORES_MARCA = {"I": "#e6f6fb", "A": "#a9ffff", "C": "#08b4d7", "R": "#006991"}
# Marca vazia: o cinza do desenho (f2-st41).
COR_SEM_MARCA = "#dadada"

# Tabela do referencial (bloco habilidades, coordenadas locais): y da 1ª linha e a altura de cada
# etapa, 1EF a 3EM. ponytail: alturas do desenho de LP; texto mais longo é cortado pelo line-clamp.
TABELA_Y = 64.8
ALTURAS_LINHAS = (22.7, 22.6, 22.7, 22.7, 22.7, 39.7, 39.6, 25.6, 25.5, 39.7, 39.6, 39.7)
assert len(EtapaReferencial.values) == len(ALTURAS_LINHAS)  # o zip abaixo cortaria etapas em silêncio
# Progressão (bloco progressao, local): x da 1ª coluna e largura de cada etapa.
PROGRESSAO_X = 19.3
PROGRESSAO_PASSO = 37.3
# Conector do descritor até cada bloco (pontos do desenho). Os pontos do início com o y do 1º
# andam junto com o bloco; o último é a ponta no cartão.
CONECTORES = {
    "tarefas": ((111.9, 445), (111.9, 216.8), (262.8, 216.8)),
    "habilidades": ((640.6, 73.8), (486.5, 73.8), (486.5, 216.3), (405.7, 216.3)),
    "progressao": ((640.6, 594.5), (550.6, 594.5), (550.6, 250.8), (405.7, 250.8)),
}


def texto_puro(html):
    """HTML já renderizado → texto puro (o svg-tour põe título e texto por textContent)."""
    return unescape(strip_tags(html)).strip()


def textos_impresso(inf):
    """[(rótulo, texto puro)] de um infográfico resolvido: o que o impresso confere (diff e planilha F2).

    Só textos: a imagem do item não entra (D-118). O resolvido já esvaziou o invisível (D-243);
    aqui só saem as entradas vazias.
    """
    def juntar(sep, partes):
        return sep.join(p.strip() for p in partes if p and p.strip())

    t = inf["textos"]
    pares = [
        ("Habilidade", inf["habilidade"]),
        ("❶ Descritor", html_para_texto(t["descritor"])),
        ("❸ Habilidades", html_para_texto(t["habilidades"])),
        ("❷ Progressão", html_para_texto(t["progressao"])),
        ("Referencial", juntar("\n", (
            juntar(" · ", (e["rotulo"] or e["etapa"], e["marca"], e["codigo"], e["texto"])) for e in inf["etapas"]
        ))),
        *((f"Tarefa {i['posicao']}", juntar("\n", (
            juntar(" – ", (i["descritor"], i["rotulo"])), i["texto_alternativo"], html_para_texto(i["analise"]),
        ))) for i in inf["itens"]),
    ]  # fmt: skip
    return [(rotulo, texto.strip()) for rotulo, texto in pares if texto and texto.strip()]


def _layout(ligados):
    """Posição de cada bloco ligado: empilha por coluna mantendo o gap do desenho."""
    pos = {"cabecalho": CAIXA["cabecalho"][:2]}
    for nomes, gap in COLUNAS.values():
        y = CAIXA[nomes[0]][1]
        for nome in nomes:
            if nome in ligados:
                pos[nome] = (CAIXA[nome][0], y)
                y += CAIXA[nome][3] + gap
    return {nome: {"x": round(x, 1), "y": round(y, 1)} for nome, (x, y) in pos.items()}


def _conector(nome, y_bloco):
    dy = y_bloco - CAIXA[nome][1]
    pontos = list(CONECTORES[nome])
    # O trecho inicial na altura do 1º ponto sai do bloco e anda com ele; o resto liga ao cartão do
    # descritor, que não se move. ponytail: vale para conectores que saem do bloco na horizontal (os 3
    # do desenho); conector com outro formato pede ponto de ancoragem explícito.
    n = next((i for i, (_, y) in enumerate(pontos) if y != pontos[0][1]), len(pontos))
    pontos[:n] = [(x, y + dy) for x, y in pontos[:n]]
    return {"pontos": " ".join(f"{round(v, 1):g}" for p in pontos for v in p),
            "fim": {"x": round(pontos[-1][0], 1), "y": round(pontos[-1][1], 1)}}


def _tabela(etapas):
    """As 12 linhas do referencial (etapa não gravada sai vazia) e as células mescladas (rowspan)."""
    gravadas = {e["etapa"]: e for e in etapas}
    tabela, celulas, y = [], [], TABELA_Y
    for etapa, altura in zip(EtapaReferencial.values, ALTURAS_LINHAS):
        g = gravadas.get(etapa, {})
        marca, codigo, texto = (g.get(c) or "" for c in ("marca", "codigo", "texto"))
        tabela.append({"etapa": etapa, "marca": marca, "cor": CORES_MARCA.get(marca, COR_SEM_MARCA),
                       "y": round(y, 1), "altura": altura, "meio": round(altura / 2, 1)})
        acima = celulas[-1] if celulas else None
        if codigo or texto or not (acima and (acima["codigo"] or acima["texto"])):
            celulas.append({"codigo": codigo, "texto": texto, "y": round(y, 1), "altura": altura})
        else:
            acima["altura"] += altura
        y += altura
    for c in celulas:
        c["altura"] = round(c["altura"], 1)
        c["clamp"] = max(1, int(c["altura"] // 12))  # line-height de .f2-cel
    return tabela, celulas


def gerar(infografico, secoes, base_imagens, componente):
    """Um infográfico de resolvido["f2"]["infograficos"] -> {"svg", "tour", "modais"}.

    `secoes` é {id: {"id", "titulo", "corpo"}}, com título escapado e corpo já renderizado; os
    `textos` e a `analise` dos itens também chegam renderizados. Seção ausente sai vazia.
    A imagem do item sai em `<base_imagens><nome do arquivo>` (no banco, `infograficos/<nome>`).
    `componente`: rótulo vindo do banco vivo, fora do resolvido e da foto arquivada; ficou fora do
    hash por decisão da D-242 (renomear componente é raro).
    """
    ligados = [p for p in PASSOS if p == "descritor" or p in infografico["passos"]]

    def secao(id_):
        return secoes.get(id_, {"titulo": "", "corpo": ""})

    textos = infografico["textos"]
    pos = _layout(ligados)
    tabela, celulas = _tabela(infografico["etapas"])
    itens = sorted(infografico["itens"], key=lambda i: i["posicao"]) if "tarefas" in ligados else []

    modais = [{"id": "dlg-descritor", "titulo": mark_safe(secao("dlg-descritor")["titulo"]),
               "corpo": mark_safe(secao("dlg-descritor")["corpo"] + textos["descritor"])}]
    for passo in ("habilidades", "progressao", "tarefas"):
        if passo in ligados:
            corpo = secao("dlg-tarefas")["corpo"] if passo == "tarefas" else textos[passo]
            modais.append({"id": f"dlg-{passo}", "titulo": mark_safe(secao(f"passo-{passo}")["titulo"]),
                           "corpo": mark_safe(corpo)})
    for n, item in enumerate(itens, 1):
        img = format_html('<img src="{}{}" alt="{}">', base_imagens, PurePosixPath(item["imagem"]).name, item["texto_alternativo"]) if item["imagem"] else ""
        modais.append({"id": f"dlg-tarefa-{n}", "titulo": format_html("{} – {}", item["descritor"], item["rotulo"]),
                       "corpo": mark_safe(img + item["analise"])})

    primeiro = re.search(r"<p\b[^>]*>(.*?)</p>", secao("abertura")["corpo"], re.S)
    tour = {
        "label": ROTULO_TOUR,
        "intro": {"title": texto_puro(secao("abertura")["titulo"]), "text": texto_puro(primeiro[1]) if primeiro else ""},
        "steps": [{"target": f"f2-{p}", "title": texto_puro(secao(f"passo-{p}")["titulo"]),
                   "text": texto_puro(secao(f"passo-{p}")["corpo"])} for p in ligados],
        "modais": [m["id"] for m in modais],
    }
    svg = render_to_string("revista/f2.svg", {
        "componente": componente,
        "habilidade": infografico["habilidade"],
        "pos": pos,
        "linhas": [_conector(p, pos[p]["y"]) for p in ligados if p in CONECTORES],
        "tabela": tabela,
        "celulas": celulas,
        "pontos": [{"etapa": l["etapa"], "marca": l["marca"], "cor": l["cor"],
                    "x": round(PROGRESSAO_X + i * PROGRESSAO_PASSO, 1)} for i, l in enumerate(tabela)],
        "itens": itens,
    })
    return {"svg": mark_safe(svg), "tour": tour, "modais": modais}
