"""Biblioteca (conteúdo mestre): Matrizes e Templates.

Mudar uma matriz ou um template muda muitas revistas: por isso o IMPACTO aparece antes do clique
(linha de impacto ao lado do botão, diálogo "Confirme o impacto", números nas tabelas).
Páginas: matrizes, matriz-<id> (x3), matriz-etapa, matriz-importar, matriz-diferencas,
templates, template-lp-f1, template-lp-f2.
"""
import json
import re

import dados as D
from paginas import shell as S

M = {m["id"]: m for m in D.MATRIZES}
ETAPAS_NOME = [("2EF", "2º EF"), ("5EF", "5º EF"), ("9EF", "9º EF"), ("3EM", "3º EM")]
LINHAS = [(e, en, c) for e, en in ETAPAS_NOME for c, _ in D.COMPONENTES]  # 8 linhas etapa × componente
PESO = [16, 18, 8, 22, 22, 24, 16, 16]  # 5º EF · LP tem 8 descritores: é a lista que a tela da etapa mostra
HOJE = "12/11"


# ── Apoios ────────────────────────────────────────────────────────────────
def _n(n, s, p=None):
    return f"{n} {s if n == 1 else (p or s + 's')}"


def _tb(heads, rows, cls="", id_=""):
    """Tabela com classe por célula: cabeçalho [str | (str, cls)], linhas [(attrs, [str | (str, cls)])]."""
    th = "".join(f'<th class="{c[1]}">{c[0]}</th>' if isinstance(c, tuple) else f"<th>{c}</th>" for c in heads)
    corpo = ""
    for attrs, cels in rows:
        corpo += f"<tr {attrs}>"
        for c in cels:
            txt, k = (c, "") if isinstance(c, str) else c
            corpo += f'<td class="{k}">{txt}</td>' if k else f"<td>{txt}</td>"
        corpo += "</tr>"
    i = f' id="{id_}"' if id_ else ""
    return f'<div class="tab-caixa"><table class="tabela {cls}"{i}><thead><tr>{th}</tr></thead><tbody>{corpo}</tbody></table></div>'


def _leitura(texto):
    return f'<div class="mb" data-p="imp">{S.aviso(texto, "leitura")}</div>'


def _rev(mid, comp=None):
    return [r for r in D.REVISTAS if r["matriz"] == mid and (comp is None or r["comp"] == comp)]


def _val(rs):
    return [r for r in rs if r["fase"] >= 4]


def _titulo_edita(valor, rotulo, extra=""):
    return (
        f'<span class="edita-inline"><input class="input" value="{S.esc(valor)}" aria-label="{S.esc(rotulo)}" '
        f'data-edita data-autosave {extra}>{S.ic("lapis")}</span>'
    )


def _secao(titulo, texto="", acao=""):
    p = f"<p>{texto}</p>" if texto else ""
    return f'<div class="secao-t"><div><h2>{titulo}</h2>{p}</div>{acao}</div>'


def _lista_impacto(revistas, destino=3):
    itens = ""
    for r in revistas:
        itens += (
            f'<li><a href="{S.href_revista(r["id"])}">{S.nome_revista(r)}</a>'
            f'<span class="vai">{S.regua_mini(r["fase"])}{S.ic("seta")}{S.regua_mini(destino)}'
            f"<span>perde o Validado</span></span></li>"
        )
    return f'<ul class="lista-imp">{itens}</ul>'


def _dlg_impacto(id_, titulo, intro, revistas, total_txt):
    corpo = (
        f"<p>{intro}</p>"
        f'<p class="num-imp">{total_txt}</p>' + (_lista_impacto(revistas) if revistas else "")
    )
    rod = (
        '<button type="button" class="btn" data-fechar>Voltar e editar</button>'
        '<button type="button" class="btn btn-prim" data-impacto-ok>Confirmar e gravar</button>'
    )
    return S.dialogo(id_, titulo, corpo, rod)


def _dlg_duplicar():
    corpo = (
        S.campo("Nome da cópia", "nome", "", attrs='id="dup-nome" data-edita')
        + '<p class="ajuda">A cópia nasce igual à matriz <b id="dup-origem">Comunitária 2026</b> e não afeta nenhuma revista até você ligá-la a um parceiro.</p>'
    )
    rod = (
        '<button type="button" class="btn" data-fechar>Cancelar</button>'
        '<button type="button" class="btn btn-prim" data-toast="Matriz duplicada. Abra a cópia para ligar parceiros." data-fechar data-edita>Duplicar</button>'
    )
    return S.dialogo("dlg-duplicar", "Duplicar matriz", corpo, rod)


def _desc_linhas(m):
    """Descritores por etapa × componente; a diferença para o total cai na última linha."""
    p = PESO[:]
    p[-1] += m["descritores"] - sum(p)
    return p


def _intervalo(mid, etapa, comp):
    base = 50 if etapa == "2EF" else 25
    return 20 if (mid == "vale-verde-2026" and (etapa, comp) in (("5EF", "LP"), ("9EF", "LP"))) else base


# ── Matrizes ──────────────────────────────────────────────────────────────
def _matrizes():
    linhas = []
    for m in D.MATRIZES:
        origem = f"cópia de {m['origem']}" if m["origem"] else "importada"
        itens = [
            S.item_menu("Duplicar", icone="copiar", attrs=f'data-abrir="dlg-duplicar" data-duplicar="{S.esc(m["nome"])}" data-edita'),
            S.item_menu("Reimportar", "matriz-importar.html#reimportar", "subir"),
        ]
        if m["origem"]:
            itens.append(S.item_menu("Diferenças", "matriz-diferencas.html", "colunas"))
        itens += ["<hr>", S.item_menu("Excluir", "excluir-em-uso.html", "lixeira", perigo=True)]
        usada = f'<a href="parceiros.html">{_n(m["parceiros"], "parceiro")} · {_n(m["revistas"], "revista")}</a>'
        linhas.append(
            (
                f'data-busca="{S.esc(m["nome"])}"',
                [
                    f'<a class="nome" href="matriz-{m["id"]}.html">{m["nome"]}</a>',
                    S.tag(origem, "" if m["origem"] else "cobalto"),
                    f'{m["mecs"]} etapas × componente',
                    (str(m["descritores"]), "num"),
                    usada,
                    m["atualizada"],
                    (S.menu_ic(itens, f"Mais ações de {m['nome']}"), "acoes"),
                ],
            )
        )
    tab = _tb(
        ["Nome", "Origem", "Etapas × componente", ("Descritores", "num"), "Usada por", "Atualizada", ("", "acoes")],
        linhas,
        id_="tab-matrizes",
    )
    vazio = S.vazio(
        "Nenhuma matriz neste ano",
        "Sem matriz, os parceiros não têm descritores nem escalas. Comece de uma matriz do ano anterior ou importe uma nova.",
        S.btn("Abrir uma matriz de 2025", tom="sec", attrs='data-toast="Matriz de 2025 copiada para 2026" data-edita'),
    )
    corpo = (
        S.cab(
            "Matrizes",
            "Os descritores e as escalas que cada parceiro usa. Mudar uma matriz muda as revistas que a usam.",
            S.btn("Nova matriz", "matriz-importar.html", "prim", "mais", attrs='data-p="ped mid adm"'),
        )
        + _leitura("Seu perfil só consulta a biblioteca. Para criar ou alterar uma matriz, peça acesso à equipe Pedagógica ou ao Admin (Diego Rocha).")
        + tab
        + f'<div id="matrizes-vazio" hidden>{vazio}</div>'
        + _dlg_duplicar()
    )
    return S.Pagina("matrizes.html", "Matrizes", "matrizes", corpo, trilha=[("Matrizes", None)])


