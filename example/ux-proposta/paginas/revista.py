"""A ficha da revista: um stepper de 6 passos, um painel por passo e um rodapé que diz o próximo clique.

Gera revista-<id>.html para as 32 revistas. O estado (passos, pendências, edição, Validado) vem de D.REVISTAS
passando por revistas.estado(), que corrige no local o que dados.py deixa incoerente.
"""
import hashlib
import re
from types import SimpleNamespace

import dados as D
from paginas import shell as S
from paginas.revistas import estado, pl, primeiro, data_curta

_NOME = {k: n for k, n, _ in D.PASSOS}
_ORDEM = [k for k, _, _ in D.PASSOS]
_FALTA_PALAVRA = {
    "base": ("Sem matriz", "Cortes", "variáveis"),
    "templates": ("template",),
    "infograficos": ("Alfa",),
    "capa": ("capa",),
    "textos": ("seções",),
}
_NOME_ETAPA = {"2EF": "2º ano do EF", "5EF": "5º ano do EF", "9EF": "9º ano do EF", "3EM": "3ª série do EM"}


def _ctx(i, r):
    passos, pend = estado(r)
    mat = next((m for m in D.MATRIZES if m["id"] == r["matriz"]), None)
    c = SimpleNamespace(
        i=i, r=r, rid=r["id"], pid=r["parceiro"], comp=r["comp"], fase=r["fase"], ed=r["editando"], val=r["validada"],
        p=D.PARCEIRO_POR_ID[r["parceiro"]], mat=mat, passos=passos, pend=pend, nome=S.nome_revista(r),
    )
    c.edita = "disabled" if c.ed else "data-edita"
    c.impacto = ' data-impacto="dlg-impacto"' if c.fase >= 4 else ""
    c.proximo = next((k for k in _ORDEM if passos[k] != "ok"), None)
    c.prontos = sum(1 for k in _ORDEM if passos[k] == "ok")
    c.href_parceiro = S.href_parceiro(c.pid)
    return c


def _ok(c, k):
    return c.passos[k] == "ok"


def _msg(c, k):
    """Texto longo de por que o passo está pendente."""
    if _ok(c, k):
        return "Pronto"
    if k == "conferir":
        return "Pronta para validar" if c.fase == 3 else "Depois dos passos"
    if c.fase == 1 and k != "base":
        return "Depois da Base"
    for p in c.pend:
        if any(w in p for w in _FALTA_PALAVRA[k]):
            return p
    return "Pendente"


def _falta(c, k):
    """Subtexto curto do stepper."""
    if _ok(c, k):
        return "Validada" if k == "conferir" else "Pronto"
    m = _msg(c, k)
    if k == "conferir" or m in ("Depois da Base", "Pendente"):
        return m
    n = re.match(r"(\d+) (?!de )", m)
    return f"Faltam {n.group(1)}" if n and int(n.group(1)) > 1 else "Falta 1"


def _hash(c):
    return hashlib.md5(c.rid.encode()).hexdigest()[:7]


# ── Topo: validar, preview, mais ──────────────────────────────────────────
def _validar(c):
    if c.fase >= 4:
        quem, quando = c.val
        return S.tag(f"Validada por {quem} em {data_curta(quando)}", "ok", "confirmado")
    if c.ed:
        return S.btn("Validar revista", tom="prim", icone="confirmado", attrs=f'disabled title="{S.esc(c.ed)} está editando este projeto"')
    if c.fase < 3 or c.pend:
        n = len(c.pend)
        aux = f'<span class="rv-aux">Resolva {pl(n, "pendência", "pendências")} para validar</span>'
        return aux + S.btn(
            "Validar revista", tom="prim", icone="confirmado",
            attrs=f'disabled title="Para validar, resolva: {S.esc("; ".join(c.pend))}"',
        )
    return S.btn("Validar revista", tom="prim", icone="confirmado", attrs='data-abrir="dlg-validar" data-edita')


def _menu_mais(c):
    if c.fase >= 4:
        zip_ = S.item_menu("Baixar zip", icone="baixar", attrs='data-toast="Zip gerado (demo): ' + c.rid + '.zip"')
    else:
        zip_ = S.item_menu("<span>Baixar zip<small>Disponível depois de validar</small></span>", icone="baixar", attrs='disabled aria-disabled="true"')
    return S.menu(
        "Mais",
        [
            zip_,
            S.item_menu("Baixar planilhas", icone="grade", attrs='data-toast="Planilhas geradas (demo)"'),
            "<hr>",
            S.item_menu("Tela do impresso", "entrega-impresso.html" + (f"#{c.rid}" if D.POR_ID[c.rid]["fase"] >= 3 else ""), "pacote"),
            S.item_menu("Editar o nome do projeto", c.href_parceiro, "lapis"),
        ],
        icone="pontos",
    )


