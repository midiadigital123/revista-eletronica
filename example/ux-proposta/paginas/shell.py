"""Casca e componentes da demo. Toda página usa estas funções; ninguém repete HTML de casca.

Contrato para os módulos de página (hoje.py, revistas.py, ...):
    def paginas() -> list[Pagina]          # obrigatório
    CSS = "..."   # opcional: estilos só das suas páginas (vão para app-paginas.css)
    JS  = "..."   # opcional: script só das suas páginas (vai para app-paginas.js)

Atributos data-* que o app.js entende (use-os em vez de escrever JS):
    data-p="ped mid"            visível só para esses perfis (ped, mid, imp, adm)
    data-edita                  vira só leitura para o perfil Impresso (desabilita o controle)
    data-aba="id" / data-painel="id"   abas ou passos: o botão mostra o painel de mesmo id (#id na URL)
    data-abrir="id-do-dialog"   abre <dialog id>; data-fechar fecha o dialog em que está
    data-sel / data-sel-todos   checkbox de linha / "marcar todas"; a .sel-barra aparece com o contador em [data-sel-n]
    data-filtro="#tabela"       <input> que filtra as linhas [data-busca="texto"] do alvo
    data-toast="mensagem"       mostra um aviso passageiro ao clicar
    data-copiar="texto"         copia o texto e avisa
    data-autosave               campo que mostra "Salvo às HH:MM" no [data-salvo] ao sair dele
    data-impacto="id-do-dialog" campo que, ao mudar, abre o dialog de impacto antes de "gravar"

Classes principais (ver app.css): .cab .abas .aba .card .card-p .tab-caixa .tabela .tag .btn .btn-prim .btn-sec
.btn-fan .btn-perigo .btn-ic .fase .regua .aviso .vazio .campo .input .select .textarea .dividido .lista-sel
.passos .passo .esteira .cartao-rev .grade .cel .escala .diff .var .sel-barra .dialogo .gaveta
"""
import html
import json
import re

import dados as D

CASCA_PERFIL = "ped"


def esc(s):
    return html.escape(str(s), quote=True)