def _matriz(m):
    mid = m["id"]
    cop = bool(m["origem"])
    ndif = {"vale-verde-2026": 12, "serra-alta-2026": 9}.get(mid, 0)
    tags = S.tag(f"cópia de {m['origem']}", "cobalto", "copiar") if cop else S.tag("importada", "cobalto", "baixar")
    tags += " " + S.tag(_n(m["descritores"], "descritor"))
    if cop and ndif:
        tags += f' <a class="tag tag-alerta" href="matriz-diferencas.html">{S.ic("colunas")}Diferenças ({ndif})</a>'
    tags += f' <span class="mudo">atualizada em {m["atualizada"]}</span>'
    sub = f'<span class="tags-cab">{tags}</span>'
    acoes = (
        S.btn("Duplicar", icone="copiar", attrs=f'data-abrir="dlg-duplicar" data-duplicar="{S.esc(m["nome"])}" data-edita', tom="sec")
        + S.menu(
            "Mais",
            [
                S.item_menu("Reimportar", "matriz-importar.html#reimportar", "subir"),
                "<hr>",
                S.item_menu("Excluir matriz…", "excluir-em-uso.html", "lixeira", perigo=True),
            ],
            "pontos",
        )
    )
    descs = _desc_linhas(m)
    linhas = []
    for i, (e, en, c) in enumerate(LINHAS):
        nrev = len(_rev(mid, c))
        impacto = "dlg-imp-lp" if c == "LP" else "dlg-imp-mt"
        campo = (
            f'<input class="cel cel-caixa" type="number" inputmode="numeric" min="5" step="5" value="{_intervalo(mid, e, c)}" '
            f'aria-label="Intervalo mínimo de {en} {c}" data-edita data-autosave data-impacto="{impacto}">'
        )
        linhas.append(
            (
                "",
                [
                    (f'<a class="nome" href="matriz-etapa.html">{en} · {c}</a>', "rot"),
                    campo,
                    (str(descs[i]), "rot num"),
                    (f'<a href="revistas.html">{nrev}</a>', "rot num"),
                ],
            )
        )
    tab = _tb(
        ["Etapa × componente", "Intervalo mínimo", ("Descritores", "num"), ("Revistas afetadas", "num")], linhas, cls="grade", id_="tab-etapas"
    )
    pars = [p for p in D.PARCEIROS if p["matriz"] == mid]
    chips = "".join(
        f'<a class="par-link" href="{S.href_parceiro(p["id"])}"><span class="sig">{p["sigla"]}</span>{p["nome"]}</a>' for p in pars[:6]
    )
    if len(pars) > 6:
        chips += f'<a class="par-link" href="parceiros.html">e mais {len(pars) - 6}</a>'
    usada = _secao(
        "Usada por",
        f'{_n(m["parceiros"], "parceiro")} · {_n(m["revistas"], "revista")}',
        '<a href="parceiros.html">Ver todos os parceiros</a>',
    )
    perigo = (
        f'<div class="zona-perigo"><p><b>Excluir esta matriz.</b> Só é possível quando nenhum parceiro a usa. '
        f'Hoje {_n(m["parceiros"], "parceiro")} {"a usam" if m["parceiros"] != 1 else "a usa"}.</p>'
        f'{S.btn("Excluir matriz…", "excluir-em-uso.html", "perigo", "lixeira", attrs="data-edita")}</div>'
    )
    lp, mt = _rev(mid, "LP"), _rev(mid, "MT")
    dlgs = ""
    for sfx, rs, comp in (("lp", lp, "LP"), ("mt", mt, "MT")):
        dlgs += _dlg_impacto(
            f"dlg-imp-{sfx}",
            f"Confirme o impacto no intervalo mínimo ({comp})",
            "O intervalo mínimo é a distância mínima entre dois cortes. Mudá-lo revalida os cortes dos parceiros desta matriz.",
            _val(rs),
            f'{_n(len(rs), "revista")} de {comp} usam {m["nome"]}. {_n(len(_val(rs)), "Validada")} {"perdem" if len(_val(rs)) != 1 else "perde"} o Validado:',
        )
    corpo = (
        S.cab(_titulo_edita(m["nome"], "Nome da matriz"), sub, acoes)
        + _leitura("Seu perfil só consulta a biblioteca. Para alterar esta matriz, peça acesso à equipe Pedagógica ou ao Admin (Diego Rocha).")
        + _secao("Etapas × componente", "Abra uma linha para editar os descritores. O intervalo mínimo grava ao sair do campo, depois de você ver o impacto.")
        + tab
        + usada
        + f'<div class="par-links">{chips}</div>'
        + perigo
        + _dlg_duplicar()
        + dlgs
    )
    return S.Pagina(f"matriz-{mid}.html", m["nome"], "matrizes", corpo, trilha=[("Matrizes", "matrizes.html"), (m["nome"], None)], status=True)


# ── Etapa × componente (lista de descritores + detalhe na mesma tela) ─────
_DET = {
    "D01": ("I. Procedimentos de leitura", "Ler palavras e frases curtas com autonomia; reconhecer o suporte do texto (jornal, cartaz, bilhete).",
            "Leitura/escuta (compartilhada e autônoma)", "Compreensão em leitura", "EF15LP03", "EF35LP03",
            ("Localiza a data de um evento em uma notícia curta.", "Localiza o ingrediente pedido em uma receita com lista e modo de preparo.")),
    "D02": ("IV. Coerência e coesão no processamento do texto", "Identificar o referente de um pronome em frases simples.",
            "Leitura/escuta; análise linguística/semiótica", "Construção do sistema alfabético e da coesão", "EF35LP29", "EF05LP27",
            ("Identifica a quem o pronome \"ela\" se refere em um conto.", "Reconhece a palavra que substitui \"a menina\" em uma notícia.")),
    "D03": ("I. Procedimentos de leitura", "Ler textos curtos e usar o contexto para entender palavras novas.",
            "Leitura/escuta (compartilhada e autônoma)", "Estratégias de leitura", "EF35LP05", "EF15LP09",
            ("Descobre o sentido de \"ágil\" em uma frase sobre um atleta.", "Infere o sentido da expressão \"botar a mão na massa\" em uma crônica.")),
    "D04": ("I. Procedimentos de leitura", "Responder perguntas sobre o que o texto diz e o que apenas sugere.",
            "Leitura/escuta (compartilhada e autônoma)", "Compreensão em leitura", "EF35LP04", "EF05LP26",
            ("Conclui que o personagem está triste a partir de suas atitudes.", "Infere o motivo de um atraso em uma carta de leitor.")),
    "D05": ("I. Procedimentos de leitura", "Ler tabelas, gráficos simples e legendas.",
            "Leitura/escuta; análise linguística/semiótica", "Compreensão em leitura de textos multimodais", "EF35LP26", "EF05LP25",
            ("Lê o total em um gráfico de colunas sobre a merenda.", "Relaciona a legenda de uma infografia ao trecho do texto.")),
    "D06": ("II. Implicações do suporte, do gênero e/ou do enunciador", "Dizer sobre o que um texto trata, com as próprias palavras.",
            "Leitura/escuta (compartilhada e autônoma)", "Compreensão em leitura", "EF15LP03", "EF35LP06",
            ("Identifica o assunto de uma reportagem sobre reciclagem.", "Reconhece o tema de um poema sobre a chuva.")),
    "D07": ("III. Relação entre textos", "Separar o que é dado verificável do que é ponto de vista em notícias e comentários.",
            "Leitura/escuta; oralidade", "Apreciação e réplica", "EF05LP19", "EF35LP15",
            ("Distingue o fato da opinião em um comentário sobre o jogo.", "Marca a frase que traz a opinião do autor em uma resenha.")),
    "D08": ("V. Relações entre recursos expressivos e efeitos de sentido", "Reconhecer o que a pontuação comunica: pergunta, surpresa, fala de personagem.",
            "Análise linguística/semiótica", "Pontuação e efeitos de sentido", "EF05LP12", "EF04LP10",
            ("Explica o efeito das reticências em um final de história.", "Reconhece o sentido das aspas em uma manchete.")),
}


def _faixa(ini, fim, maximo=500):
    esq, larg = ini / maximo * 100, (fim - ini) / maximo * 100
    return (
        f'<span class="faixa" role="img" aria-label="Faixa de {ini} a {fim} na escala de 0 a {maximo}" '
        f'title="{ini} a {fim} na escala de 0 a {maximo}"><i style="left:{esq:.1f}%;width:{larg:.1f}%"></i></span>'
    )