def _cab(c):
    mat = (
        f'matriz <a href="matriz-{c.mat["id"]}.html">{S.esc(c.mat["nome"])}</a>'
        if c.mat
        else S.tag("sem matriz", "alerta", "alerta")
    )
    sub = (
        f'<span class="rv-sub"><a href="{c.href_parceiro}">{S.esc(c.p["nome"])}</a><span aria-hidden="true">·</span>{mat}'
        f'<span aria-hidden="true">·</span>{S.regua(c.fase)}</span>'
    )
    acoes = _validar(c) + S.btn("Preview", tom="sec", icone="olho", attrs='data-ir-aba="conferir" title="Ver o preview no passo Conferir"', href="#conferir") + _menu_mais(c)
    return S.cab(f"{S.esc(c.p['nome'])} · {D.COMP_NOME[c.comp]}", sub, acoes)


def _avisos(c):
    out = []
    if c.ed:
        out.append(S.aviso(f"Somente leitura: {S.esc(c.ed)} está editando este projeto. Tente de novo em instantes.", "leitura"))
    out.append(
        '<div data-p="imp">'
        + S.aviso(
            f'Você vê esta revista, mas não altera nada. Para mudar algo, peça à equipe Pedagógica ou de Mídias Digitais. '
            f'Sua parte é marcar o impresso na <a href="entrega-impresso.html{'#' + c.rid if D.POR_ID[c.rid]['fase'] >= 3 else ''}">tela do impresso</a>.',
            "leitura",
        )
        + "</div>"
    )
    if not c.mat:
        out.append(
            S.aviso(
                f'Sem matriz: {S.esc(c.p["nome"])} não tem matriz atribuída, então não há descritores nem cortes para montar a escala. '
                f'Atribua uma em <a href="{c.href_parceiro}#matriz">Parceiro › Matriz</a>.',
                "alerta",
            )
        )
    return f'<div class="rv-avisos">{"".join(out)}</div>'


# ── Stepper ───────────────────────────────────────────────────────────────
def _stepper(c):
    ativo = c.proximo or "conferir"
    bs = ""
    for n, k in enumerate(_ORDEM, 1):
        ok = _ok(c, k)
        bs += (
            f'<button type="button" class="passo" role="tab" data-aba="{k}" data-estado="{"ok" if ok else "pend"}" '
            f'aria-selected="{"true" if k == ativo else "false"}">'
            f'<span class="passo-n">{S.ic("ok") if ok else n}</span>'
            f'<span class="passo-txt"><b>{_NOME[k]}</b><small>{S.esc(_falta(c, k))}</small></span></button>'
        )
    return f'<div class="passos" role="tablist" aria-label="Passos da revista" data-abas>{bs}</div>'


# ── Passo Base ────────────────────────────────────────────────────────────
_PADRAO_CORTES = {"2EF": [350, 400, 450], "5EF": [150, 175, 200], "9EF": [200, 225, 250], "3EM": [225, 250, 275]}
_MAX = dict(D.ETAPAS)


def _cortes(c, etapa):
    """Lista de 3 cortes ou None. Só falta quando a pendência da revista diz que falta."""
    if any(p.startswith(f"Cortes de {etapa}") for p in c.pend):
        return None
    s = D.cortes(c.pid, etapa, c.comp) or D.cortes(c.pid, etapa, "MT" if c.comp == "LP" else "LP")
    return [int(x) for x in s.split(", ")] if s else _PADRAO_CORTES[etapa]


def _variaveis_vazias(c):
    for p in c.pend:
        m = re.match(r"(\d+) de 24 variáveis vazias", p)
        if m:
            return [v[1] for v in D.VARIAVEIS[: int(m.group(1))]], int(m.group(1))
    return [], 0


