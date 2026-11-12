"""Hoje: "o que eu faço agora?" por perfil. Uma tarefa em destaque, a régua da temporada e o apoio ao lado."""
import dados as D
from paginas import parceiros as PA
from paginas import shell as S
from paginas.revistas import estado, pl

_MIN = {"vale-verde-lp": 4, "costa-dourada-mt": 11}  # há quantos minutos cada edição começou


def _contagens():
    cnt = D.contagem_fases()
    montagem = D.revistas_na_fase(2)
    est = [estado(r)[0] for r in montagem]
    return {
        "cnt": cnt,
        "total": len(D.REVISTAS),
        "inf_ou_capa": sum(1 for p in est if p["infograficos"] == "pend" or p["capa"] == "pend"),
        "capa": sum(1 for p in est if p["capa"] == "pend"),
        "inf": sum(1 for p in est if p["infograficos"] == "pend"),
        "validadas": cnt[4] + cnt[5],
        "cortes_vazios": sum(1 for p in D.PARCEIROS for e, _ in D.ETAPAS for c, _ in D.COMPONENTES if not PA.corte(p["id"], e, c)),
        "var_vazias": sum(1 for p in D.PARCEIROS for k, *_ in D.VARIAVEIS if not PA.valor_var(p["id"], k)),
        "sem_matriz": sum(1 for p in D.PARCEIROS if not p["matriz"]),
    }


def _linha(n, texto, href):
    return f'<a class="h-linha" href="{href}"><b class="h-n">{n}</b><span class="h-txt">{texto}</span>{S.ic("dir")}</a>'


def _foco(perfil, lead, botao, linhas, extra=""):
    return (
        f'<section class="card h-foco" data-p="{perfil}" aria-labelledby="h-foco-t-{perfil}">'
        f'<h2 id="h-foco-t-{perfil}" class="h-lead">{lead}</h2><div class="h-acao">{botao}{extra}</div>'
        f'<div class="h-linhas">{"".join(linhas)}</div></section>'
    )


def _focos(c):
    cnt = c["cnt"]
    n3, n1, n2 = cnt[3], cnt[1], cnt[2]
    validar = S.btn(f"Conferir e validar {pl(n3, 'revista', 'revistas')}", "entrega-validar.html", "prim", "confirmado", cls="btn-grande")
    ped = _foco(
        "ped",
        f"{pl(n3, 'revista está', 'revistas estão')} na fase Conferir, com todos os passos prontos. Falta olhar o preview e validar.",
        validar,
        [
            _linha(n1, f"Ver {pl(n1, 'revista', 'revistas')} em Preparar: faltam matriz, cortes ou dados do parceiro", "revistas.html?fase=1"),
            _linha(c["inf_ou_capa"], f"Abrir as {pl(c['inf_ou_capa'], 'revista', 'revistas')} em Montar com infográfico ou capa pendente", "revistas.html?fase=2"),
            _linha(c["cortes_vazios"], "Preencher as células de cortes que estão sem dado", "parceiros.html#cortes"),
        ],
    )
    mid = _foco(
        "mid",
        f"{pl(n3, 'revista está', 'revistas estão')} prontas para conferir. Antes, gere os pacotes das que já foram validadas.",
        validar,
        [
            _linha(c["validadas"], f"{'revista validada' if c['validadas'] == 1 else 'revistas validadas'}: gerar pacotes", "entrega-pacotes.html"),
            _linha(c["capa"], f"{'revista esperando' if c['capa'] == 1 else 'revistas esperando'} a capa", "revistas.html?fase=2"),
            _linha(c["inf"], f"{'revista com' if c['inf'] == 1 else 'revistas com'} infográfico pendente", "revistas.html?fase=2"),
        ],
    )
    imp = _foco(
        "imp",
        f"{pl(cnt[4], 'revista foi validada', 'revistas foram validadas')} e o impresso ainda está na versão anterior.",
        S.btn(f"Atualizar o impresso de {pl(cnt[4], 'revista', 'revistas')}", "entrega-impresso.html", "prim", "pacote", cls="btn-grande"),
        [
            _linha(cnt[5], f"{'revista com' if cnt[5] == 1 else 'revistas com'} o impresso em dia", "revistas.html?fase=5"),
            _linha(n3, f"em conferência: chegam ao impresso depois de validadas", "revistas.html?fase=3"),
        ],
    )
    adm = _foco(
        "adm",
        f"A temporada {D.ANO} está com {c['validadas']} de {c['total']} revistas validadas. Abrir {D.ANO_PROX} copia a configuração de {D.ANO}; "
        f"{D.ANO} continua acessível, só para leitura.",
        S.btn(f"Abrir {D.ANO_PROX}", "ano-abrir.html", "prim", "mais", cls="btn-grande"),
        [
            _linha(n3, f"{'revista para' if n3 == 1 else 'revistas para'} conferir e validar", "entrega-validar.html"),
            _linha(n1, f"{pl(n1, 'revista', 'revistas')} ainda sem matriz ou cortes", "revistas.html?fase=1"),
        ],
        extra=S.btn(f"Conferir e validar {pl(n3, 'revista', 'revistas')}", "entrega-validar.html", "sec"),
    )
    leitura = (
        '<div data-p="imp">'
        + S.aviso("Você acompanha tudo, mas só grava a marcação de impressa. Para alterar uma revista, peça à equipe Pedagógica ou de Mídias Digitais.", "leitura")
        + "</div>"
    )
    return ped + mid + imp + adm + leitura