# ── Ícones: um conjunto só, traço 1.75, desenhados em 24×24 ────────────────
_ICONES = {
    "lista": '<path d="M4 6l1.6 1.6L8.4 4.8M4 12l1.6 1.6 2.8-2.8M4 18l1.6 1.6 2.8-2.8M11 6.5h9M11 12.5h9M11 18.5h9"/>',
    "camadas": '<path d="M12 3.5l9 4.8-9 4.8-9-4.8 9-4.8zM3 13l9 4.8 9-4.8M3 17.5L12 22l9-4.5"/>',
    "pessoas": '<circle cx="9" cy="8" r="3.4"/><path d="M2.8 20c0-3.5 2.8-5.8 6.2-5.8s6.2 2.3 6.2 5.8M16.5 4.8a3.2 3.2 0 010 6.4M18.2 14.6c2 .7 3.3 2.4 3.3 5.4"/>',
    "pacote": '<path d="M3.5 8L12 3.5 20.5 8v8L12 20.5 3.5 16V8zM3.5 8L12 12.5 20.5 8M12 12.5v8"/>',
    "livro": '<path d="M5 4.5A1.5 1.5 0 016.5 3H19v15H6.5A1.5 1.5 0 005 19.5v-15zM5 19.5A1.5 1.5 0 006.5 21H19v-3"/>',
    "arquivo": '<path d="M6 3h8l5 5v13H6V3zM14 3v5h5M9 13h7M9 17h7"/>',
    "ajustes": '<path d="M4 7h9M17 7h3M4 17h3M11 17h9M15 4.5v5M9 14.5v5"/>',
    "calendario": '<rect x="4" y="5" width="16" height="15" rx="2"/><path d="M4 10h16M9 3v4M15 3v4"/>',
    "busca": '<circle cx="11" cy="11" r="6"/><path d="M15.5 15.5L20 20"/>',
    "mais": '<path d="M12 5v14M5 12h14"/>',
    "ok": '<path d="M5 12.5l4.5 4.5L19 7.5"/>',
    "x": '<path d="M6 6l12 12M18 6L6 18"/>',
    "seta": '<path d="M5 12h14M13 6l6 6-6 6"/>',
    "volta": '<path d="M19 12H5M11 6l-6 6 6 6"/>',
    "dir": '<path d="M9 6l6 6-6 6"/>',
    "baixo": '<path d="M6 9l6 6 6-6"/>',
    "alerta": '<path d="M12 4l9.5 16h-19L12 4zM12 10v4.5M12 17.4v.1"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.1"/>',
    "olho": '<path d="M2.5 12S6 5.8 12 5.8 21.5 12 21.5 12 18 18.2 12 18.2 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="2.8"/>',
    "baixar": '<path d="M12 4v11M7 11l5 5 5-5M5 20h14"/>',
    "subir": '<path d="M12 16V5M7 9l5-5 5 5M5 20h14"/>',
    "pontos": '<circle cx="12" cy="5.5" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="12" cy="18.5" r="1.2"/>',
    "cadeado": '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/>',
    "usuario": '<circle cx="12" cy="8" r="3.6"/><path d="M5 20c0-3.6 3-6 7-6s7 2.4 7 6"/>',
    "copiar": '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V6a2 2 0 00-2-2H6a2 2 0 00-2 2v8a2 2 0 002 2h2"/>',
    "link": '<path d="M10 14a4 4 0 005.7 0l3-3a4 4 0 00-5.7-5.7l-1 1M14 10a4 4 0 00-5.7 0l-3 3a4 4 0 005.7 5.7l1-1"/>',
    "lixeira": '<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "relogio": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "imagem": '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="1.8"/><path d="M21 16l-5-5-8 8"/>',
    "historico": '<path d="M4 12a8 8 0 108-8 8 8 0 00-6 2.7M4 4v4h4M12 8v4l3 2"/>',
    "lapis": '<path d="M4 20l1-4L16 5l3 3L8 19l-4 1zM14 7l3 3"/>',
    "externo": '<path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1h5"/>',
    "escudo": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3z"/>',
    "sair": '<path d="M10 4H6a2 2 0 00-2 2v12a2 2 0 002 2h4M15 8l4 4-4 4M19 12H9"/>',
    "aberto": '<circle cx="12" cy="12" r="7.5"/>',
    "traco": '<path d="M7 12h10"/>',
    "confirmado": '<circle cx="12" cy="12" r="9"/><path d="M8 12.4l2.8 2.8L16 9.6"/>',
    "filtro": '<path d="M4 5h16l-6 8v6l-4-2v-4L4 5z"/>',
    "grade": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 10h16M4 15h16M10 4v16"/>',
    "colunas": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M9.5 4v16M14.5 4v16"/>',
    "estrela": '<path d="M12 3.5l2.6 5.4 5.9.8-4.3 4.1 1 5.9L12 16.9l-5.2 2.8 1-5.9-4.3-4.1 5.9-.8L12 3.5z"/>',
}


def _sprite():
    simbolos = "".join(f'<symbol id="i-{n}" viewBox="0 0 24 24">{p}</symbol>' for n, p in _ICONES.items())
    return (
        '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false" '
        f'fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">{simbolos}</svg>'
    )


def ic(nome, cls=""):
    return f'<svg class="ic {cls}" aria-hidden="true" focusable="false"><use href="#i-{nome}"/></svg>'


# ── Peças pequenas ────────────────────────────────────────────────────────
def regua_mini(f, extra=""):
    """Glifo de 5 trechos preenchidos até a fase f (a "régua" da esteira)."""
    nome = D.FASE_NOME[f]
    return (
        f'<span class="regua {extra}" data-f="{f}" role="img" aria-label="Fase {f} de 5: {esc(nome)}">'
        + "<i></i>" * 5
        + "</span>"
    )


def regua(f):
    """Régua + nome da fase, em uma etiqueta."""
    return f'<span class="fase">{regua_mini(f)}<span class="fase-nome">{esc(D.FASE_NOME[f])}</span></span>'


def tag(texto, tom="", icone=None):
    i = ic(icone) if icone else ""
    return f'<span class="tag{" tag-" + tom if tom else ""}">{i}{esc(texto)}</span>'