def _p_base(c):
    nota = S.aviso(
        f'Somente leitura aqui. A base se edita no parceiro: <a href="{c.href_parceiro}">abrir {S.esc(c.p["nome"])}</a>.',
        "info",
    )
    if c.mat:
        origem = f"Derivada de {S.esc(c.mat['origem'])}. " if c.mat["origem"] else ""
        matriz = (
            f'<h3>Matriz</h3><p><a href="matriz-{c.mat["id"]}.html"><b>{S.esc(c.mat["nome"])}</b></a></p>'
            f'<p class="mudo">{origem}{c.mat["mecs"]} MECs · {c.mat["descritores"]} descritores · atualizada em {c.mat["atualizada"]}</p>'
        )
    else:
        matriz = (
            f'<h3>Matriz</h3><p>{S.tag("Sem matriz", "alerta", "alerta")}</p>'
            f'<p class="mudo">Sem matriz, a revista não tem descritores. <a href="{c.href_parceiro}#matriz">Atribuir no parceiro</a>.</p>'
        )
    vazias, n_vazias = _variaveis_vazias(c)
    cheias = 24 - n_vazias
    var = (
        f'<h3>Dados do parceiro</h3><p><b>{cheias} de 24</b> variáveis preenchidas</p>'
        + (
            f'<p class="mudo">Vazias: {S.esc(", ".join(vazias))}.</p>'
            if vazias
            else '<p class="mudo">Nenhuma variável vazia.</p>'
        )
        + f'<p><a href="{c.href_parceiro}#variaveis">Ver as variáveis do parceiro</a></p>'
    )
    linhas, faltam = [], []
    for etapa, _ in D.ETAPAS:
        cs = _cortes(c, etapa)
        nome = f'<b>{etapa}</b> <span class="mudo">{_NOME_ETAPA[etapa]}</span>'
        if cs is None:
            faltam.append(etapa)
            linhas.append([nome, S.tag("Faltando", "alerta", "alerta"), f'<a href="{c.href_parceiro}#cortes">Preencher no parceiro</a>'])
        else:
            linhas.append([nome, S.escala(cs, _MAX[etapa], 12), ", ".join(map(str, cs))])
    aviso_cortes = (
        S.aviso(f'Cortes de {S.esc(", ".join(faltam))} faltando. <a href="{c.href_parceiro}#cortes">Preencha no parceiro</a>.', "alerta")
        if faltam
        else ""
    )
    leg = "".join(
        f'<span class="rv-leg-i"><i style="background:{cor}"></i>Padrão 0{n} · {S.esc(nome)}</span>' for n, nome, cor in D.PADROES
    )
    cortes = (
        f'<div class="rv-cab"><h3>Cortes desta revista ({D.COMP_NOME[c.comp]})</h3></div>{aviso_cortes}'
        + S.tabela(["Etapa", "Escala", "Cortes"], linhas, cls="rv-cortes")
        + f'<div class="rv-leg">{leg}</div>'
    )
    return (
        f'<section data-painel="base" aria-label="Base">{nota}'
        f'<div class="rv-dois"><div class="card card-p rv-bl">{matriz}</div><div class="card card-p rv-bl">{var}</div></div>'
        f'<div class="card card-p rv-bl rv-largo">{cortes}</div></section>'
    )


# ── Passo Templates ───────────────────────────────────────────────────────
def _p_templates(c):
    f1 = [t for t in D.TEMPLATES if t["comp"] == c.comp and t["fasc"] == "F1"]
    f2 = [t for t in D.TEMPLATES if t["comp"] == c.comp and t["fasc"] == "F2"]
    f2_pend = c.fase == 1 or any("template do F2" in p for p in c.pend)
    atual1 = "" if c.fase == 1 else (f"{c.comp.lower()}-f1-municipio" if c.p["tipo"] == "Município" else f"{c.comp.lower()}-f1")
    atual2 = "" if f2_pend else f2[0]["id"]
    attrs = f"{c.edita} data-autosave{c.impacto}"

    def bloco(rot, nome, tpls, atual, link):
        ops = [("", "Escolha um template")] + [(t["id"], t["nome"]) for t in tpls]
        t = next((t for t in tpls if t["id"] == atual), None)
        if t:
            ajuda = f'Versão {t["versao"]} · usado em {t["usado"]} revistas · atualizado em {t["atualizado"]} · <a href="{link}">ver template</a>'
        else:
            ajuda = f'{S.tag("Falta escolher", "alerta", "alerta")} Cada fascículo precisa de um template.'
        return f'<div class="rv-campo">{S.selecao(rot, nome, ops, atual, attrs)}<span class="ajuda">{ajuda}</span></div>'

    return (
        '<section data-painel="templates" aria-label="Templates">'
        '<div class="card card-p rv-bl"><h3>Template de cada fascículo</h3><div class="campos-2">'
        + bloco("Fascículo 1 · escalas", "template-f1", f1, atual1, "template-lp-f1.html")
        + bloco("Fascículo 2 · infográfico", "template-f2", f2, atual2, "template-lp-f2.html")
        + "</div></div>"
        + S.aviso(
            'Cópias de seção: quando você edita o texto de uma seção em <a href="#textos" data-ir-aba="textos">Textos</a>, a revista guarda uma cópia dela. '
            "Trocar o template não apaga as cópias: elas aparecem como &ldquo;desatualizadas&rdquo; e você escolhe manter ou descartar.",
            "info",
        )
        + "</section>"
    )


# ── Passo Infográficos ────────────────────────────────────────────────────
_TAREFAS = {
    "alfa": [
        ("A01", "Ler palavras formadas por sílabas simples."),
        ("A02", "Identificar o assunto de um bilhete."),
        ("A03", "Localizar uma informação em uma frase curta."),
        ("A04", "Completar frases com a palavra adequada."),
    ],
    "outras": [(d, t) for d, t, *_ in D.DESCRITORES_5EF_LP[:4]],
}
_HAB = {
    "alfa": "Ler palavras e frases curtas, identificando o assunto de um texto.",
    "outras": "Localizar informações explícitas em textos de diferentes gêneros.",
}