def _painel_desc(k, cod, desc, ini, fim):
    top, pre, prat, conh, h1, h2, tarefas = _DET[cod]
    mid = int((ini + fim) / 2 // 5 * 5)
    faixas = [(ini, mid), (mid, fim)]
    ci = lambda extra: f'data-edita data-autosave {extra}'
    linhas = []
    for t, ((a, b), txt) in enumerate(zip(faixas, tarefas), 1):
        arq = f"tarefa-{cod.lower()}-{t}.png"
        linhas.append(
            (
                "",
                [
                    f'<input class="cel cel-caixa" type="number" value="{a}" aria-label="Início da tarefa {t} de {cod}" {ci("")}>',
                    f'<input class="cel cel-caixa" type="number" value="{b}" aria-label="Fim da tarefa {t} de {cod}" {ci("")}>',
                    f'<input class="cel" value="{S.esc(txt)}" aria-label="Texto da tarefa {t} de {cod}" style="min-width:200px" {ci("")}>',
                    f'<span class="arq"><span>{arq}</span><span class="mudo">·</span>'
                    f'<button type="button" class="btn btn-sm btn-fan" data-edita data-toast="Escolha o novo arquivo do item (demo)">Trocar</button></span>',
                    _faixa(a, b),
                    (S.btn_ic("lixeira", f"Remover a tarefa {t} de {cod}", attrs="data-edita data-toast=\"Tarefa removida (demo)\""), "acoes"),
                ],
            )
        )
    tab = _tb(["Início", "Fim", "Texto da tarefa", "Arquivo do item", "Faixa na escala", ("", "acoes")], linhas, cls="grade")
    return f"""
<section class="card card-p painel-desc" data-painel="{k}" hidden aria-label="Descritor {cod}">
  <div class="desc-cab"><h2>{cod} · {S.esc(top.split(". ", 1)[1])}</h2>{S.tag(f"escala {ini} a {fim}", "cobalto")}</div>
  <div class="campos-cod">
    {S.campo("Código", f"cod-{k}", cod, attrs=ci(""))}
    {S.campo("Tópico", f"top-{k}", top, attrs=ci(""))}
  </div>
  {S.campo("Descrição", f"desc-{k}", desc, textarea=True, ajuda="Mudar a descrição muda o texto das revistas de LP que usam esta matriz. Você vê o impacto antes de gravar.", attrs='data-edita data-autosave data-impacto="dlg-impacto" rows="2"')}
  {S.campo("Pré-requisitos", f"pre-{k}", pre, textarea=True, attrs=ci('rows="2"'))}
  <div><h3>BNCC</h3>
    <div class="campos-2 sp">
      {S.campo("Práticas de linguagem", f"bp-{k}", prat, attrs=ci(""))}
      {S.campo("Objeto de conhecimento", f"bk-{k}", conh, attrs=ci(""))}
      {S.campo("Habilidade", f"bh1-{k}", h1, attrs=ci(""))}
      {S.campo("Outra habilidade (opcional)", f"bh2-{k}", h2, attrs=ci(""))}
    </div></div>
  <div><div class="secao-t sem-topo"><div><h3>Tarefas</h3><p>Cada tarefa ocupa uma faixa da escala; o arquivo é a imagem do item na revista.</p></div></div>
    {tab}
    <p class="sp">{S.btn("Adicionar tarefa", icone="mais", attrs='data-edita data-toast="Tarefa adicionada (demo)"')}</p></div>
  <div class="zona-perigo"><p><b>Excluir {cod}.</b> Só é possível quando nenhuma revista o usa; hoje 12 revistas de LP o usam.</p>
    {S.btn("Excluir descritor…", "excluir-em-uso.html", "perigo", "lixeira", attrs="data-edita")}</div>
</section>"""


def _etapa():
    m = M["comunitaria-2026"]
    rs = _rev(m["id"], "LP")
    val = _val(rs)
    cab = S.cab(
        "5º EF · Língua Portuguesa",
        f'{m["nome"]} · escala de 0 a {D.ESCALA_5EF}',
        S.btn("Voltar à matriz", "matriz-comunitaria-2026.html", "sec", "volta"),
    )
    faixa = f"""
<div class="card card-p faixa-ctx" aria-label="Contexto da etapa">
  <label class="bloco"><span class="rot">Intervalo mínimo</span>
    <input class="cel cel-caixa" type="number" min="5" step="5" value="25" aria-label="Intervalo mínimo entre cortes" data-edita data-autosave data-impacto="dlg-impacto-int"></label>
  <div class="bloco"><span class="rot">Afeta</span><span><a href="revistas.html">{_n(len(rs), "revista")}</a> de LP, {_n(len(val), "Validada")}</span></div>
  <div class="bloco"><span class="rot">Escala e cortes de referência ({", ".join(map(str, D.CORTES_5EF_LP))})</span>{S.escala(D.CORTES_5EF_LP, D.ESCALA_5EF, 16)}</div>
</div>"""
    itens = "".join(
        f'<button type="button" role="tab" class="desc-item" data-aba="{c.lower()}" data-busca="{S.esc(c + " " + d)}" aria-selected="{"true" if i == 0 else "false"}">'
        f"<b>{c}</b><span>{S.esc(d)}</span></button>"
        for i, (c, d, *_r) in enumerate(D.DESCRITORES_5EF_LP)
    )
    lista = f"""
<div class="col-lista">
  <div class="linha">
    <label class="campo" style="flex:1;min-width:0"><span class="sr">Buscar descritor</span>
      <input class="input" type="search" placeholder="Buscar descritor" data-filtro="#lista-desc" aria-label="Buscar descritor"></label>
  </div>
  <div class="linha-sp"><span class="mudo"><span data-contagem="#lista-desc">{len(D.DESCRITORES_5EF_LP)}</span> descritores</span>
    {S.btn("Novo descritor", icone="mais", attrs='data-abrir="dlg-novo-desc" data-edita', cls="btn-sm")}</div>
  <div class="lista-sel lista-desc" id="lista-desc" role="tablist" aria-orientation="vertical" data-abas>{itens}</div>
</div>"""
    paineis = "".join(_painel_desc(c.lower(), c, d, a, b) for c, d, a, b in D.DESCRITORES_5EF_LP)
    dlg_novo = S.dialogo(
        "dlg-novo-desc",
        "Novo descritor",
        S.campo("Código", "novo-cod", "D09", attrs="data-edita")
        + S.campo("Descrição", "novo-desc", "", textarea=True, attrs='data-edita rows="2" placeholder="O que o estudante sabe fazer"'),
        '<button type="button" class="btn" data-fechar>Cancelar</button>'
        '<button type="button" class="btn btn-prim" data-toast="D09 criado. Preencha a BNCC e as tarefas." data-fechar data-edita>Criar descritor</button>',
    )
    dlgs = _dlg_impacto(
        "dlg-impacto",
        "Confirme o impacto na descrição",
        "A descrição aparece no texto das revistas de LP que usam a Comunitária 2026.",
        val,
        f'{_n(len(rs), "revista")} mudam. {_n(len(val), "Validada")} {"perdem" if len(val) != 1 else "perde"} o Validado:',
    ) + _dlg_impacto(
        "dlg-impacto-int",
        "Confirme o impacto no intervalo mínimo",
        "Mudar o intervalo mínimo revalida os cortes de 5º EF · LP de todos os parceiros desta matriz.",
        val,
        f'{_n(len(rs), "revista")} são revalidadas. {_n(len(val), "Validada")} {"perdem" if len(val) != 1 else "perde"} o Validado:',
    )
    corpo = (
        cab
        + _leitura("Seu perfil só consulta a biblioteca. Para alterar esta etapa, peça acesso à equipe Pedagógica ou ao Admin (Diego Rocha).")
        + faixa
        + f'<div class="dividido dividido-desc">{lista}<div class="det-col">{paineis}</div></div>'
        + dlg_novo
        + dlgs
    )
    return S.Pagina(
        "matriz-etapa.html",
        "5º EF · Língua Portuguesa",
        "matrizes",
        corpo,
        trilha=[("Matrizes", "matrizes.html"), ("Comunitária 2026", "matriz-comunitaria-2026.html"), ("5º EF · LP", None)],
        status=True,
    )


# ── Criar e importar (uma página, três blocos numerados) ──────────────────
def _importar():
    m = M["comunitaria-2026"]
    ops = "".join(
        f'<option value="{x["id"]}" data-nome="{S.esc(x["nome"])}" data-rev="{len(_rev(x["id"]))}" data-val="{len(_val(_rev(x["id"])))}" '
        f'data-desc="{x["descritores"]}" data-mecs="{x["mecs"]}">{x["nome"]}</option>'
        for x in D.MATRIZES
    )
    cab = (
        '<header class="cab"><div class="cab-txt">'
        '<h1><span data-so-modo="novo">Criar e importar matriz</span><span data-so-modo="reimp" hidden>Reimportar matriz</span></h1>'
        '<p class="sub"><span data-so-modo="novo">Dê um nome e envie o arquivo. A matriz já nasce com as etapas e os descritores.</span>'
        '<span data-so-modo="reimp" hidden>Envie o arquivo novo. A matriz escolhida é apagada e recriada a partir dele.</span></p>'
        "</div></header>"
    )
    p1 = f"""
<li data-passo="1"><span class="seq-n">1</span><div class="seq-corpo">
  <h2>Nome</h2>
  <div data-so-modo="novo">{S.campo("Nome da matriz", "nome", "", attrs='id="imp-nome" placeholder="Ex.: Comunitária 2027" data-edita')}</div>
  <div data-so-modo="reimp" hidden>
    <label class="campo"><span class="rot">Matriz a substituir</span><select class="select" id="imp-matriz" data-edita>{ops}</select></label></div>
</div></li>"""
    p2 = """
<li data-passo="2"><span class="seq-n">2</span><div class="seq-corpo">
  <h2>Arquivo</h2>
  <label class="soltar" id="imp-soltar">
    <input type="file" id="imp-arquivo" accept=".pdf,.xlsx" data-edita>
    <span class="soltar-ic">""" + S.ic("subir") + """</span>
    <b>Solte o PDF ou a planilha XLSX aqui</b>
    <span class="mudo">ou clique para escolher. Até 20 MB.</span>
  </label>
  <p class="sp" id="imp-erro" role="alert" hidden></p>
  <p class="arq-ok" id="imp-arq-ok" hidden>""" + S.ic("confirmado") + """<span id="imp-arq-nome"></span>
    <button type="button" class="btn btn-sm btn-fan" id="imp-trocar" data-edita>Trocar</button></p>
  <p class="sp" id="imp-exemplo-p"><button type="button" class="btn btn-sm btn-fan" id="imp-exemplo" data-edita>Usar um arquivo de exemplo</button></p>
</div></li>"""
    p3 = f"""
<li data-passo="3"><span class="seq-n">3</span><div class="seq-corpo">
  <h2>Confirmação</h2>
  <div data-so-modo="novo"><p>Conferiu o nome e o arquivo? Ao criar, a matriz aparece na lista e fica disponível para ligar a parceiros.</p></div>
  <div data-so-modo="reimp" hidden>
    {S.campo("Digite o nome da matriz para confirmar", "conf", "", attrs='id="imp-confirma" autocomplete="off" data-edita', ajuda='Escreva exatamente: <b id="imp-conf-nome">Comunitária 2026</b>. Isso evita apagar a matriz errada.')}</div>
  <div class="linha sp">
    <a class="btn btn-prim" id="imp-ir" href="matriz-comunitaria-2026.html" aria-disabled="true" data-edita>
      <span data-so-modo="novo">Criar e importar</span><span data-so-modo="reimp" hidden>Importar e substituir</span></a>
    <a class="btn btn-fan" href="matrizes.html">Cancelar</a>
    <span class="ajuda" id="imp-falta" aria-live="polite"></span></div>
</div></li>"""
    resumo = f"""
<aside class="card card-p resumo-imp" aria-label="O que vai acontecer">
  <h2>O que vai acontecer</h2>
  <div data-so-modo="novo">
    <p class="mudo" data-so-arq="sem">Escolha o arquivo no passo 2 para ver o que será criado.</p>
    <ul class="resumo-lista" data-so-arq="com" hidden>
      <li>{S.ic("ok")}<span>Cria a matriz <b id="sum-nome">nova</b></span></li>
      <li>{S.ic("ok")}<span>Vai criar <b>8 etapas × componente</b> e <b>142 descritores</b></span></li>
      <li>{S.ic("info")}<span>Nenhuma revista muda: a matriz só vale depois de ligada a um parceiro.</span></li>
    </ul>
  </div>
  <div data-so-modo="reimp" hidden>
    <div class="aviso aviso-alerta" role="status">{S.ic("alerta")}<div class="aviso-txt"><b>Apaga e recria.</b> Afeta <b id="sum-rev">{_n(len(_rev(m["id"])), "revista")}</b>; <b id="sum-val">{_n(len(_val(_rev(m["id"]))), "Validada")}</b> perdem o Validado e voltam para Conferir.</div></div>
    <ul class="resumo-lista">
      <li>{S.ic("ok")}<span>Recria <b id="sum-mecs">{m["mecs"]} etapas × componente</b> e <b id="sum-desc">{m["descritores"]} descritores</b></span></li>
      <li>{S.ic("ok")}<span>Antes de apagar, guarda a matriz atual como <b>“<span id="sum-copia">{m["nome"]}</span> (antes de {HOJE})”</b>, só para consulta.</span></li>
      <li>{S.ic("info")}<span>Cortes e variáveis dos parceiros não mudam. Cortes fora do novo intervalo mínimo viram pendência.</span></li>
    </ul>
    <p><a href="revistas.html">Ver as revistas afetadas</a></p>
  </div>
</aside>"""
    corpo = (
        '<div data-importar>'
        + cab
        + _leitura("Seu perfil só consulta a biblioteca. Para importar uma matriz, peça acesso à equipe Pedagógica ou ao Admin (Diego Rocha).")
        + f'<div class="importar" id="reimportar"><ol class="seq">{p1}{p2}{p3}</ol>{resumo}</div></div>'
    )
    return S.Pagina("matriz-importar.html", "Criar e importar matriz", "matrizes", corpo, trilha=[("Matrizes", "matrizes.html"), ("Criar e importar", None)])


# ── Diferenças em relação à origem ────────────────────────────────────────
def _diferencas():
    vv, cm = M["vale-verde-2026"], M["comunitaria-2026"]
    d5, d9, m3 = "5EF LP", "9EF LP", "3EM MT"
    rot = {d5: "5º EF · LP", d9: "9º EF · LP", m3: "3º EM · MT"}
    L = [
        (d5, "D03", "Descrição", "Inferir o sentido de palavra ou expressão <del>pelo contexto</del>.", "Inferir o sentido de palavra ou expressão <ins>pelo contexto e pelas ilustrações</ins>."),
        (d5, "D05", "Faixa na escala", "<del>225 a 300</del>", "<ins>225 a 325</ins>"),
        (d5, "D09", "Descritor novo", "não existe", "<ins>D09 · Reconhecer recursos expressivos em poemas.</ins>"),
        (d5, "D07", "Pré-requisitos", "Ler tabelas, gráficos simples e <del>legendas</del>.", "Ler tabelas, gráficos simples e <ins>legendas e manchetes</ins>."),
        (d5, "Etapa", "Intervalo mínimo", "<del>25</del>", "<ins>20</ins>"),
        (d9, "D11", "Descrição", "Reconhecer <del>o gênero</del> de um texto.", "Reconhecer <ins>o gênero e o suporte</ins> de um texto."),
        (d9, "D14", "Descritor removido", "<del>D14 · Identificar o narrador de um conto.</del>", "não existe"),
        (d9, "D02", "BNCC · habilidade", "<del>EF69LP03</del>", "<ins>EF69LP04</ins>"),
        (d9, "Etapa", "Intervalo mínimo", "<del>25</del>", "<ins>20</ins>"),
        (m3, "D05", "Arquivo do item", "<del>tarefa-d05-1.png</del>", "<ins>tarefa-d05-1-v2.png</ins>"),
        (m3, "D08", "Descrição", "Resolver problema com <del>porcentagem</del>.", "Resolver problema com <ins>porcentagem e juros simples</ins>."),
        (m3, "D12", "Descritor novo", "não existe", "<ins>D12 · Interpretar gráfico de função afim.</ins>"),
    ]
    linhas = []
    for k, (et, cod, oque, orig, nova) in enumerate(L):
        onde = f"{rot[et]} · {cod}" if cod != "Etapa" else f"{rot[et]}"
        onde = f'<a href="matriz-etapa.html">{onde}</a>' if et == d5 else onde
        tipo = {"Descritor novo": "ok", "Descritor removido": "erro"}.get(oque, "")
        linhas.append(
            (
                f'data-busca="{S.esc(rot[et] + " " + cod + " " + oque)}" data-etapa="{et}"',
                [(onde, ""), S.tag(oque, tipo), (orig, "quebra"), (nova, "quebra")],
            )
        )
    tab = _tb(["Onde", "O quê", "Na origem (Comunitária 2026)", "Nesta matriz (Vale Verde 2026)"], linhas, id_="tab-dif")
    opcoes = '<option value="">Todas as etapas × componente</option>' + "".join(f'<option value="{k}">{v}</option>' for k, v in rot.items())
    filtro = (
        f'<div class="linha mb"><label class="campo-linha"><span>Mostrar</span>'
        f'<select class="select" data-alvo="#tab-dif" data-filtra="etapa" aria-label="Filtrar por etapa × componente">{opcoes}</select></label>'
        f'<span class="mudo"><span data-contagem="#tab-dif">12</span> de 12 diferenças</span></div>'
    )
    corpo = (
        S.cab(
            f'Diferenças de {vv["nome"]} em relação à {cm["nome"]}',
            "Compare o que foi alterado depois da cópia. Mudanças na origem não chegam sozinhas à cópia.",
            S.btn("Voltar à matriz", "matriz-vale-verde-2026.html", "sec", "volta"),
        )
        + f'<p class="resumo-dif mb">{S.ic("colunas")}<b>12 diferenças em 3 etapas × componente</b>'
        f' <span class="mudo">· 5 em 5º EF · LP, 4 em 9º EF · LP, 3 em 3º EM · MT</span></p>'
        + filtro
        + tab
    )
    return S.Pagina(
        "matriz-diferencas.html",
        "Diferenças de Vale Verde 2026",
        "matrizes",
        corpo,
        trilha=[("Matrizes", "matrizes.html"), ("Vale Verde 2026", "matriz-vale-verde-2026.html"), ("Diferenças", None)],
    )


# ── Templates ─────────────────────────────────────────────────────────────
def _href_tpl(t):
    return "template-lp-f1.html" if t["fasc"] == "F1" else "template-lp-f2.html"


def _dlg_novo_template():
    corpo = (
        '<div class="campos-2">'
        + S.selecao("Componente", "comp", [("LP", "Língua Portuguesa"), ("MT", "Matemática")], attrs="data-edita")
        + S.selecao("Fascículo", "fasc", [("F1", "F1 · escalas de proficiência"), ("F2", "F2 · infográfico")], attrs="data-edita")
        + "</div>"
        + S.campo("Nome", "nome", "", attrs='placeholder="Ex.: LP · F1 · Município 2027" data-edita')
        + '<p class="ajuda">O template novo nasce vazio, na versão 1. Para partir de um existente, use Duplicar no menu da linha.</p>'
    )
    rod = (
        '<button type="button" class="btn" data-fechar>Cancelar</button>'
        '<button type="button" class="btn btn-prim" data-toast="Template criado na versão 1" data-fechar data-edita>Criar template</button>'
    )
    return S.dialogo("dlg-novo-template", "Novo template", corpo, rod)


def _templates():
    corpo_t = ""
    for comp, nome in D.COMPONENTES:
        ts = sorted([t for t in D.TEMPLATES if t["comp"] == comp], key=lambda t: (t["fasc"], t["nome"]))
        corpo_t += f'<tr class="grupo"><td colspan="6">{nome} · {_n(len(ts), "template")}</td></tr>'
        for t in ts:
            copias = f' <span class="mudo">· {_n(t["copias"], "com cópia de seção", "com cópia de seção")}</span>' if t["copias"] else ""
            itens = [
                S.item_menu("Versões", _href_tpl(t) + "#versoes", "historico"),
                S.item_menu("Duplicar", icone="copiar", attrs=f'data-toast="Template duplicado: {S.esc(t["nome"])} (cópia)" data-edita'),
                "<hr>",
                S.item_menu("Excluir", "excluir-em-uso.html", "lixeira", perigo=True),
            ]
            corpo_t += (
                f'<tr><td><a class="nome" href="{_href_tpl(t)}">{t["nome"]}</a></td><td>{S.tag(t["fasc"], "cobalto")}</td>'
                f'<td>v{t["versao"]}</td><td><a href="revistas.html">{_n(t["usado"], "revista")}</a>{copias}</td>'
                f'<td>{t["atualizado"]}</td><td class="acoes">{S.menu_ic(itens, "Mais ações de " + t["nome"])}</td></tr>'
            )
    tab = (
        '<div class="tab-caixa"><table class="tabela"><thead><tr><th>Nome</th><th>Fascículo</th><th>Versão</th><th>Usado por</th>'
        f'<th>Atualizado</th><th></th></tr></thead><tbody>{corpo_t}</tbody></table></div>'
    )
    corpo = (
        S.cab(
            "Templates",
            "Os textos-modelo das revistas. Cada template tem versões; mudar um texto muda as revistas que o usam.",
            S.btn("Novo template", icone="mais", tom="prim", attrs='data-abrir="dlg-novo-template" data-p="ped mid adm"'),
        )
        + _leitura("Seu perfil só consulta a biblioteca. Para alterar um template, peça acesso à equipe Pedagógica ou ao Admin (Diego Rocha).")
        + tab
        + _dlg_novo_template()
    )
    return S.Pagina("templates.html", "Templates", "templates", corpo, trilha=[("Templates", None)])


_EXTRA_VARS = [("ano", "Ano da temporada"), ("nome_parceiro", "Nome do parceiro"), ("pd03", "Nome do Padrão 03"), ("pd04", "Nome do Padrão 04")]
_VAR_RE = re.compile(r"\{\{\s*([a-z0-9_]+)\s*\}\}", re.I)


def _vars():
    v = {re.sub(r"[{}]", "", ph): rot for _, rot, _, ph, _ in D.VARIAVEIS}
    v.update(dict(_EXTRA_VARS))
    return v


def _amostras():
    def base(pid, nome):
        g = lambda k: D.variavel(pid, k)
        return {
            "ano": str(D.ANO), "nome_parceiro": nome, "issn": g("colecao"), "adj_masc_sing": g("pat_m"), "adj_fem_sing": g("pat_f"),
            "programa": g("programa"), "secretaria": g("secretaria"), "regional": g("regional"),
            "pd01": g("pd01"), "pd02": g("pd02"), "pd03": "Adequado", "pd04": "Avançado",
        }
    vv = base("vale-verde", "Vale Verde")
    bt = base("boa-terra", "Boa Terra")
    bt["secretaria"] = ""
    bt["regional"] = ""
    return {"vv": vv, "bt": bt}


def _erros(txt):
    vs = _vars()
    return sorted({m.group(1) for m in _VAR_RE.finditer(txt) if m.group(1) not in vs})


_VERSOES = {
    "F1": [
        ("Ana Souza", "03/11 11:02", "Introdução cita o programa e o adjetivo pátrio em vez do nome genérico."),
        ("Elisa Prado", "27/10 16:40", "Fechamento fala da secretaria e da recomposição das aprendizagens."),
        ("Ana Souza", "14/10 09:15", "Título da introdução passa a trazer o ano e o parceiro."),
        ("Bruno Lima", "02/10 14:30", "Versão inicial, importada do modelo de 2025."),
    ],
    "F2": [
        ("Elisa Prado", "09/11 15:44", "Passo 2 usa a regional do parceiro."),
        ("Bruno Lima", "21/10 10:20", "Versão inicial, importada do modelo de 2025."),
    ],
}
_DIFFS = {
    "F1": {
        "A": ("Introdução", "Esta revista apresenta os resultados do <del>programa estadual</del> para a rede <del>pública</del>.",
              "Esta revista apresenta os resultados do <ins>{{programa}}</ins> para a rede <ins>{{adj_fem_sing}}</ins>."),
        "B": ("Fechamento", "A <del>secretaria</del> e as equipes <del>de ensino</del> podem usar estas páginas para <del>planejar o ano letivo</del>.",
              "A <ins>{{secretaria}}</ins> e as equipes <ins>pedagógicas</ins> podem usar estas páginas para <ins>planejar a recomposição das aprendizagens</ins>."),
        "C": ("Título da Introdução", "<del>Resultados</del>", "<ins>Resultados de {{ano}} em {{nome_parceiro}}</ins>"),
        "por_versao": {3: "A", 2: "AB", 1: "ABC"},
    },
    "F2": {
        "A": ("Passo 2", "Veja como a habilidade evolui <del>do 1º ano</del> ao 3º ano do Ensino Médio.",
              "Veja como a habilidade evolui <ins>da {{regional}}</ins> ao 3º ano do Ensino Médio."),
        "por_versao": {1: "A"},
    },
}


def _gaveta_versoes(t):
    fasc, atual = t["fasc"], t["versao"]
    pessoas = {p["nome"]: p for p in D.PESSOAS}
    itens = ""
    for i, (autor, quando, nota) in enumerate(_VERSOES[fasc]):
        v = atual - i
        atual_tag = " " + S.tag("atual", "ok") if i == 0 else ""
        cab = f'<div class="lt-cab"><b>v{v}</b>{atual_tag}<span class="mudo">{S.avatar(pessoas[autor])}{autor} · {quando}</span></div>'
        acoes = ""
        if i > 0:
            blocos = ""
            for k in _DIFFS[fasc]["por_versao"][v]:
                sec, esq, dir_ = _DIFFS[fasc][k]
                blocos += (
                    f'<div class="comp-sec"><b>{sec}</b><div class="diff"><div><h4>v{v}</h4>{esq}</div><div><h4>v{atual} (atual)</h4>{dir_}</div></div></div>'
                )
            acoes = (
                '<div class="lt-acoes">'
                f'<button type="button" class="btn btn-sm" data-toast="Abrindo a v{v} só para leitura (demo)">{S.ic("olho")}Ver</button>'
                f'<details class="comp"><summary class="btn btn-sm">{S.ic("colunas")}Comparar com a atual</summary>{blocos}</details>'
                f'<button type="button" class="btn btn-sm btn-fan" data-edita data-toast="v{v} copiada como rascunho. Salve para criar a versão {atual + 1}.">Restaurar como rascunho</button>'
                "</div>"
            )
        itens += f"<li>{cab}<p>{nota}</p>{acoes}</li>"
    corpo = f'<p class="mudo">Cada versão guarda os textos como estavam. Revistas com cópia de seção não acompanham as versões novas.</p><ol class="linha-tempo">{itens}</ol>'
    return S.gaveta("versoes", f"Versões de {t['nome']}", corpo)


def _template(t):
    fasc, ver = t["fasc"], t["versao"]
    nxt = ver + 1
    secoes = [list(s) for s in (D.SECOES_F1 if fasc == "F1" else D.SECOES_F2)]
    if fasc == "F2":  # ponytail: rascunho com erro de propósito, para mostrar a validação e o bloqueio de salvar
        for s in secoes:
            if s[0] == "passo3":
                s[3] += " Compare as etapas em {{nome_regiao}}."
    selec = "passo3" if fasc == "F2" else secoes[0][0]
    vs = _vars()
    erros = {s[0]: _erros(s[2] + " " + s[3]) for s in secoes}
    n_err = sum(len(e) for e in erros.values())
    primeiro_err = next((s[1] for s in secoes if erros[s[0]]), "")

    # impacto (números do dado + validadas calculadas das revistas da demo)
    comp_rs = [r for r in D.REVISTAS if r["comp"] == t["comp"]]
    val = _val(comp_rs)
    nv = len(val)
    cop_txt = f'{t["copias"]} com cópia (não mudam)' if t["copias"] else "nenhuma com cópia"
    impacto_txt = (
        f'Afeta <b>{_n(t["usado"], "revista")}</b> · {cop_txt} · '
        f'<b>{_n(nv, "Validada")}</b> {"perdem" if nv != 1 else "perde"} o Validado'
    )
    outras = t["usado"] - t["copias"] - nv
    copias_nomes = ", ".join(S.nome_revista(r) for r in [r for r in comp_rs if r["fase"] < 4][: t["copias"]])

    idx_btn, paineis = "", ""
    for sid, rot, titulo, texto in secoes:
        e = erros[sid]
        sel = "true" if sid == selec else "false"
        status = S.tag(_n(len(e), "erro"), "erro") if e else S.st("ok", "Sem erros")
        idx_btn += (
            f'<button type="button" role="tab" class="sec-item" data-aba="{sid}" aria-selected="{sel}">'
            f'<span class="sec-nome">{S.esc(rot)}</span><span data-idx="{sid}">{status}</span></button>'
        )
        opcoes = '<option value="">Variável…</option>' + "".join(f'<option value="{k}">{r} ({{{{{k}}}}})</option>' for k, r in vs.items())
        paineis += f"""
<section class="card card-p secao-ed" data-painel="{sid}"{"" if sid == selec else " hidden"}>
  <div class="linha"><span class="chip-travado" title="O nome da seção é fixo">{S.ic("cadeado")}{S.esc(rot)}</span>
    <span class="ajuda">Nome fixo: é por ele que a revista encontra o texto.</span></div>
  {S.campo("Título", f"t-{sid}", titulo, attrs='data-campo="titulo" data-edita data-autosave')}
  <div class="campo"><span class="rot" id="rot-{sid}">Texto</span>
    <div class="barra-fmt" role="toolbar" aria-label="Formatação do texto">
      <button type="button" class="btn btn-sm btn-fan" data-fmt="n" aria-label="Negrito" title="Negrito" data-edita><b>N</b></button>
      <button type="button" class="btn btn-sm btn-fan" data-fmt="i" aria-label="Itálico" title="Itálico" data-edita><i>I</i></button>
      <button type="button" class="btn btn-sm btn-fan" data-fmt="l" aria-label="Lista" title="Lista" data-edita>{S.ic("lista")}</button>
      <select class="select" data-var-ins aria-label="Inserir variável no texto" data-edita>{opcoes}</select>
    </div>
    <textarea class="textarea" data-campo="texto" aria-labelledby="rot-{sid}" data-edita data-autosave rows="9">{S.esc(texto)}</textarea>
    <span class="ajuda">Use <b>**negrito**</b>, <b>*itálico*</b> e linhas começando com <b>-</b> para listas. Variáveis ficam entre chaves duplas.</span></div>
</section>"""

    add = ""
    if fasc == "F2":
        add = (
            '<div class="add-sec">'
            + S.btn("Adicionar passo", icone="mais", cls="btn-sm", attrs='data-edita data-toast="Passo 4 adicionado ao fim da lista (demo)"')
            + S.btn("Adicionar diálogo", icone="mais", cls="btn-sm", attrs='data-edita data-toast="Diálogo adicionado ao fim da lista (demo)"')
            + "</div>"
        )
    ops_pv = '<option value="vv">Vale Verde (tudo preenchido)</option><option value="bt">Boa Terra (2 variáveis vazias)</option>'
    tags = (
        f'<span class="tags-cab">{S.tag(f"v{ver}", "cobalto")}{S.tag(f"atualizado {t["atualizado"][:5]}")}'
        f'{S.tag(t["comp"] + " · " + fasc)}<span class="mudo">usado por {_n(t["usado"], "revista")}</span></span>'
    )
    mais = S.menu(
        "Mais",
        [
            S.item_menu("Duplicar template", icone="copiar", attrs='data-toast="Template duplicado (demo)" data-edita'),
            "<hr>",
            S.item_menu("Excluir template…", "excluir-em-uso.html", "lixeira", perigo=True),
        ],
        "pontos",
    )
    erro_vis = "" if n_err else " hidden"
    barra = f"""
<div class="barra-acao" role="region" aria-label="Salvar uma versão">
  <div class="linha">
    <button type="button" class="btn" data-abrir="versoes">{S.ic("historico")}Versões <span class="n-ver">{ver}</span></button>
    <span class="ajuda">Seus ajustes ficam em rascunho. Só a versão {nxt} muda as revistas.</span></div>
  <div class="linha" data-p="ped mid adm">
    <span class="impacto erro" id="sv-erro"{erro_vis}>{S.ic("alerta")}<span id="sv-erro-txt">{_n(n_err, "erro")} {"em " + primeiro_err if primeiro_err else ""}: corrija para salvar</span></span>
    <span class="impacto" id="sv-imp">{S.ic("alerta")}<span>{impacto_txt}</span></span>
    <button type="button" class="btn btn-prim" id="salvar-versao" data-abrir="dlg-versao" aria-disabled="{"true" if n_err else "false"}">Salvar versão {nxt}</button>
  </div>
</div>"""
    dados = (
        f'data-modelo data-vars="{S.esc(json.dumps(vs, ensure_ascii=False))}" '
        f'data-amostras="{S.esc(json.dumps(_amostras(), ensure_ascii=False))}" data-prox="{nxt}"'
    )
    corpo = (
        S.cab(_titulo_edita(t["nome"], "Nome do template"), tags, mais)
        + _leitura("Seu perfil só consulta os templates. Para criar uma versão, peça acesso à equipe Pedagógica ou ao Admin (Diego Rocha).")
        + barra
        + f"""
<div class="modelo" {dados}>
  <div class="col-idx"><p class="mudo ti">{_n(len(secoes), "seção", "seções")}</p>
    <div class="lista-sel" role="tablist" aria-orientation="vertical" data-abas>{idx_btn}</div>{add}</div>
  <div class="col-ed">{paineis}</div>
  <div class="pv-col">
    <div class="pv-cab"><h2>Pré-visualização</h2>
      <label class="campo-linha"><span class="mudo">Com os dados de</span><select class="select" id="pv-parceiro" aria-label="Parceiro de exemplo">{ops_pv}</select></label></div>
    <article class="pv" id="pv" aria-live="polite"></article>
    <div id="pv-valida"></div>
  </div>
</div>"""
        + S.dialogo(
            "dlg-versao",
            "Confirme o impacto",
            f'<p>Ao criar a versão {nxt}, o texto novo vale para todas as revistas que usam <b>{t["nome"]}</b>.</p>'
            f'<ul class="resumo-lista"><li>{S.ic("ok")}<span><b>{_n(t["usado"] - t["copias"], "revista")}</b> passam a usar a versão {nxt}</span></li>'
            f'<li>{S.ic("info")}<span>{cop_txt[0].upper() + cop_txt[1:] if t["copias"] else "Nenhuma revista tem cópia de seção"}'
            f'{": " + copias_nomes if copias_nomes else ""}</span></li>'
            f'<li>{S.ic("alerta")}<span><b>{_n(nv, "Validada")}</b> {"perdem" if nv != 1 else "perde"} o Validado e voltam para Conferir'
            f'{"; as outras " + str(outras) + " ainda não tinham Validado" if outras > 0 else ""}:</span></li></ul>'
            + _lista_impacto(val)
            + S.campo("Nota da versão", "nota", "", attrs='placeholder="O que mudou? Aparece no histórico." data-edita'),
            '<button type="button" class="btn" data-fechar>Voltar e editar</button>'
            f'<button type="button" class="btn btn-prim" data-toast="Versão {nxt} criada. {_n(nv, "revista")} {"voltaram" if nv != 1 else "voltou"} para Conferir." data-fechar data-salva data-edita>Confirmar e criar versão {nxt}</button>',
            largo=False,
        )
        + _gaveta_versoes(t)
    )
    arq = "template-lp-f1.html" if fasc == "F1" else "template-lp-f2.html"
    return S.Pagina(arq, t["nome"], "templates", corpo, trilha=[("Templates", "templates.html"), (t["nome"], None)], status=True, largura="larga")


# ── Estilos e scripts desta biblioteca ────────────────────────────────────
CSS = """
/* ── Biblioteca: Matrizes e Templates ─────────────────────────────────── */
.mb{margin-bottom:16px}.sp{margin-top:12px}.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.edita-inline{position:relative;display:inline-flex;align-items:center;gap:4px;max-width:100%}
.edita-inline .input{font:inherit;font-size:24px;font-weight:650;letter-spacing:-.02em;height:42px;border-color:transparent;background:transparent;padding:0 8px;margin-left:-8px;
  width:auto;min-width:12ch;max-width:100%;field-sizing:content;text-overflow:ellipsis}
.edita-inline .input:hover{border-color:var(--fio-2);background:var(--papel)}
.edita-inline .ic{color:var(--txt-2);pointer-events:none;flex:none}
.tags-cab{display:inline-flex;gap:6px;flex-wrap:wrap;align-items:center}
a.tag{text-decoration:none}a.tag:hover{background:var(--cobalto-fundo);color:var(--cobalto-2)}
a.tag-alerta:hover{background:oklch(0.94 0.07 85);color:var(--alerta)}
.secao-t{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin:26px 0 10px;flex-wrap:wrap}
.secao-t > div > p{color:var(--txt-2);margin-top:2px;max-width:74ch}
.secao-t.sem-topo{margin-top:0}
.par-links{display:flex;flex-wrap:wrap;gap:8px}
.par-link{display:inline-flex;align-items:center;gap:8px;height:34px;padding:0 12px 0 5px;border:1px solid var(--fio);background:var(--papel);border-radius:99px;color:var(--txt);text-decoration:none;font-weight:550}
.par-link:hover{border-color:var(--cobalto-fio);color:var(--cobalto)}
.par-link .sig{display:grid;place-items:center;width:24px;height:24px;border-radius:50%;background:var(--tela-2);font-size:11px;font-weight:650;color:var(--txt-2)}
.par-link:not(:has(.sig)){padding-left:12px}
.zona-perigo{display:flex;align-items:center;gap:16px;justify-content:space-between;flex-wrap:wrap;margin-top:26px;padding-top:14px;border-top:1px solid var(--fio)}
.zona-perigo p{max-width:72ch;color:var(--txt-2)}.zona-perigo b{color:var(--txt)}
.cel-caixa{width:92px;min-width:0;height:30px;margin:4px 12px;border:1px solid var(--fio-2);border-radius:6px;background:var(--papel);text-align:right}
td > .cel:not(.cel-caixa){width:100%}
.cel-caixa:focus{outline-offset:0}
.grade td.rot.num{text-align:right}
.grade .nome{font-weight:600}
.grade td a.nome{color:var(--txt);text-decoration:none}.grade td a.nome:hover{color:var(--cobalto);text-decoration:underline}
.lista-imp{list-style:none;margin:0;padding:0;display:grid;border:1px solid var(--fio);border-radius:var(--raio)}
.lista-imp li{display:flex;align-items:center;gap:10px;padding:9px 12px;border-bottom:1px solid var(--fio);flex-wrap:wrap}
.lista-imp li:last-child{border-bottom:0}
.lista-imp a{font-weight:600;color:var(--txt);text-decoration:none}.lista-imp a:hover{color:var(--cobalto);text-decoration:underline}
.lista-imp .vai{margin-left:auto;display:inline-flex;gap:8px;align-items:center;color:var(--txt-2);font-size:13px}
.lista-imp .vai .ic{width:14px;height:14px;opacity:.6}
.num-imp{font-weight:600}
.campo-linha{display:inline-flex;align-items:center;gap:8px;font-size:13px}.campo-linha .select{width:auto;min-width:200px}

/* etapa × componente */
.faixa-ctx{display:grid;grid-template-columns:auto auto minmax(260px,1fr);gap:16px 32px;align-items:center;margin-bottom:20px}
.faixa-ctx .bloco{display:grid;gap:5px}.faixa-ctx .rot{font-weight:600;font-size:13px}
.faixa-ctx .cel-caixa{margin:0;text-align:left;padding:0 10px}
.dividido-desc{grid-template-columns:320px minmax(0,1fr)}
.col-lista{display:grid;gap:10px;align-content:start;position:sticky;top:68px}
.linha-sp{display:flex;align-items:center;justify-content:space-between;gap:8px}
.lista-desc{max-height:calc(100vh - 230px);overflow:auto}
.desc-item{align-items:flex-start!important}
.desc-item b{min-width:34px;color:var(--cobalto-2)}
.desc-item span{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;color:var(--txt)}
.lista-sel [aria-selected="true"]{background:var(--cobalto-fundo)}
.painel-desc{display:grid;grid-template-columns:minmax(0,1fr);gap:18px}
.det-col{min-width:0}
.desc-cab{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:space-between}
.campos-cod{display:grid;grid-template-columns:130px minmax(0,1fr);gap:14px}
.faixa{position:relative;display:block;height:8px;border-radius:4px;background:var(--tela-2);border:1px solid var(--fio);min-width:96px;margin:0 12px}
.faixa i{position:absolute;top:-1px;bottom:-1px;background:var(--cobalto);border-radius:4px;min-width:4px}
.arq{display:inline-flex;align-items:center;gap:4px;color:var(--txt-2);padding:0 8px}
.painel-desc .cel-caixa{width:68px;margin:4px 6px}
.gaveta:not([open]){display:none}

/* criar e importar */
.importar{display:grid;grid-template-columns:minmax(0,1fr) 340px;gap:20px;align-items:start}
.seq{display:grid;gap:14px;list-style:none;margin:0;padding:0}
.seq > li{display:grid;grid-template-columns:30px minmax(0,1fr);gap:14px;padding:18px;background:var(--papel);border:1px solid var(--fio);border-radius:var(--raio-g)}
.seq-corpo{display:grid;gap:12px;min-width:0;align-content:start}
.seq-n{display:grid;place-items:center;width:28px;height:28px;border-radius:50%;background:var(--cobalto-fundo);color:var(--cobalto-2);font-weight:650}
.seq > li[data-feito="true"] .seq-n{background:var(--ok);color:#fff}
.soltar{position:relative;display:grid;justify-items:center;gap:4px;padding:26px 16px;border:1.5px dashed var(--fio-2);border-radius:var(--raio-g);background:var(--tela);text-align:center;cursor:pointer}
.soltar:hover,.soltar.sobre{border-color:var(--cobalto);background:var(--cobalto-fundo)}
.soltar:focus-within{outline:2px solid var(--cobalto);outline-offset:2px}
.soltar input{position:absolute;opacity:0;width:1px;height:1px}
.soltar-ic{display:grid;place-items:center;width:40px;height:40px;border-radius:50%;background:var(--papel);color:var(--cobalto);border:1px solid var(--fio)}
.soltar-ic .ic{width:20px;height:20px;vertical-align:0}
.arq-ok{display:flex;align-items:center;gap:8px;font-weight:550}.arq-ok .ic{color:var(--ok)}
#imp-erro{color:var(--erro);font-weight:550}
.resumo-imp{position:sticky;top:68px;display:grid;gap:12px}
.resumo-lista{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.resumo-lista li{display:grid;grid-template-columns:18px minmax(0,1fr);gap:10px;align-items:start}
.resumo-lista .ic{margin-top:1px;color:var(--ok)}
.resumo-lista li .ic[href="#i-info"],.resumo-lista li:last-child .ic{color:var(--txt-2)}
.resumo-dif{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.resumo-dif .ic{color:var(--cobalto)}
del,ins{white-space:normal}

/* templates */
.barra-acao{position:sticky;top:60px;z-index:20;display:flex;gap:12px 20px;align-items:center;justify-content:space-between;flex-wrap:wrap;background:var(--papel);
  border:1px solid var(--fio);border-radius:var(--raio-g);padding:10px 14px;margin-bottom:16px;box-shadow:var(--sombra-p)}
.barra-acao .linha{gap:10px}
.n-ver{font-size:12px;background:var(--tela-2);color:var(--txt-2);border-radius:99px;padding:0 7px;min-width:20px;text-align:center;font-weight:600}
.impacto{display:inline-flex;align-items:center;gap:8px;padding:5px 12px;border-radius:99px;background:var(--alerta-fundo);color:var(--alerta);font-size:13px}
.impacto .ic{flex:none;width:16px;height:16px}.impacto b{font-weight:650}
.impacto.erro{background:var(--erro-fundo);color:var(--erro)}
.modelo{display:grid;grid-template-columns:220px minmax(0,1.15fr) minmax(0,1fr);gap:16px;align-items:start}
.col-idx{display:grid;gap:8px;align-content:start}.col-idx .ti{padding:0 4px;font-weight:600}
.sec-item span.sec-nome{flex:1}
.sec-item{min-height:44px}
.add-sec{display:grid;gap:6px}.add-sec .btn{justify-content:flex-start}
.secao-ed{display:grid;gap:14px}
.chip-travado{display:inline-flex;align-items:center;gap:6px;height:28px;padding:0 11px;border-radius:99px;background:var(--tela-2);border:1px solid var(--fio);font-weight:600;color:var(--txt-2)}
.chip-travado .ic{width:14px;height:14px;vertical-align:0}
.barra-fmt{display:flex;align-items:center;gap:2px;flex-wrap:wrap;padding:4px;border:1px solid var(--fio-2);border-bottom:0;border-radius:var(--raio) var(--raio) 0 0;background:var(--tela)}
.barra-fmt .btn{min-width:30px;padding:0 7px}
.barra-fmt .select{width:auto;height:28px;margin-left:auto;font-size:13px;max-width:210px}
.barra-fmt + .textarea{border-radius:0 0 var(--raio) var(--raio);min-height:190px}
.pv-col{display:grid;gap:12px;position:sticky;top:128px}
.pv-cab{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap}
.pv{background:var(--papel);border:1px solid var(--fio);border-radius:var(--raio-g);padding:20px 22px;display:grid;gap:10px;line-height:1.65;font-size:15px;min-height:160px;align-content:start}
.pv h3{font-size:19px;line-height:1.3}
.pv p,.pv ul{margin:0}.pv ul{padding-left:20px}
.valida ul{margin:4px 0 0;padding-left:18px}
.linha-tempo{list-style:none;margin:0;padding:0}
.linha-tempo > li{display:grid;gap:8px;padding:14px 0;border-bottom:1px solid var(--fio)}
.lt-cab{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.lt-cab .mudo{display:inline-flex;align-items:center;gap:6px}
.lt-cab .avatar{width:22px;height:22px;font-size:10px}
.lt-acoes{display:flex;gap:6px;flex-wrap:wrap;align-items:flex-start}
.comp{display:grid;gap:8px;width:100%}.comp[open]{order:5}
.comp > summary{list-style:none;cursor:pointer;width:max-content}.comp > summary::-webkit-details-marker{display:none}
.comp-sec{display:grid;gap:6px}
.gaveta .diff{grid-template-columns:1fr}

@media (max-width:1180px){
  .modelo{grid-template-columns:220px minmax(0,1fr)}
  .pv-col{grid-column:1/-1;position:static}
}
@media (max-width:960px){
  .modelo,.importar,.faixa-ctx,.dividido-desc{grid-template-columns:1fr}
  .resumo-imp,.col-lista{position:static}
  .barra-acao{position:static}
  .lista-desc{max-height:260px}
  .campos-cod{grid-template-columns:1fr}
  .edita-inline .input{font-size:21px}
}
"""

JS = r"""
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const ico = (n) => `<svg class="ic" aria-hidden="true" focusable="false"><use href="#i-${n}"/></svg>`;
  const pl = (n, s, p) => `${n} ${n === 1 ? s : (p || s + "s")}`;
  const sel = $("[data-perfil-sel]");

  /* Duplicar: o diálogo diz de qual matriz sai a cópia */
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-duplicar]");
    if (!b) return;
    const n = b.dataset.duplicar, i = $("#dup-nome"), o = $("#dup-origem");
    if (i) i.value = "Cópia de " + n;
    if (o) o.textContent = n;
  });

  /* Gaveta de versões abre por #versoes (vem do menu da lista) */
  const abreVersoes = () => { const d = $("#versoes"); if (d && location.hash === "#versoes" && !d.open) d.showModal(); };
  abreVersoes();
  window.addEventListener("hashchange", abreVersoes);

  /* ── Criar e importar / reimportar ─────────────────────────────────── */
  const imp = $("[data-importar]");
  if (imp) {
    const nome = $("#imp-nome"), matriz = $("#imp-matriz"), conf = $("#imp-confirma"), ir = $("#imp-ir"), falta = $("#imp-falta");
    const entrada = $("#imp-arquivo"), soltar = $("#imp-soltar"), erro = $("#imp-erro");
    let arquivo = "";
    const reimp = () => location.hash === "#reimportar";
    const opt = () => matriz.selectedOptions[0];
    const atualiza = () => {
      const r = reimp();
      $$("[data-so-modo]").forEach((el) => { el.hidden = el.dataset.soModo !== (r ? "reimp" : "novo"); });
      $$("[data-so-arq]").forEach((el) => { el.hidden = el.dataset.soArq !== (arquivo ? "com" : "sem"); });
      $("#imp-arq-ok").hidden = !arquivo;
      $("#imp-exemplo-p").hidden = !!arquivo;
      $("#imp-arq-nome").textContent = arquivo;
      const o = opt();
      $("#imp-conf-nome").textContent = o.dataset.nome;
      $("#sum-copia").textContent = o.dataset.nome;
      const rev = +o.dataset.rev, val = +o.dataset.val;
      $("#sum-rev").textContent = pl(rev, "revista");
      $("#sum-val").textContent = pl(val, "Validada");
      $("#sum-mecs").textContent = o.dataset.mecs + " etapas × componente";
      $("#sum-desc").textContent = o.dataset.desc + " descritores";
      $("#sum-nome").textContent = nome.value.trim() || "nova";
      const nomeOk = r ? conf.value.trim() === o.dataset.nome : nome.value.trim().length >= 3;
      const ok = nomeOk && !!arquivo;
      const passo1 = $('[data-passo="1"]'), passo2 = $('[data-passo="2"]');
      passo1.dataset.feito = String(r ? true : nome.value.trim().length >= 3);
      passo2.dataset.feito = String(!!arquivo);
      ir.setAttribute("aria-disabled", String(!ok));
      const f = [];
      if (!(r || nome.value.trim().length >= 3)) f.push("dar um nome");
      if (!arquivo) f.push("escolher o arquivo");
      if (r && !nomeOk) f.push("digitar o nome da matriz");
      falta.textContent = ok ? "" : "Falta: " + f.join(", ") + ".";
    };
    const aceita = (f) => {
      erro.hidden = true;
      if (!f) return;
      if (!/\.(pdf|xlsx)$/i.test(f.name)) { erro.textContent = "Formato não aceito: envie um PDF ou uma planilha XLSX."; erro.hidden = false; return; }
      if (f.size > 20 * 1024 * 1024) { erro.textContent = "Arquivo maior que 20 MB: reduza o PDF ou envie só as páginas da matriz."; erro.hidden = false; return; }
      arquivo = f.name + " · " + (f.size / 1048576).toFixed(1).replace(".", ",") + " MB";
      atualiza();
    };
    entrada.addEventListener("change", () => aceita(entrada.files[0]));
    ["dragenter", "dragover"].forEach((t) => soltar.addEventListener(t, (e) => { e.preventDefault(); soltar.classList.add("sobre"); }));
    ["dragleave", "drop"].forEach((t) => soltar.addEventListener(t, (e) => { e.preventDefault(); soltar.classList.remove("sobre"); }));
    soltar.addEventListener("drop", (e) => aceita(e.dataTransfer.files[0]));
    $("#imp-exemplo").addEventListener("click", () => { arquivo = "matriz-comunitaria-2027.xlsx · 4,2 MB"; atualiza(); });
    $("#imp-trocar").addEventListener("click", () => { arquivo = ""; entrada.value = ""; atualiza(); soltar.scrollIntoView({ block: "center" }); });
    [nome, conf, matriz].forEach((el) => el.addEventListener("input", atualiza));
    matriz.addEventListener("change", () => { conf.value = ""; atualiza(); });
    window.addEventListener("hashchange", atualiza);
    if (sel) sel.addEventListener("change", atualiza);
    atualiza();
  }

  /* ── Editor de template: seções, variáveis, pré-visualização, validação ─ */
  const mod = $("[data-modelo]");
  if (mod) {
    const VARS = JSON.parse(mod.dataset.vars), AMOSTRAS = JSON.parse(mod.dataset.amostras);
    const VAR = /\{\{\s*([a-z0-9_]+)\s*\}\}/gi;
    const salvar = $("#salvar-versao"), erroBox = $("#sv-erro"), erroTxt = $("#sv-erro-txt"), pv = $("#pv"), valida = $("#pv-valida"), parc = $("#pv-parceiro");
    const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
    const painelAtivo = () => $$("[data-painel]", mod).find((p) => !p.hidden) || $("[data-painel]", mod);
    const erros = (txt) => {
      const out = [], vistos = new Set();
      for (const m of txt.matchAll(VAR)) { if (!(m[1] in VARS) && !vistos.has(m[1])) { vistos.add(m[1]); out.push(m[1]); } }
      const a = (txt.match(/\{\{/g) || []).length, f = (txt.match(/\}\}/g) || []).length;
      if (a !== f) out.push(null);
      return out;
    };
    const textos = (p) => ({ t: $('[data-campo="titulo"]', p).value, x: $('[data-campo="texto"]', p).value });
    const msgErro = (k) => k === null
      ? "Há <b>{{</b> sem o <b>}}</b> correspondente. Feche a variável com <b>}}</b>."
      : `A variável <span class="var var-vazia">{{${esc(k)}}}</span> não existe. Escolha outra em “Variável…” ou peça a criação ao Admin do ano.`;
    const fmt = (txt, am) => {
      let h = esc(txt).replace(VAR, (_, k) => {
        if (!(k in VARS)) return `<span class="var var-vazia">{{${k}}}</span>`;
        const v = am[k];
        return v ? `<span class="var">${esc(v)}</span>` : `<span class="var var-vazia">{{${k}}} vazia</span>`;
      });
      h = h.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/(^|[^*])\*(?!\*)(.+?)\*(?!\*)/g, "$1<em>$2</em>");
      return h.split(/\n{2,}/).filter((b) => b.trim()).map((b) => {
        const ls = b.split("\n");
        if (ls.every((l) => /^-\s+/.test(l))) return "<ul>" + ls.map((l) => "<li>" + l.replace(/^-\s+/, "") + "</li>").join("") + "</ul>";
        return "<p>" + ls.join("<br>") + "</p>";
      }).join("") || '<p class="mudo">(sem texto)</p>';
    };
    const marca = () => {
      let total = 0, primeiro = "";
      $$("[data-painel]", mod).forEach((p) => {
        const { t, x } = textos(p), e = [...erros(t), ...erros(x)];
        total += e.length;
        const id = p.dataset.painel, alvo = $(`[data-idx="${id}"]`, mod);
        if (e.length && !primeiro) primeiro = $(".chip-travado", p).textContent.trim();
        if (alvo) alvo.innerHTML = e.length
          ? `<span class="tag tag-erro">${pl(e.length, "erro")}</span>`
          : `<span class="st st-ok" title="Sem erros" role="img" aria-label="Sem erros">${ico("ok")}</span>`;
      });
      salvar.setAttribute("aria-disabled", String(total > 0));
      erroBox.hidden = total === 0;
      erroTxt.textContent = `${pl(total, "erro")}${primeiro ? " em " + primeiro : ""}: corrija para salvar`;
    };
    const desenha = () => {
      const p = painelAtivo(), { t, x } = textos(p), am = AMOSTRAS[parc.value];
      pv.innerHTML = `<h3>${fmt(t, am).replace(/^<p>|<\/p>$/g, "")}</h3>${fmt(x, am)}`;
      const es = [...erros(t), ...erros(x)];
      const vazias = [...new Set([...(t + " " + x).matchAll(VAR)].map((m) => m[1]).filter((k) => k in VARS && !am[k]))];
      let h = "";
      if (es.length) h += `<div class="aviso aviso-erro" role="status">${ico("alerta")}<div class="aviso-txt"><b>${pl(es.length, "erro")} nesta seção.</b><ul>${es.map((k) => "<li>" + msgErro(k) + "</li>").join("")}</ul></div></div>`;
      else h += `<div class="aviso aviso-ok" role="status">${ico("confirmado")}<div class="aviso-txt">Sem erros: todas as variáveis desta seção existem.</div></div>`;
      if (vazias.length) h += `<div class="aviso aviso-alerta" style="margin-top:8px" role="status">${ico("alerta")}<div class="aviso-txt">${vazias.map((k) => `<span class="var var-vazia">{{${k}}}</span>`).join(" ")} ${vazias.length === 1 ? "está vazia" : "estão vazias"} em ${esc(am.nome_parceiro)}: a frase sai incompleta na revista. <a href="parceiro-boa-terra.html">Preencher em Parceiros</a>.</div></div>`;
      valida.innerHTML = h;
    };
    let tempo;
    const agenda = () => { clearTimeout(tempo); tempo = setTimeout(() => { marca(); desenha(); }, 120); };
    mod.addEventListener("input", agenda);
    parc.addEventListener("change", desenha);
    mod.addEventListener("click", (e) => { if (e.target.closest("[data-aba]")) setTimeout(desenha, 0); });
    window.addEventListener("hashchange", () => setTimeout(desenha, 0));

    let alvo = null;
    mod.addEventListener("focusin", (e) => { if (e.target.matches("[data-campo]")) alvo = e.target; });
    const poe = (ta, ini, fim, novo) => {
      ta.setRangeText(novo, ini, fim, "end");
      ta.focus();
      ta.dispatchEvent(new Event("input", { bubbles: true }));
      ta.dispatchEvent(new Event("change", { bubbles: true }));
    };
    mod.addEventListener("click", (e) => {
      const b = e.target.closest("[data-fmt]");
      if (!b || b.disabled) return;
      const ta = $('[data-campo="texto"]', painelAtivo()), a = ta.selectionStart, z = ta.selectionEnd, s = ta.value.slice(a, z);
      if (b.dataset.fmt === "n") poe(ta, a, z, `**${s || "negrito"}**`);
      if (b.dataset.fmt === "i") poe(ta, a, z, `*${s || "itálico"}*`);
      if (b.dataset.fmt === "l") poe(ta, a, z, (s || "item").split("\n").map((l) => "- " + l.replace(/^-\s+/, "")).join("\n"));
    });
    mod.addEventListener("change", (e) => {
      const s = e.target.closest("[data-var-ins]");
      if (!s || !s.value) return;
      const p = painelAtivo(), ta = alvo && p.contains(alvo) ? alvo : $('[data-campo="texto"]', p);
      poe(ta, ta.selectionStart, ta.selectionEnd, `{{${s.value}}}`);
      s.value = "";
    });
    if (sel) sel.addEventListener("change", () => { setTimeout(marca, 0); });
    marca();
    desenha();
  }
})();
"""


def paginas():
    out = [_matrizes()]
    out += [_matriz(m) for m in D.MATRIZES]
    out += [_etapa(), _importar(), _diferencas(), _templates()]
    out += [_template(t) for t in D.TEMPLATES if t["id"] in ("lp-f1", "lp-f2")]
    return out