def st(status, titulo=""):
    """Célula de status: ok (verde, check), pend (âmbar, círculo aberto), na (traço)."""
    nome = {"ok": "ok", "pend": "aberto", "na": "traco"}[status]
    rot = titulo or {"ok": "Pronto", "pend": "Pendente", "na": "Não se aplica"}[status]
    return f'<span class="st st-{status}" title="{esc(rot)}" role="img" aria-label="{esc(rot)}">{ic(nome)}</span>'


def btn(texto, href=None, tom="sec", icone=None, attrs="", cls=""):
    i = ic(icone) if icone else ""
    c = f"btn btn-{tom} {cls}".strip()
    if href:
        return f'<a class="{c}" href="{esc(href)}" {attrs}>{i}{texto}</a>'
    return f'<button type="button" class="{c}" {attrs}>{i}{texto}</button>'


def btn_ic(icone, rotulo, href=None, attrs=""):
    corpo = ic(icone)
    if href:
        return f'<a class="btn-ic" href="{esc(href)}" aria-label="{esc(rotulo)}" title="{esc(rotulo)}" {attrs}>{corpo}</a>'
    return f'<button type="button" class="btn-ic" aria-label="{esc(rotulo)}" title="{esc(rotulo)}" {attrs}>{corpo}</button>'


def menu(rotulo, itens, icone=None, cls="btn"):
    """Menu suspenso. itens: lista de <a>/<button>/<hr> prontos (use class="perigo" no destrutivo)."""
    i = ic(icone) if icone else ""
    return f'<details class="menu"><summary class="{cls}">{i}{rotulo}</summary><div class="menu-lista">{"".join(itens)}</div></details>'


def menu_ic(itens, rotulo="Mais ações"):
    """Menu de três pontos (só ícone)."""
    return (
        f'<details class="menu"><summary class="btn-ic" aria-label="{esc(rotulo)}" title="{esc(rotulo)}">{ic("pontos")}</summary>'
        f'<div class="menu-lista">{"".join(itens)}</div></details>'
    )


def item_menu(rotulo, href=None, icone=None, perigo=False, attrs=""):
    i = ic(icone) if icone else ""
    c = ' class="perigo"' if perigo else ""
    if href:
        return f'<a href="{esc(href)}"{c} {attrs}>{i}{rotulo}</a>'
    return f'<button type="button"{c} {attrs}>{i}{rotulo}</button>'


def cab(titulo, sub="", acoes=""):
    s = f'<p class="sub">{sub}</p>' if sub else ""
    a = f'<div class="cab-acoes">{acoes}</div>' if acoes else ""
    return f'<header class="cab"><div class="cab-txt"><h1>{titulo}</h1>{s}</div>{a}</header>'


def abas_js(itens, atual=None):
    """itens: [(id, rotulo, contagem|None)]. Painéis: <section data-painel="id">."""
    atual = atual or itens[0][0]
    bs = []
    for i, rot, n in itens:
        sel = "true" if i == atual else "false"
        cont = f'<span class="n">{n}</span>' if n is not None else ""
        bs.append(f'<button type="button" class="aba" role="tab" data-aba="{i}" aria-selected="{sel}">{esc(rot)}{cont}</button>')
    return f'<div class="abas" role="tablist" data-abas>{"".join(bs)}</div>'


def abas_links(itens, atual):
    """itens: [(rotulo, href, contagem|None)]; atual = rótulo da aba atual."""
    out = []
    for rot, href, n in itens:
        cur = ' aria-current="page"' if rot == atual else ""
        cont = f'<span class="n">{n}</span>' if n is not None else ""
        out.append(f'<a class="aba" href="{esc(href)}"{cur}>{esc(rot)}{cont}</a>')
    return f'<nav class="abas" aria-label="Seções">{"".join(out)}</nav>'


def aviso(texto, tom="info", icone=None, acao=""):
    icone = icone or {"info": "info", "alerta": "alerta", "erro": "alerta", "ok": "confirmado", "leitura": "cadeado"}[tom]
    a = f'<div class="aviso-acao">{acao}</div>' if acao else ""
    return f'<div class="aviso aviso-{tom}" role="status">{ic(icone)}<div class="aviso-txt">{texto}</div>{a}</div>'