def _passo_inf(c, chave, n, titulo, corpo, ativo=True):
    ck = f'<input type="checkbox" class="rv-chk" {"checked" if ativo else ""} aria-label="Ligar o passo {titulo}" {c.edita} data-autosave>'
    return (
        f'<details class="rv-det"{" open" if n == 1 else ""}><summary>{ck}<b>Passo {n} · {titulo}</b>'
        f'<span class="mudo rv-det-s">{"Ligado" if ativo else "Desligado"}</span>{S.ic("baixo", "rv-det-seta")}</summary><div class="rv-det-c">{corpo}</div></details>'
    )


def _p_inf_aba(c, chave, ident, vazio):
    attrs = f"{c.edita} data-autosave{c.impacto}"
    aviso = ""
    if vazio and chave == "alfa" and c.fase > 1:
        aviso = S.aviso("Infográfico Alfa sem habilidade. Escreva a habilidade abaixo para liberar a validação.", "alerta")
    hab = S.campo(
        "Habilidade em foco", f"hab-{chave}", "" if vazio else _HAB[chave],
        ajuda="Aparece na abertura do infográfico.", attrs=f'{attrs} placeholder="Ex.: {_HAB[chave][:48]}…"',
    )
    prog = (
        '<p>Mostra como a habilidade evolui entre as etapas avaliadas.</p><p class="linha">'
        + "".join(S.tag(e) for e, _ in D.ETAPAS)
        + "</p>"
    )
    linhas = [
        [f"<b>Tarefa {k}</b>", cod, S.esc(t), S.st("pend" if vazio else "ok")]
        for k, (cod, t) in enumerate(_TAREFAS[chave], 1)
    ]
    tarefas = S.tabela(["Tarefa", "Descritor", "Enunciado (resumo)", ""], linhas, cls="rv-tarefas")
    hab_txt = S.campo(
        "Texto do passo", f"hab-txt-{chave}", "" if vazio else f"Cada descritor ancora uma habilidade: {_HAB[chave].lower()}",
        textarea=True, attrs=f'{attrs} rows="3"',
    )
    return (
        f'<section data-painel="{ident}" aria-label="Infográfico {"Alfa" if chave == "alfa" else "Outras Etapas"}">{aviso}'
        f'<div class="card card-p rv-bl">{hab}</div>'
        f'<div class="rv-dets">{_passo_inf(c, chave, 1, "Habilidades", hab_txt)}{_passo_inf(c, chave, 2, "Progressão", prog)}'
        f'{_passo_inf(c, chave, 3, "Tarefas", tarefas)}</div></section>'
    )


def _p_infograficos(c):
    vazio_alfa = c.fase == 1 or any("Alfa" in p for p in c.pend)
    abas = S.abas_js([("inf-alfa", "Alfa", None), ("inf-outras", "Outras Etapas", None)])
    return (
        '<section data-painel="infograficos" aria-label="Infográficos">'
        f'<p class="mudo rv-intro">São dois infográficos por revista: um para o Alfa e outro para as Outras Etapas. Cada um tem uma habilidade e três passos que podem ser ligados ou desligados.</p>'
        + abas
        + _p_inf_aba(c, "alfa", "inf-alfa", vazio_alfa)
        + _p_inf_aba(c, "outras", "inf-outras", c.fase == 1)
        + "</section>"
    )


# ── Passo Capa ────────────────────────────────────────────────────────────
def _p_capa(c):
    if _ok(c, "capa"):
        corpo = (
            f'<div class="rv-capa"><div class="rv-capa-img" role="img" aria-label="Miniatura da capa">{S.ic("imagem")}<span>Capa</span></div>'
            f'<div class="rv-capa-info"><h3>capa-{S.esc(c.rid)}.jpg</h3>'
            '<p class="mudo">1240 × 1754 px · 312 KB · enviada por Bruno Lima em 10/11</p>'
            f'<p class="mudo">Para trocar, solte outra imagem sobre a miniatura ou use o botão.</p>'
            + S.btn("Substituir capa", tom="sec", icone="subir", attrs=f'{c.edita} data-salva data-toast="Capa substituída (demo)"')
            + "</div></div>"
        )
    else:
        corpo = (
            f'<div class="rv-soltar">{S.ic("imagem", "rv-soltar-ic")}<h3>Solte a capa aqui</h3>'
            '<p class="mudo">JPG ou PNG, em pé, na proporção de uma página A4. Ela aparece no preview e no zip.</p>'
            + S.btn("Enviar capa", tom="sec", icone="subir", attrs=f'{c.edita} data-salva data-toast="Capa enviada (demo)"')
            + "</div>"
        )
    return f'<section data-painel="capa" aria-label="Capa"><div class="card card-p rv-bl">{corpo}</div></section>'