def _regua(c):
    cnt, total = c["cnt"], c["total"]
    trechos = "".join(
        f'<a class="trecho" href="revistas.html?fase={f}" data-f="{f}" style="--n:{cnt[f]}" '
        f'aria-label="{S.esc(nome)}: {pl(cnt[f], "revista", "revistas")}" title="{S.esc(nome)}: {pl(cnt[f], "revista", "revistas")} ({round(cnt[f] / total * 100)}%)">'
        f"<b>{cnt[f]}</b><span>{S.esc(nome)}</span></a>"
        for f, _, nome, _ in D.FASES
    )
    sua = {3: ("ped mid adm", "Sua fila"), 4: ("imp", "Sua fila")}
    leg = ""
    for f, _, nome, desc in D.FASES:
        marca = f'<span class="tag tag-cobalto" data-p="{sua[f][0]}">{sua[f][1]}</span>' if f in sua else ""
        leg += (
            f'<li><a class="h-leg-i" href="revistas.html?fase={f}"><span class="h-leg-t"><i class="h-sw" data-f="{f}"></i>'
            f'<b>{S.esc(nome)}</b><span class="h-leg-n">{cnt[f]}</span>{marca}</span>'
            f'<span class="mudo">{S.esc(desc)}</span></a></li>'
        )
    return (
        '<section class="card card-p h-regua" aria-labelledby="h-reg-t">'
        f'<div class="h-regua-cab"><div><h2 id="h-reg-t">A temporada {D.ANO}</h2>'
        f'<p class="sub">{total} revistas, da matriz ao impresso. Cada trecho é uma fase e a largura é o número de revistas.</p></div>'
        + S.btn("Ver todas", "revistas.html", "fan", "dir", cls="btn-sm")
        + f'</div><div class="regua-temp">{trechos}</div><ol class="h-leg">{leg}</ol></section>'
    )


def _pessoa(nome):
    return next((p for p in D.PESSOAS if p["nome"] == nome), D.PESSOAS[0])


def _editando():
    itens = ""
    for rid, quem in D.EDITANDO.items():
        r = D.POR_ID[rid]
        itens += (
            f'<li class="h-ed">{S.avatar(_pessoa(quem))}<div><b>{S.esc(quem)}</b> <span class="mudo">há {_MIN.get(rid, 5)} min</span>'
            f'<br><a href="{S.href_revista(rid)}">{S.esc(S.nome_revista(r))}</a></div></li>'
        )
    return (
        '<section class="card card-p" aria-labelledby="h-ed-t"><h2 id="h-ed-t">Em edição agora</h2>'
        f'<ul class="h-lista">{itens}</ul>'
        f'<p class="h-nota mudo">{S.ic("cadeado")}Quem abrir uma dessas revistas depois vê só leitura, até a edição terminar.</p></section>'
    )