def vazio(titulo, texto, acao=""):
    a = f'<div class="vazio-acao">{acao}</div>' if acao else ""
    return f'<div class="vazio"><h3>{titulo}</h3><p>{texto}</p>{a}</div>'


def dialogo(id_, titulo, corpo, rodape="", largo=False):
    cls = "dialogo dialogo-largo" if largo else "dialogo"
    rod = f"<footer>{rodape}</footer>" if rodape else ""
    return (
        f'<dialog class="{cls}" id="{id_}" aria-labelledby="{id_}-t"><div class="dlg-cab"><h2 id="{id_}-t">{titulo}</h2>'
        f'{btn_ic("x", "Fechar", attrs="data-fechar")}</div><div class="dlg-corpo">{corpo}</div>{rod}</dialog>'
    )


def gaveta(id_, titulo, corpo, rodape=""):
    rod = f"<footer>{rodape}</footer>" if rodape else ""
    return (
        f'<dialog class="gaveta" id="{id_}" aria-labelledby="{id_}-t"><div class="dlg-cab"><h2 id="{id_}-t">{titulo}</h2>'
        f'{btn_ic("x", "Fechar", attrs="data-fechar")}</div><div class="dlg-corpo">{corpo}</div>{rod}</dialog>'
    )


def campo(rotulo, nome, valor="", tipo="text", ajuda="", attrs="", textarea=False):
    aj = f'<span class="ajuda">{ajuda}</span>' if ajuda else ""
    if textarea:
        ctl = f'<textarea class="textarea" name="{nome}" {attrs}>{esc(valor)}</textarea>'
    else:
        ctl = f'<input class="input" type="{tipo}" name="{nome}" value="{esc(valor)}" {attrs}>'
    return f'<label class="campo"><span class="rot">{rotulo}</span>{ctl}{aj}</label>'


def selecao(rotulo, nome, opcoes, atual=None, attrs=""):
    ops = "".join(f'<option value="{esc(v)}"{" selected" if v == atual else ""}>{esc(t)}</option>' for v, t in opcoes)
    return f'<label class="campo"><span class="rot">{rotulo}</span><select class="select" name="{nome}" {attrs}>{ops}</select></label>'


def tabela(cabecalho, linhas, cls="", id_=""):
    """cabecalho: [str | (str, classe)]. linhas: [[html] | (attrs, [html])]. Devolve a caixa rolável com a tabela."""
    th = ""
    for c in cabecalho:
        txt, k = (c, "") if isinstance(c, str) else c
        th += f'<th class="{k}">{txt}</th>' if k else f"<th>{txt}</th>"
    corpo = ""
    for l in linhas:
        attrs, cels = ("", l) if isinstance(l, list) else l
        corpo += f"<tr {attrs}>" + "".join(f"<td>{c}</td>" for c in cels) + "</tr>"
    i = f' id="{id_}"' if id_ else ""
    return f'<div class="tab-caixa"><table class="tabela {cls}"{i}><thead><tr>{th}</tr></thead><tbody>{corpo}</tbody></table></div>'


def escala(cortes, maximo, altura=14):
    """Barra da escala com os Padrões 01..N (cores = dado do sistema) e os cortes marcados."""
    pontos = [0, *cortes, maximo]
    seg = ""
    for k in range(len(pontos) - 1):
        n, nome, cor = D.PADROES[k]
        w = pontos[k + 1] - pontos[k]
        seg += (
            f'<span class="esc-seg" style="flex:{w};background:{cor}" title="Padrão 0{n} · {esc(nome)}: {pontos[k]} a {pontos[k+1]}"></span>'
        )
    rotulos = "".join(f'<span style="left:{c / maximo * 100:.2f}%">{c}</span>' for c in cortes)
    return f'<div class="escala" style="--h:{altura}px"><div class="esc-barra">{seg}</div><div class="esc-rot">{rotulos}</div></div>'


def avatar(pessoa):
    ini = "".join(p[0] for p in pessoa["nome"].split()[:2])
    return f'<span class="avatar" aria-hidden="true">{esc(ini)}</span>'