# ── Passo Textos ──────────────────────────────────────────────────────────
_ROT = {"template": ("do template", ""), "copia": ("cópia", "cobalto"), "desatualizada": ("desatualizada", "alerta"), "vazio": ("sem texto", "alerta")}
_VAR_CHAVE = {"adj_fem_sing": "pat_f", "adj_masc_sing": "pat_m", "issn": "colecao", "programa": "programa", "secretaria": "secretaria", "regional": "regional"}
_ESCOLHA_SEM_F2 = ("abertura", "passo1", "passo2", "passo3", "dlg-descritor")


def _status_secoes(c):
    ids = [s[0] for s in D.SECOES_F1 + D.SECOES_F2]
    if c.fase == 1:
        return {i: "vazio" for i in ids}
    st = {i: "template" for i in ids}
    if any("template do F2" in p for p in c.pend):
        for i in _ESCOLHA_SEM_F2:
            st[i] = "vazio"
    if any("seções sem texto" in p for p in c.pend):
        for i in ("passo2", "passo3", "dlg-descritor"):
            st[i] = "vazio"
    if c.i % 3 == 0 and st["introducao"] == "template":
        st["introducao"] = "copia"
    if c.i % 4 == 1 and st["fechamento"] == "template":
        st["fechamento"] = "desatualizada"
    return st


def _chip(c, nome, vazias):
    vazia = any(v[3] == "{{" + nome + "}}" and v[1] in vazias for v in D.VARIAVEIS)
    cls = "var var-vazia" if vazia else "var"
    t = ' title="Vazia no parceiro"' if vazia else ""
    return f'<span class="{cls}"{t}>' + "{{" + nome + "}}" + "</span>"


def _secao_detalhe(c, sec, status, vazias, oculto):
    ident, nome, titulo, texto = sec
    rot, tom = _ROT[status]
    attrs = f"{c.edita} data-autosave{c.impacto}"
    vars_ = list(dict.fromkeys(re.findall(r"\{\{(\w+)\}\}", titulo + " " + texto)))
    chips = " ".join(_chip(c, v, vazias) for v in vars_) or '<span class="mudo">nenhuma</span>'
    vazio = status == "vazio"
    area = S.campo(
        "Texto da seção", f"txt-{ident}", "" if vazio else texto, textarea=True,
        attrs=f'{attrs} rows="5"' + (' placeholder="Escreva o texto desta seção ou use o do template."' if vazio else ""),
    )
    extra = ""
    if status == "desatualizada":
        extra = (
            '<div class="rv-desat"><p><b>O template mudou depois que você editou esta seção.</b> Compare e escolha.</p>'
            '<div class="diff"><div><h4>Seu texto (cópia)</h4><p>A {{secretaria}} e as equipes pedagógicas podem usar estas páginas para '
            "<del>planejar a recomposição</del> das aprendizagens.</p></div>"
            '<div><h4>Template novo (versão 2)</h4><p>A {{secretaria}} e as equipes pedagógicas podem usar estas páginas para '
            "<ins>orientar o planejamento e a recomposição</ins> das aprendizagens.</p></div></div>"
            '<div class="linha">'
            + S.btn("Manter meu texto", tom="sec", attrs=f'{c.edita} data-toast="Mantido. A cópia continua sendo sua."')
            + S.btn("Descartar cópia", tom="perigo", attrs=f'{c.edita} data-toast="Cópia descartada. A seção voltou ao template."')
            + "</div></div>"
        )
    elif status == "copia":
        extra = (
            '<p class="mudo">Esta seção é uma cópia desta revista, editada em 09/11. Mudanças no template não chegam aqui.</p>'
            + S.btn("Voltar ao texto do template", tom="sec", attrs=f'{c.edita} data-toast="A seção voltou ao template."')
        )
    elif vazio:
        extra = S.btn("Usar o texto do template", tom="sec", attrs=f'{c.edita} data-salva data-toast="Texto do template aplicado."')
    else:
        extra = '<p class="mudo">Usa o texto do template. Ao editar, a revista passa a ter uma cópia só dela.</p>'
    return (
        f'<div class="rv-sec" data-sec-p="{ident}"{" hidden" if oculto else ""}>'
        f'<div class="rv-sec-cab"><h3>{S.esc(nome)}</h3>{S.tag(rot, tom)}</div>'
        + S.campo("Título (vem do template)", f"tit-{ident}", titulo, attrs="readonly")
        + area
        + f'<p class="rv-vars"><span class="mudo">Variáveis nesta seção:</span> {chips}</p>'
        + extra
        + "</div>"
    )