def _atividade():
    itens = ""
    for quem, acao, quando in D.ATIVIDADES:
        for r in D.REVISTAS:
            nome = S.nome_revista(r)
            if nome in acao:
                acao = acao.replace(nome, f'<a href="{S.href_revista(r["id"])}">{S.esc(nome)}</a>')
        itens += f'<li><span><b>{S.esc(quem)}</b> {acao}</span><span class="mudo h-quando">{S.esc(quando)}</span></li>'
    return f'<section class="card card-p" aria-labelledby="h-at-t"><h2 id="h-at-t">Atividade recente</h2><ul class="h-lista h-ativ">{itens}</ul></section>'


def _preparar(c):
    itens = [
        ("ok", "Etapas e componentes", f"{len(D.ETAPAS)} etapas, {len(D.COMPONENTES)} componentes", "ano.html"),
        ("ok", "Padrões de desempenho", f"{len(D.PADROES)} padrões", "ano.html"),
        ("ok", "Parceiros", f"{len(D.PARCEIROS)} cadastrados", "parceiros.html"),
        ("pend", "Cortes", f"{c['cortes_vazios']} células sem dado", "parceiros.html#cortes"),
        ("pend", "Matriz", f"{pl(c['sem_matriz'], 'parceiro sem matriz', 'parceiros sem matriz')}", "parceiros.html"),
        ("pend", "Variáveis", f"{c['var_vazias']} vazias", "parceiros.html#variaveis"),
    ]
    prontos = sum(1 for s, *_ in itens if s == "ok")
    li = "".join(
        f'<li>{S.st(s)}<a href="{h}">{S.esc(t)}</a><small>{S.esc(d)}</small></li>' for s, t, d, h in itens
    )
    return (
        '<section class="card card-p" aria-labelledby="h-pr-t"><div class="h-cab-s"><h2 id="h-pr-t">Preparar o ano</h2>'
        f'<span class="mudo">{prontos} de {len(itens)} itens</span></div><ul class="checklist h-prep">{li}</ul></section>'
    )


def corpo():
    c = _contagens()
    sub = 'Olá, <span data-pessoa>Ana Souza</span>. Quinta-feira, 12 de novembro de 2026.'
    return (
        S.cab("Hoje", sub)
        + '<div class="h-grade"><div class="h-main">'
        + _focos(c)
        + _regua(c)
        + '</div><div class="h-lado">'
        + _editando()
        + _preparar(c)
        + _atividade()
        + "</div></div>"
    )


def paginas():
    return [S.Pagina("index.html", "Hoje", "hoje", corpo(), trilha=[("Hoje", None)])]