def status_salvo():
    return '<span class="salvo" data-salvo aria-live="polite"></span>'


def href_revista(rid):
    return f"revista-{rid}.html"


def href_parceiro(pid):
    return f"parceiro-{pid}.html"


def nome_revista(r):
    return f'{r["nome_parceiro"]} · {r["comp"]}'


# ── Casca ─────────────────────────────────────────────────────────────────
class Pagina:
    def __init__(self, arquivo, titulo, secao, corpo, trilha=(), largura="", solo=False, status=False, topo_extra=""):
        self.arquivo, self.titulo, self.secao, self.corpo = arquivo, titulo, secao, corpo
        self.trilha, self.largura, self.solo, self.status, self.topo_extra = trilha, largura, solo, status, topo_extra


def _nav_item(secao_atual, secao, rotulo, href, icone, n=None, extra="", attrs=""):
    cur = ' aria-current="page"' if secao_atual == secao else ""
    cont = f'<span class="n">{n}</span>' if n is not None else ""
    return f'<a href="{href}"{cur} {attrs}>{ic(icone)}<span>{rotulo}</span>{cont}{extra}</a>'


def _rail(secao):
    cnt = D.contagem_fases()
    n_ped = cnt[3]
    n_imp = cnt[4]
    n_adm = n_ped + n_imp
    entrega = (
        f'<span class="n n-acao" data-n-ped="{n_ped}" data-n-mid="{n_ped}" data-n-imp="{n_imp}" data-n-adm="{n_adm}">{n_ped}</span>'
    )
    marca = '<span class="regua marca-regua" data-f="5" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span>'
    perfis = "".join(f'<option value="{k}">{v} · {D.EU[k]["nome"].split()[0]}</option>' for k, v in D.PERFIS.items())
    return f"""
<aside class="rail" id="rail" aria-label="Navegação principal">
  <div class="rail-topo"><a class="marca" href="index.html">{marca}<span>Revista Express</span></a>
    <button type="button" class="btn-ic rail-fechar" data-rail aria-label="Fechar menu">{ic("x")}</button></div>
  <details class="temp">
    <summary>{ic("calendario")}<span>Temporada <b>{D.ANO}</b></span>{ic("baixo", "temp-seta")}</summary>
    <div class="temp-menu">
      <a href="index.html" aria-current="true">{D.ANO}<span class="mudo">atual</span></a>
      <a href="index.html">2025<span class="mudo">somente leitura</span></a>
      <hr>
      <a href="ano.html">{ic("ajustes")}Configurar o ano</a>
      <a href="ano-abrir.html" data-p="ped mid adm">{ic("mais")}Abrir {D.ANO_PROX}</a>
    </div>
  </details>
  <button type="button" class="busca-btn" data-abrir="paleta">{ic("busca")}<span>Buscar</span><kbd>Ctrl K</kbd></button>
  <nav class="rail-nav" aria-label="Trabalho da temporada">
    {_nav_item(secao, "hoje", "Hoje", "index.html", "lista")}
    {_nav_item(secao, "revistas", "Revistas", "revistas.html", "camadas", len(D.REVISTAS))}
    {_nav_item(secao, "parceiros", "Parceiros", "parceiros.html", "pessoas", len(D.PARCEIROS))}
    {_nav_item(secao, "entrega", "Entrega", "entrega-validar.html", "pacote", extra=entrega, attrs='data-href-imp="entrega-impresso.html"')}
  </nav>
  <p class="rail-grupo">Biblioteca</p>
  <nav class="rail-nav" aria-label="Biblioteca">
    {_nav_item(secao, "matrizes", "Matrizes", "matrizes.html", "livro", len(D.MATRIZES))}
    {_nav_item(secao, "templates", "Templates", "templates.html", "arquivo", len(D.TEMPLATES))}
  </nav>
  <div class="rail-rodape">
    <nav class="rail-nav" aria-label="Sistema">
      {_nav_item(secao, "ano", "Configurar o ano", "ano.html", "ajustes")}
      {_nav_item(secao, "usuarios", "Usuários", "usuarios.html", "usuario", attrs='data-p="adm"')}
      <a href="https://example.invalid/admin/" data-p="adm" onclick="return false" title="Só superusuário">{ic("escudo")}<span>Admin do Django</span></a>
      {_nav_item(secao, "sobre", "Sobre esta proposta", "sobre.html", "info")}
    </nav>
    <label class="perfil-demo"><span>Ver como (demo)</span><select data-perfil-sel aria-label="Ver como">{perfis}</select></label>
    <div class="pessoa"><span class="avatar" data-avatar>AS</span><div class="pessoa-txt"><b data-pessoa>Ana Souza</b><span class="mudo" data-perfil-nome>Pedagógica</span></div>
      <a class="btn-ic sair" href="entrar.html" aria-label="Sair" title="Sair">{ic("sair")}</a></div>
  </div>
</aside>"""