def _p_textos(c):
    st = _status_secoes(c)
    vazias, _ = _variaveis_vazias(c)
    ordem = [s[0] for s in D.SECOES_F1 + D.SECOES_F2]
    inicial = next((i for i in ordem if st[i] in ("vazio", "desatualizada")), ordem[0])

    def grupo(rot, secs):
        it = ""
        for ident, nome, *_ in secs:
            r, tom = _ROT[st[ident]]
            sel = "true" if ident == inicial else "false"
            it += f'<button type="button" data-sec="{ident}" aria-current="{sel}"><span class="rv-sec-n">{S.esc(nome)}</span>{S.tag(r, tom)}</button>'
        return f'<p class="rv-grupo">{rot}</p>{it}'

    lista = f'<div class="lista-sel" data-secoes>{grupo("Fascículo 1 · escalas", D.SECOES_F1)}{grupo("Fascículo 2 · infográfico", D.SECOES_F2)}</div>'
    det = "".join(_secao_detalhe(c, s, st[s[0]], vazias, s[0] != inicial) for s in D.SECOES_F1 + D.SECOES_F2)
    return f'<section data-painel="textos" aria-label="Textos"><div class="dividido">{lista}<div class="card card-p rv-det-sec">{det}</div></div></section>'


def _dlg_impacto(c):
    corpo = (
        f'<p>Gravar esta alteração tira o Validado de <b>1 revista</b>. Ela volta para a fase Conferir e precisa ser validada de novo.</p>'
        f'<ul class="checklist"><li>{S.st("pend", "Perde o Validado")}<span class="txt"><b>{S.esc(c.nome)}</b></span>'
        f"<small>Validada por {S.esc(c.val[0])}"
        + (" · o impresso fica desatualizado" if c.fase == 5 else "")
        + "</small></li></ul>"
    )
    return S.dialogo(
        "dlg-impacto",
        "Esta alteração tira o Validado",
        corpo,
        S.btn("Cancelar", tom="fan", attrs="data-fechar") + S.btn("Gravar e tirar o Validado", tom="prim", attrs="data-impacto-ok"),
    )


def _dlg_validar(c):
    corpo = (
        f'<p>Você vai validar <b>{S.esc(c.nome)}</b> exatamente como está no preview (versão {_hash(c)}).</p>'
        '<p class="mudo">A revista entra na fila do impresso. Se algo mudar depois, o Validado cai e o sistema avisa antes de gravar.</p>'
    )
    return S.dialogo(
        "dlg-validar",
        "Validar revista",
        corpo,
        S.btn("Cancelar", tom="fan", attrs="data-fechar")
        + S.btn("Validar revista", tom="prim", icone="confirmado", attrs='data-edita data-fechar data-salva data-toast="Revista validada. Ela entrou na fila do impresso."'),
    )


# ── Passo Conferir ────────────────────────────────────────────────────────
def _p_conferir(c):
    li = ""
    for k in _ORDEM[:-1]:
        ok = _ok(c, k)
        li += (
            f'<li>{S.st("ok" if ok else "pend")}<a class="txt" href="#{k}" data-ir-aba="{k}">{_NOME[k]}</a>'
            f'<small>{S.esc(_msg(c, k))}</small></li>'
        )
    prev = (
        f'<div class="rv-prev" role="img" aria-label="Moldura do preview da revista">{S.ic("livro", "rv-prev-ic")}<b>Preview</b>'
        f'<span>Versão {_hash(c)}</span></div>'
        + S.btn("Abrir preview", tom="sec", icone="externo", attrs='data-toast="Preview aberto em nova aba (demo)"', cls="rv-prev-btn")
    )
    if c.pend:
        titulo_check = f"{pl(len(c.pend), 'pendência', 'pendências')} antes de validar"
    else:
        titulo_check = "Tudo pronto para validar" if c.fase == 3 else "Nenhuma pendência"
    direita = (
        f'<div class="rv-bl"><h3>{titulo_check}</h3><ul class="checklist">{li}</ul></div>'
        + (
            f'<p class="mudo rv-conf-acao">Você valida quando {S.esc(c.ed)} terminar de editar.</p>'
            if c.ed
            else f'<div class="rv-conf-acao">{_validar(c)}</div>'
        )
    )
    if c.fase in (3, 4):
        mudou = (
            f'<div class="rv-bl"><h3>O que mudou para o impresso</h3>'
            '<p class="mudo">2 mudanças desde a última versão enviada ao impresso: Introdução e Capa.</p>'
            '<div class="diff"><div><h4>Impresso atual</h4><p>Esta revista apresenta os resultados do <del>Programa Avalia</del> para a rede '
            f'<del>estadual</del>. Cada escala mostra o que os estudantes <del>sabem</del> fazer em cada padrão. <span class="mudo">Capa: imagem anterior.</span></p></div>'
            f'<div><h4>Nesta revista</h4><p>Esta revista apresenta os resultados do <ins>Avalia {S.esc(c.p["nome"])}</ins> para a rede '
            '<ins>pública</ins>. Cada escala mostra o que os estudantes <ins>são capazes de</ins> fazer em cada padrão. <span class="mudo">Capa: imagem nova.</span></p></div></div></div>'
        )
    elif c.fase == 5:
        mudou = '<div class="rv-bl"><h3>O que mudou para o impresso</h3>' + S.aviso("Impresso em dia: nada mudou desde que o impresso foi atualizado.", "ok") + "</div>"
    else:
        mudou = '<div class="rv-bl"><h3>O que mudou para o impresso</h3><p class="mudo">Aparece depois que todos os passos estiverem prontos.</p></div>'
    return (
        '<section data-painel="conferir" aria-label="Conferir">'
        f'<div class="card card-p"><div class="rv-conf"><div class="rv-prev-col">{prev}</div><div class="rv-conf-dir">{direita}</div></div></div>'
        f'<div class="card card-p rv-mudou">{mudou}</div></section>'
    )


