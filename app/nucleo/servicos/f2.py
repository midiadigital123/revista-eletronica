"""Gerador do infográfico do F2: um infográfico resolvido -> SVG, tour e modais (D-239, D-242).

O desenho está em templates/revista/f2.svg (o comentário do topo é o contrato do contexto); aqui
ficam os números medidos no desenho em uso (example/f2-gerado/desenho-original.svg), no viewBox 0 0 1190.6 793.7.
"""

import textwrap
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

# Tabela do referencial (bloco habilidades, coordenadas locais): y da 1ª linha e a altura mínima de
# cada etapa, 1EF a 3EM (as do desenho de LP). A célula cujo texto não cabe cresce (D-300).
TABELA_Y = 64.8
ALTURAS_LINHAS = (22.7, 22.6, 22.7, 22.7, 22.7, 39.7, 39.6, 25.6, 25.5, 39.7, 39.6, 39.7)
assert len(EtapaReferencial.values) == len(ALTURAS_LINHAS)  # o zip abaixo cortaria etapas em silêncio
FIM_TABELA_Y = 427.6  # fio final da tabela
LEGENDA_Y = 450.6
LINHA_CEL = 12  # line-height de .f2-cel
RESPIRO_CEL = 6
# ponytail: estimativa de linhas por caracteres (cabem ~95 na célula de 351 px; 88 dá folga); texto com
# muita letra larga ainda pode ser cortado pelo line-clamp. Medir no navegador se isso aparecer.
CARACTERES_LINHA = 88
MARGEM_INFERIOR = 42.7  # do bloco mais baixo do desenho (progressão, base em 751) até o fim do viewBox
ALTURA_SVG = 793.7
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
        ("❷ Habilidades", html_para_texto(t["habilidades"])),
        ("❸ Progressão", html_para_texto(t["progressao"])),
        ("Referencial", juntar("\n", (
            juntar(" · ", (e["rotulo"] or e["etapa"], e["marca"], e["codigo"], e["texto"])) for e in inf["etapas"]
        ))),
        *((f"Tarefa {i['posicao']}", juntar("\n", (
            juntar(" – ", (i["descritor"], i["rotulo"])), i["texto_alternativo"], html_para_texto(i["analise"]),
        ))) for i in inf["itens"]),
    ]  # fmt: skip
    return [(rotulo, texto.strip()) for rotulo, texto in pares if texto and texto.strip()]


def _layout(ligados, cresceu=0):
    """Posição de cada bloco ligado (empilha por coluna com o gap do desenho) e a altura do SVG.

    `cresceu`: quanto a tabela do bloco habilidades passou da altura do desenho.
    """
    pos, base = {"cabecalho": CAIXA["cabecalho"][:2]}, 0
    for nomes, gap in COLUNAS.values():
        y = CAIXA[nomes[0]][1]
        for nome in nomes:
            if nome in ligados:
                pos[nome] = (CAIXA[nome][0], y)
                y += CAIXA[nome][3] + (cresceu if nome == "habilidades" else 0)
                base = max(base, y)
                y += gap
    altura_svg = round(max(ALTURA_SVG, base + MARGEM_INFERIOR), 1)
    return {nome: {"x": round(x, 1), "y": round(y, 1)} for nome, (x, y) in pos.items()}, altura_svg


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


def _linhas_texto(codigo, texto):
    """Linhas estimadas que o texto da célula ocupa (o código entra na frente, como no SVG)."""
    return len(textwrap.wrap(f"({codigo}) {texto}" if codigo else texto, CARACTERES_LINHA))


def _tabela(etapas):
    """As 12 linhas do referencial (etapa não gravada sai vazia), as células mescladas (rowspan) e
    quanto a tabela cresceu além do desenho.

    Célula cujo texto não cabe nas linhas que cobre divide o que falta igualmente entre elas.
    """
    gravadas = {e["etapa"]: e for e in etapas}
    tabela, celulas, alturas = [], [], list(ALTURAS_LINHAS)
    for i, etapa in enumerate(EtapaReferencial.values):
        g = gravadas.get(etapa, {})
        marca, codigo, texto = (g.get(c) or "" for c in ("marca", "codigo", "texto"))
        tabela.append({"etapa": etapa, "marca": marca, "cor": CORES_MARCA.get(marca, COR_SEM_MARCA)})
        acima = celulas[-1] if celulas else None
        if codigo or texto or not (acima and (acima["codigo"] or acima["texto"])):
            celulas.append({"codigo": codigo, "texto": texto, "linhas": [i]})
        else:
            acima["linhas"].append(i)
    for c in celulas:
        falta = _linhas_texto(c["codigo"], c["texto"]) * LINHA_CEL + RESPIRO_CEL - sum(alturas[i] for i in c["linhas"])
        if falta > 0:
            for i in c["linhas"]:
                alturas[i] += falta / len(c["linhas"])
    y, topo = TABELA_Y, []
    for linha, altura in zip(tabela, alturas):
        linha.update(y=round(y, 1), altura=round(altura, 1), meio=round(altura / 2, 1))
        topo.append(y)
        y += altura
    for c in celulas:
        linhas = c.pop("linhas")
        altura = sum(alturas[i] for i in linhas)
        c.update(y=round(topo[linhas[0]], 1), altura=round(altura, 1), clamp=max(1, int(altura // LINHA_CEL)))
    return tabela, celulas, round(sum(alturas) - sum(ALTURAS_LINHAS), 1) or 0  # 0.0 sairia "589.0" no translate


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
    tabela, celulas, cresceu = _tabela(infografico["etapas"])
    pos, altura_svg = _layout(ligados, cresceu if "habilidades" in ligados else 0)
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

    tour = {
        "label": ROTULO_TOUR,
        # Só o título: os parágrafos da abertura já estão na página, logo acima do infográfico (D-258).
        "intro": {"title": texto_puro(secao("abertura")["titulo"]), "text": ""},
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
        "fim_tabela": round(FIM_TABELA_Y + cresceu, 1),
        "legenda_y": round(LEGENDA_Y + cresceu, 1),
        "altura_svg": altura_svg,
        "pontos": [{"etapa": l["etapa"], "marca": l["marca"], "cor": l["cor"],
                    "x": round(PROGRESSAO_X + i * PROGRESSAO_PASSO, 1)} for i, l in enumerate(tabela)],
        "itens": itens,
    })
    return {"svg": mark_safe(svg), "tour": tour, "modais": modais}