CSS = """
/* ── Hoje ────────────────────────────────────────────────────────────── */
.h-grade{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1fr);gap:20px;align-items:start}
.h-main,.h-lado{display:grid;gap:20px;min-width:0}
.h-lado .card h2{font-size:14px}
.h-sup{font-size:13px;font-weight:600;color:var(--txt-2);letter-spacing:0}
.h-foco{padding:22px 24px 0;overflow:hidden}
.h-lead{font-size:17px;line-height:1.4;margin:8px 0 18px;max-width:52ch;text-wrap:pretty}
.h-acao{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:22px}
.btn-grande{height:46px;padding:0 22px;font-size:16px;border-radius:10px}
.btn-grande .ic{width:18px;height:18px}
.h-linhas{display:grid;margin:0 -24px;border-top:1px solid var(--fio)}
.h-linha{display:flex;align-items:center;gap:14px;padding:12px 24px;color:var(--txt);text-decoration:none;border-bottom:1px solid var(--fio);transition:background .12s var(--ease)}
.h-linha:last-child{border-bottom:0}
.h-linha:hover{background:var(--tela)}
.h-linha .ic{margin-left:auto;color:var(--txt-2)}
.h-n{min-width:34px;height:28px;padding:0 8px;display:inline-grid;place-items:center;border-radius:8px;background:var(--alerta-fundo);color:var(--alerta);font-weight:650}
.h-txt{min-width:0}
.h-regua{padding:20px 24px 22px}
.h-regua-cab{display:flex;gap:12px;justify-content:space-between;align-items:flex-start;margin-bottom:16px;flex-wrap:wrap}
.h-regua-cab h2{font-size:18px}
.h-regua-cab .sub{margin-top:2px;max-width:60ch}
.regua-temp{height:92px;gap:4px}
.regua-temp .trecho{padding:10px 12px;border-radius:8px;min-width:64px}
.regua-temp .trecho b{font-size:30px;letter-spacing:-.02em}
.regua-temp .trecho span{font-size:13px}
.regua-temp .trecho[data-f="1"]{box-shadow:inset 0 0 0 1px var(--fio-2)}
.regua-temp:hover .trecho:not(:hover){opacity:.7}
.regua-temp .trecho:hover{filter:none;transform:translateY(-2px);box-shadow:0 6px 16px oklch(0.2 0.03 263 / .18)}
html[data-perfil="ped"] .trecho[data-f="3"],html[data-perfil="mid"] .trecho[data-f="3"],html[data-perfil="adm"] .trecho[data-f="3"],
html[data-perfil="imp"] .trecho[data-f="4"]{outline:2px solid var(--txt);outline-offset:3px}
.h-leg{list-style:none;margin:18px 0 0;padding:0;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px}
.h-leg-i{display:grid;gap:4px;color:inherit;text-decoration:none;font-size:12.5px;line-height:1.4;padding:8px 8px 6px;margin:-8px -8px -6px;border-radius:8px;align-content:start}
.h-leg-i:hover{background:var(--tela)}
.h-leg-t{display:flex;align-items:center;gap:6px;flex-wrap:wrap}
.h-leg-t b{font-size:14px}
.h-leg-n{color:var(--txt-2);font-weight:600}
.h-leg-t .tag{height:18px;font-size:11px;padding:0 6px}
.h-sw{width:10px;height:10px;border-radius:3px;display:block;flex:none;background:var(--c)}
.h-sw[data-f="1"]{--c:var(--r1);outline:1px solid var(--fio-2)}.h-sw[data-f="2"]{--c:var(--r2)}.h-sw[data-f="3"]{--c:var(--r3)}.h-sw[data-f="4"]{--c:var(--r4)}.h-sw[data-f="5"]{--c:var(--r5)}
.h-lista{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:12px}
.h-ed{display:flex;gap:10px;align-items:flex-start;line-height:1.35}
.h-nota{display:flex;gap:8px;margin-top:14px;font-size:12.5px}
.h-nota .ic{margin-top:1px}
.h-ativ li{display:flex;gap:10px;justify-content:space-between;align-items:baseline;font-size:13px;line-height:1.4}
.h-quando{white-space:nowrap;font-size:12px}
.h-cab-s{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.h-prep{margin-top:6px}
.h-prep li{padding:6px 0}
.h-prep small{margin-left:auto;text-align:right}
.h-prep li > a{flex:0 1 auto}
@media (max-width:1240px){.h-leg{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media (max-width:960px){
  .h-grade{grid-template-columns:minmax(0,1fr)}
  .h-foco{padding:18px 18px 0}.h-linhas{margin:0 -18px}.h-linha{padding:12px 18px}
  .h-lead{font-size:16px}
}
@media (max-width:640px){
  .regua-temp{height:76px;gap:3px}
  .regua-temp .trecho{min-width:0;padding:8px 6px}
  .regua-temp .trecho span{display:none}
  .regua-temp .trecho b{font-size:22px}
  .h-leg{grid-template-columns:1fr}
  .h-regua{padding:16px}
}
"""