# ── Rodapé fixo ───────────────────────────────────────────────────────────
def _rodape(c):
    segs = "".join(f'<i class="{"on" if _ok(c, k) else ""}"></i>' for k in _ORDEM)
    if c.proximo:
        prox = c.proximo
        dest = f'<a class="btn" href="#{prox}" data-ir-aba="{prox}">Próximo: {_NOME[prox]}{S.ic("seta")}</a>'
        if c.proximo == "conferir" and c.fase == 3:
            dest = f'<a class="btn" href="#conferir" data-ir-aba="conferir">Próximo: conferir e validar{S.ic("seta")}</a>'
        txt = f"<b>{c.prontos} de 6 passos prontos</b>"
    else:
        txt = "<b>6 de 6 passos prontos</b>"
        dest = f'<a class="btn" href="entrega-impresso.html#{c.rid}">Ver na tela do impresso{S.ic("seta")}</a>'
    return f'<div class="rv-rodape" role="region" aria-label="Andamento da revista"><span class="rv-prog" aria-hidden="true">{segs}</span>{txt}<span class="rv-sep">·</span>{dest}</div>'


def _pagina(i, r):
    c = _ctx(i, r)
    paineis = (
        _p_base(c) + _p_templates(c) + _p_infograficos(c) + _p_capa(c) + _p_textos(c) + _p_conferir(c)
    )
    dialogos = _dlg_validar(c) if (c.fase == 3 and not c.pend) else ""
    if c.fase >= 4:
        dialogos += _dlg_impacto(c)
    corpo = _cab(c) + _avisos(c) + _stepper(c) + f'<div class="rv-paineis">{paineis}</div>' + _rodape(c) + dialogos
    return S.Pagina(
        S.href_revista(c.rid), c.nome, "revistas", corpo,
        trilha=[("Revistas", "revistas.html"), (f'{c.p["nome"]} · {c.comp}', None)], status=True,
    )


def paginas():
    return [_pagina(i, r) for i, r in enumerate(D.REVISTAS)]