def _paleta():
    return (
        '<dialog class="dialogo paleta" id="paleta" aria-label="Buscar">'
        f'<div class="paleta-cab">{ic("busca")}<input type="search" id="paleta-q" placeholder="Parceiro, revista, descritor, template…" autocomplete="off" aria-label="Buscar">'
        '<kbd>Esc</kbd></div><ul id="paleta-lista" class="paleta-lista"></ul></dialog>'
    )


_TIT = re.compile(r"<(/?)h([1-6])((?:\s[^>]*)?)>")


def _corrige_titulos(h):
    """Nenhum título pode pular nível (h1 → h3). O nível semântico é rebaixado e o original vai em data-n,
    que o app.css usa para manter o tamanho visual que o módulo escolheu."""
    pilha, ant = [], 0

    def troca(m):
        nonlocal ant
        fecha, n, resto = m.group(1), int(m.group(2)), m.group(3)
        if fecha:
            novo = pilha.pop() if pilha else n
            return f"</h{novo}>"
        novo = min(n, ant + 1) if ant else n
        ant = novo
        pilha.append(novo)
        marca = f' data-n="{n}"' if novo != n else ""
        return f"<h{novo}{resto}{marca}>"

    return _TIT.sub(troca, h)


def render(p):
    indice = json.dumps(D.indice_busca(), ensure_ascii=False)
    cab_head = (
        '<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{esc(p.titulo)} · Revista Express (demo)</title>"
        '<link rel="stylesheet" href="app.css"><link rel="stylesheet" href="app-paginas.css">'
        "<script>try{document.documentElement.dataset.perfil=localStorage.getItem('perfil')||'ped'}catch(e){document.documentElement.dataset.perfil='ped'}</script>"
    )
    fim = (
        f'<div class="toasts" id="toasts" aria-live="polite"></div><script>window.INDICE={indice};</script>'
        '<script src="app.js" defer></script><script src="app-paginas.js" defer></script>'
    )
    if p.solo:
        return _corrige_titulos(f'<!doctype html><html lang="pt-BR"><head>{cab_head}</head><body class="solo">{_sprite()}{p.corpo}{fim}</body></html>')
    partes = []
    for i, (rot, href) in enumerate(p.trilha):
        ultimo = i == len(p.trilha) - 1
        partes.append(f'<span aria-current="page">{rot}</span>' if (ultimo or not href) else f'<a href="{href}">{rot}</a>')
    sep = f'<span class="sep">{ic("dir")}</span>'
    trilha = f'<nav class="trilha" aria-label="Você está em">{sep.join(partes)}</nav>' if partes else '<span class="trilha"></span>'
    salvo = status_salvo() if p.status else ""
    return _corrige_titulos(
        f'<!doctype html><html lang="pt-BR"><head>{cab_head}</head><body>{_sprite()}'
        f'<a class="pular" href="#conteudo">Pular para o conteúdo</a>{_rail(p.secao)}'
        f'<div class="principal"><header class="topo"><button type="button" class="btn-ic hamb" data-rail aria-label="Abrir menu">{ic("menu")}</button>'
        f'{trilha}<div class="topo-dir">{p.topo_extra}{salvo}</div></header>'
        f'<main id="conteudo" class="pagina {p.largura}">{p.corpo}</main></div>{_paleta()}'
        f'<div class="rail-fundo" data-rail></div>{fim}</body></html>'
    )