CSS = """
/* ── Ficha da revista ────────────────────────────────────────────────── */
.rv-sub{display:inline-flex;gap:4px 10px;flex-wrap:wrap;align-items:center}
.rv-aux{color:var(--txt-2);font-size:13px}
.rv-avisos{display:grid;gap:10px;margin-bottom:16px}
.rv-avisos:empty{display:none}
.rv-avisos > [data-p][hidden]{display:none}
.rv-paineis{display:grid;gap:16px;grid-template-columns:minmax(0,1fr)}
.rv-paineis > section{display:grid;gap:16px;align-content:start;grid-template-columns:minmax(0,1fr);min-width:0}
.rv-paineis > section[hidden]{display:none}
.rv-paineis section[data-painel^="inf-"]{display:grid;gap:16px;align-content:start;grid-template-columns:minmax(0,1fr)}
.rv-paineis section[data-painel^="inf-"][hidden]{display:none}
.rv-bl h3{margin-bottom:6px}
.rv-bl p{margin-top:4px}
.rv-dois{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}
.rv-cab{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-bottom:8px}
.rv-cortes td,.rv-cortes th{white-space:nowrap}
.rv-cortes td:nth-child(2){min-width:260px;width:50%}
.rv-cortes .escala{padding-bottom:2px}
.rv-leg{display:flex;gap:6px 18px;flex-wrap:wrap;margin-top:12px;font-size:12px;color:var(--txt-2)}
.rv-leg-i{display:inline-flex;align-items:center;gap:6px}
.rv-leg-i i{width:10px;height:10px;border-radius:3px;display:block}
.rv-bl .tab-caixa{margin-top:6px}
.rv-campo{display:grid;gap:6px;align-content:start}
.rv-intro{max-width:70ch}
.rv-dets{display:grid;gap:10px}
.rv-det{background:var(--papel);border:1px solid var(--fio);border-radius:var(--raio-g)}
.rv-det > summary{list-style:none;display:flex;align-items:center;gap:12px;padding:12px 16px;cursor:pointer;min-height:48px}
.rv-det > summary::-webkit-details-marker{display:none}
.rv-det > summary b{font-weight:600}
.rv-det-s{margin-left:auto;font-size:12px}
.rv-det-seta{color:var(--txt-2)}
.rv-det[open] .rv-det-seta{transform:rotate(180deg)}
.rv-det-c{padding:2px 16px 16px;display:grid;gap:10px}
.rv-chk{width:18px;height:18px;margin:0;cursor:pointer}
.rv-det .tab-caixa{border-radius:8px}
.rv-capa{display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap}
.rv-capa-img{width:190px;aspect-ratio:210/297;background:var(--tela-2);border:1px solid var(--fio);border-radius:8px;display:grid;place-content:center;justify-items:center;gap:6px;color:var(--txt-2);font-weight:600}
.rv-capa-img .ic{width:32px;height:32px}
.rv-capa-info{display:grid;gap:6px;align-content:start;max-width:46ch}
.rv-soltar{display:grid;justify-items:center;text-align:center;gap:8px;padding:40px 20px;border:2px dashed var(--fio-2);border-radius:var(--raio-g);background:var(--tela)}
.rv-soltar p{max-width:48ch}
.rv-soltar-ic{width:36px;height:36px;color:var(--txt-2)}
.rv-grupo{margin:0;padding:10px 12px 6px;font-size:12px;font-weight:600;color:var(--txt-2);background:var(--tela);border-bottom:1px solid var(--fio)}
.rv-sec-n{flex:1;min-width:0;font-weight:550}
.lista-sel .tag{height:20px;font-size:11.5px;padding:0 7px}
.rv-det-sec{display:block;min-width:0}
.rv-sec{display:grid;gap:14px}
.rv-sec[hidden]{display:none}
.rv-sec-cab{display:flex;justify-content:space-between;gap:12px;align-items:center}
.rv-sec-cab h3{font-size:16px}
.rv-vars{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.rv-desat{display:grid;gap:12px;padding:14px;background:var(--alerta-fundo);border-radius:10px}
.rv-desat .diff > div{background:var(--papel)}
.rv-conf{display:grid;grid-template-columns:minmax(0,260px) minmax(0,1fr);gap:28px;align-items:start}
.rv-prev-col{display:grid;gap:10px}
.rv-prev{aspect-ratio:210/297;background:var(--tela-2);border:1px solid var(--fio-2);border-radius:6px;display:grid;place-content:center;justify-items:center;gap:6px;color:var(--txt-2);box-shadow:var(--sombra-p)}
.rv-prev-ic{width:34px;height:34px}
.rv-prev span{font-size:12px}
.rv-conf-dir{display:grid;gap:18px;align-content:start}
.rv-conf-dir .checklist li{padding:8px 0;border-bottom:1px solid var(--fio)}
.rv-conf-dir .checklist li:last-child{border-bottom:0}
.rv-conf-acao{display:flex;gap:12px;align-items:center;flex-wrap:wrap}
.rv-mudou .diff{margin-top:10px}
.rv-rodape{position:sticky;bottom:16px;z-index:20;display:flex;align-items:center;gap:12px;flex-wrap:wrap;background:var(--tinta);color:#fff;border-radius:12px;padding:10px 14px;box-shadow:var(--sombra-g);margin-top:20px}
.rv-rodape .btn{background:var(--tinta-2);border-color:var(--tinta-3);color:#fff;height:32px}
.rv-rodape .btn:hover{background:var(--tinta-3)}
.rv-sep{color:var(--tinta-mudo)}
.rv-prog{display:inline-grid;grid-auto-flow:column;gap:3px}
.rv-prog i{width:16px;height:6px;border-radius:2px;background:var(--tinta-3);display:block}
.rv-prog i.on{background:oklch(0.72 0.14 155)}
@media (max-width:960px){
  .rv-dois,.rv-conf{grid-template-columns:minmax(0,1fr)}
  .rv-prev-col{max-width:260px}
  .rv-rodape{bottom:10px;padding:10px 12px}
  .rv-sep{display:none}
  .passo{padding:10px}
}
"""

JS = r"""
(() => {
  const lista = document.querySelector("[data-secoes]");
  if (!lista) return;
  const btns = [...lista.querySelectorAll("[data-sec]")];
  const mostra = (id) => {
    btns.forEach((b) => b.setAttribute("aria-current", String(b.dataset.sec === id)));
    document.querySelectorAll("[data-sec-p]").forEach((p) => { p.hidden = p.dataset.secP !== id; });
  };
  btns.forEach((b) => b.addEventListener("click", () => mostra(b.dataset.sec)));
})();
"""
