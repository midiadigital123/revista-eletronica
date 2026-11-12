"""Revistas: a esteira de 5 fases (e a mesma lista em tabela). Substitui Painel, Lista de Projetos e a aba Revistas.

Este módulo também guarda os ajudantes que revista.py e hoje.py reaproveitam (estado, curto, pl).
"""
import json
import re

import dados as D
from paginas import shell as S

_SEM_MATRIZ_ALT = "4 de 24 variáveis vazias"


def pl(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


def estado(r):
    """Passos e pendências de uma revista, corrigindo no local o que dados.py deixa incoerente.

    - texto de pendência cita o componente certo (dados.py escreve sempre "LP");
    - "Sem matriz" só vale para parceiro sem matriz; com matriz, vira outra pendência de Base;
    - parceiro sem matriz: o passo Base fica pendente mesmo em fase 2.
    """
    passos = dict(r["passos"])
    pend = [p.replace(" LP ", f" {r['comp']} ") for p in r["pend"]]
    if r["matriz"] and pend == ["Sem matriz"]:
        pend = [_SEM_MATRIZ_ALT]
    if not r["matriz"]:
        passos["base"] = "pend"
        if "Sem matriz" not in pend:
            pend.insert(0, "Sem matriz")
    return passos, pend


_CURTO = {
    "Falta escolher o template do F2": "Falta template F2",
    "Infográfico Alfa sem habilidade": "Alfa sem habilidade",
    "3 seções sem texto": "3 textos vazios",
    "4 de 24 variáveis vazias": "4 variáveis vazias",
}


def curto(p):
    p = re.sub(r"^Cortes de (\w+) \w+ faltando$", r"Cortes \1 faltando", p)
    return _CURTO.get(p, p)


def primeiro(nome):
    return nome.split()[0]


def data_curta(quando):
    return quando.split(" ")[0]


def ordenadas():
    return sorted(D.REVISTAS, key=lambda r: (r["nome_parceiro"], r["comp"]))


def _tipo(r):
    return D.PARCEIRO_POR_ID[r["parceiro"]]["tipo"]


def _attrs(r, pend):
    busca = " ".join([r["nome_parceiro"], r["comp"], D.COMP_NOME[r["comp"]], _tipo(r), D.FASE_NOME[r["fase"]], *pend, r["editando"] or ""])
    return (
        f'data-busca="{S.esc(busca)}" data-comp="{r["comp"]}" data-tipo="{S.esc(_tipo(r))}" data-fase="{r["fase"]}" '
        f'data-parceiro="{r["parceiro"]}" data-parceiro-nome="{S.esc(r["nome_parceiro"])}"'
    )


# ── Vista Esteira ─────────────────────────────────────────────────────────
def _cartao(r):
    passos, pend = estado(r)
    f = r["fase"]
    n_ok = sum(1 for k, _, _ in D.PASSOS if passos[k] == "ok")
    chips = [S.tag(curto(p), "alerta") for p in pend]
    if f == 3:
        chips.append(S.tag("Pronta para validar", "ok", "confirmado"))
    if f == 4:
        chips.append(S.tag("Impresso a atualizar", "cobalto"))
    if f == 5:
        chips.append(S.tag("Impresso em dia", "ok"))
    if r["editando"]:
        chips.append(S.tag(f"{primeiro(r['editando'])} editando", "alerta", "cadeado"))
    val = ""
    if r["validada"]:
        quem, quando = r["validada"]
        val = f'<span class="mudo cr-val">Validada por {S.esc(quem)} · {S.esc(data_curta(quando))}</span>'
    return (
        f'<a class="cartao-rev" href="{S.href_revista(r["id"])}" {_attrs(r, pend)}>'
        f'<span class="linha cr-topo"><b>{S.esc(r["nome_parceiro"])}</b>{S.tag(r["comp"])}</span>'
        f'<span class="linha cr-prog">{S.regua_mini(f)}<span class="mudo">{n_ok} de 6 passos prontos</span></span>'
        f'<span class="linha cr-chips">{"".join(chips)}</span>{val}</a>'
    )


def _coluna(n, nome, sub, rs):
    cartoes = "".join(_cartao(r) for r in rs)
    return (
        f'<section class="col-fase" data-col="{n}" aria-label="Fase {n}: {S.esc(nome)}">'
        f'<div class="col-cab"><span class="sw" data-f="{n}"></span><h2>{S.esc(nome)}</h2><span class="n" data-col-n>{len(rs)}</span></div>'
        f'<p class="col-sub">{S.esc(sub)}</p>{cartoes}'
        f'<p class="col-nada" hidden>Nenhuma revista nesta fase com os filtros atuais.</p></section>'
    )


# ── Vista Tabela ──────────────────────────────────────────────────────────
def _st_derivado(ok, pend_se, titulo_na):
    if ok:
        return S.st("ok")
    return S.st("pend") if pend_se else S.st("na", titulo_na)


def _json_espia(r, passos, pend):
    d = {
        "id": r["id"],
        "nome": S.nome_revista(r),
        "href": S.href_revista(r["id"]),
        "fase": r["fase"],
        "faseNome": D.FASE_NOME[r["fase"]],
        "passos": [{"id": k, "nome": n, "ok": passos[k] == "ok"} for k, n, _ in D.PASSOS],
        "pend": [curto(p) for p in pend],
        "editando": r["editando"] or "",
        "validada": (f"{r['validada'][0]} em {data_curta(r['validada'][1])}" if r["validada"] else ""),
    }
    return json.dumps(d, ensure_ascii=False)


def _linha(r):
    passos, pend = estado(r)
    f = r["fase"]
    nome = S.nome_revista(r)
    ed = S.tag(f"{primeiro(r['editando'])}", "alerta", "cadeado") if r["editando"] else '<span class="mudo">&mdash;</span>'
    cels = [
        f'<input type="checkbox" data-sel aria-label="Selecionar {S.esc(nome)}">',
        f'<a class="nome" href="{S.href_revista(r["id"])}">{S.esc(nome)}</a>',
        S.regua(f),
        S.st(passos["base"]),
        S.st(passos["templates"]),
        S.st(passos["infograficos"]),
        S.st(passos["capa"]),
        S.st(passos["textos"]),
        _st_derivado(f >= 4, f == 3, "Depois de montar e conferir"),
        _st_derivado(f == 5, f == 4, "Depois de validar"),
        ed,
        S.btn_ic("olho", f"Espiar {nome}", attrs='data-abrir="g-espia" data-espiar')
        + S.btn_ic("seta", f"Abrir {nome}", href=S.href_revista(r["id"])),
    ]
    attrs = f"{_attrs(r, pend)} data-espia=\"{S.esc(_json_espia(r, passos, pend))}\""
    return (attrs, cels)


_CAB = [
    '<input type="checkbox" data-sel-todos="#tab-rev" aria-label="Marcar todas as revistas visíveis">',
    "Revista",
    "Fase",
    ("Base", "ctr"),
    ("Templates", "ctr"),
    ("Infográficos", "ctr"),
    ("Capa", "ctr"),
    ("Textos", "ctr"),
    ("Validado", "ctr"),
    ("Impresso", "ctr"),
    "Em edição",
    ("", "acoes"),
]


def _dialogos():
    aviso_val = (
        '<div data-aviso-val hidden>'
        + S.aviso(
            '<span data-aviso-val-txt>2 das selecionadas estão Validadas: perdem o Validado e voltam para Conferir.</span>',
            "alerta",
        )
        + "</div>"
    )
    matriz = S.dialogo(
        "dlg-matriz",
        "Atribuir matriz",
        '<p class="mudo">A matriz define descritores e cortes. Vale para todas as revistas selecionadas.</p>'
        + S.selecao("Matriz", "matriz", [(m["id"], m["nome"]) for m in D.MATRIZES], attrs="data-edita")
        + aviso_val,
        S.btn("Cancelar", tom="fan", attrs="data-fechar")
        + S.btn("Atribuir matriz", tom="prim", attrs='data-edita data-fechar data-salva data-toast="Matriz atribuída às revistas selecionadas."'),
    )
    f1 = [("", "Manter o atual")] + [(t["id"], t["nome"]) for t in D.TEMPLATES if t["fasc"] == "F1"]
    f2 = [("", "Manter o atual")] + [(t["id"], t["nome"]) for t in D.TEMPLATES if t["fasc"] == "F2"]
    templ = S.dialogo(
        "dlg-template",
        "Atribuir template",
        '<p class="mudo">Escolha o template do F1, do F2 ou dos dois. O que ficar em &ldquo;Manter o atual&rdquo; não muda.</p>'
        + '<div class="campos">'
        + S.selecao("Template do F1", "tf1", f1, attrs="data-edita")
        + S.selecao("Template do F2", "tf2", f2, attrs="data-edita")
        + "</div>"
        + aviso_val,
        S.btn("Cancelar", tom="fan", attrs="data-fechar")
        + S.btn("Atribuir template", tom="prim", attrs='data-edita data-fechar data-salva data-toast="Template atribuído às revistas selecionadas."'),
    )
    return matriz + templ


def _gaveta():
    corpo = '<div id="esp-corpo"></div>'
    rodape = (
        '<a class="btn" id="esp-preview" href="#">' + S.ic("olho") + "Preview</a>"
        '<a class="btn btn-prim" id="esp-abrir" href="#">Abrir revista' + S.ic("seta") + "</a>"
    )
    return S.gaveta("g-espia", "Espiar revista", corpo, rodape)


def corpo():
    rs = ordenadas()
    n = len(rs)
    colunas = "".join(_coluna(f, nome, sub, [r for r in rs if r["fase"] == f]) for f, _, nome, sub in D.FASES)
    tabela = S.tabela(_CAB, [_linha(r) for r in rs], id_="tab-rev")
    filtros = (
        '<div class="rl-filtros" role="search">'
        f'<label class="rl-busca">{S.ic("busca")}<input class="input" type="search" data-filtro="#lista-rev" placeholder="Buscar parceiro ou pendência" aria-label="Buscar revista"></label>'
        '<select class="select" data-alvo="#lista-rev" data-filtra="comp" aria-label="Componente"><option value="">Componente</option>'
        + "".join(f'<option value="{k}">{S.esc(v)}</option>' for k, v in D.COMPONENTES)
        + "</select>"
        '<select class="select" data-alvo="#lista-rev" data-filtra="tipo" aria-label="Tipo de parceiro"><option value="">Tipo de parceiro</option>'
        '<option value="Estado">Estado</option><option value="Município">Município</option></select>'
        '<select class="select" data-alvo="#lista-rev" data-filtra="fase" aria-label="Fase"><option value="">Fase</option>'
        + "".join(f'<option value="{f}">{S.esc(nome)}</option>' for f, _, nome, _ in D.FASES)
        + "</select>"
        f'<button type="button" class="btn btn-fan btn-sm" data-limpar-filtros hidden>{S.ic("x")}Limpar filtros</button>'
        f'<span class="rl-cont" aria-live="polite"><b data-contagem="#lista-rev">{n}</b> de {n}</span>'
        "</div>"
    )
    barra = (
        '<div class="sel-barra" role="region" aria-label="Revistas selecionadas">'
        '<span class="contagem"><span data-sel-n>0</span> <span data-sel-plural>selecionadas</span></span>'
        + S.btn("Conferir e validar", "entrega-validar.html", "prim", "confirmado")
        + S.btn("Atribuir matriz…", tom="sec", attrs='data-abrir="dlg-matriz" data-edita')
        + S.btn("Atribuir template…", tom="sec", attrs='data-abrir="dlg-template" data-edita')
        + S.btn("Limpar", tom="fan", attrs="data-sel-limpar")
        + "</div>"
    )
    leitura = (
        '<div data-p="imp" class="rl-aviso">'
        + S.aviso(
            "Você vê todas as revistas, mas não altera nada nesta tela. Para atribuir matriz ou template, peça à equipe Pedagógica ou de Mídias Digitais.",
            "leitura",
        )
        + "</div>"
    )
    lista = (
        '<div id="lista-rev">'
        + S.abas_js([("esteira", "Esteira", None), ("tabela", "Tabela", None)])
        + filtros
        + '<div class="rev-paineis">'
        f'<section data-painel="esteira" aria-label="Esteira de fases"><div class="esteira">{colunas}</div></section>'
        f'<section data-painel="tabela" aria-label="Tabela de revistas">{tabela}</section>'
        "</div>"
        '<div id="rev-vazio" hidden>'
        + S.vazio(
            "Nenhuma revista com esses filtros",
            f"Tire um filtro ou procure por outro nome. A temporada tem {n} revistas.",
            S.btn("Limpar filtros", tom="sec", attrs="data-limpar-filtros"),
        )
        + "</div></div>"
    )
    acoes = S.btn("Fila de validação", "entrega-validar.html", "sec", "confirmado", attrs='data-p="ped mid adm"')
    return (
        S.cab("Revistas", f"{n} revistas de {D.ANO}, da matriz ao impresso.", acoes)
        + leitura
        + lista
        + barra
        + _dialogos()
        + _gaveta()
    )


def paginas():
    return [S.Pagina("revistas.html", "Revistas", "revistas", corpo(), trilha=[("Revistas", None)], largura="larga")]


CSS = """
/* ── Revistas: filtros, esteira, tabela, gaveta ─────────────────────── */
.rl-aviso{margin-bottom:14px}
.rl-filtros{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:14px}
.rl-busca{position:relative;flex:1 1 240px;max-width:340px;display:block}
.rl-busca .ic{position:absolute;left:10px;top:8px;color:var(--txt-2);pointer-events:none}
.rl-busca .input{padding-left:34px}
.rl-filtros .select{width:auto;min-width:150px}
.rl-cont{margin-left:auto;color:var(--txt-2);white-space:nowrap}
.rl-cont b{color:var(--txt)}
#lista-rev > .abas{margin-bottom:14px}
#lista-rev.sem-resultado .rev-paineis{display:none}
.esteira{grid-template-columns:repeat(5,minmax(205px,1fr));scroll-snap-type:x proximity}
.col-fase{scroll-snap-align:start}
.col-cab h2{font-size:14px}
.col-cab .sw[data-f]{display:block;flex:none}
.col-nada{padding:14px 8px;text-align:center;color:var(--txt-2);font-size:12px}
.cartao-rev .cr-topo{justify-content:space-between}
.cartao-rev .cr-topo b{font-size:14px}
.cartao-rev .cr-prog{font-size:12px}
.cartao-rev .cr-chips:empty{display:none}
.cartao-rev .cr-chips{gap:4px}
.cartao-rev .tag{height:20px;font-size:11.5px;padding:0 7px}
.cartao-rev .cr-val{font-size:12px}
#tab-rev td:nth-child(n+4):nth-child(-n+10){text-align:center}
#tab-rev th:first-child,#tab-rev td:first-child{width:38px;padding-right:0}
#tab-rev input[type=checkbox],.rl-filtros input[type=checkbox]{width:16px;height:16px;cursor:pointer}
#tab-rev td:nth-child(2){min-width:190px}
#tab-rev td:nth-child(3){min-width:150px}
#tab-rev tbody tr:has([data-sel]:checked) td{background:var(--cobalto-fundo)}
.gaveta:not([open]){display:none}
.esp-fase{display:flex;align-items:center;gap:10px;font-weight:600}
.esp-sec{display:grid;gap:6px}
.esp-sec h3{font-size:13px;color:var(--txt-2)}
.esp-chips{display:flex;gap:6px;flex-wrap:wrap}
.esp-sec .checklist li{padding:5px 0}
@media (max-width:960px){
  .rl-busca{max-width:none;flex-basis:100%}
  .rl-filtros .select{flex:1 1 140px}
  .rl-cont{margin-left:0;flex-basis:100%}
  .esteira{grid-template-columns:repeat(5,minmax(260px,82vw))}
}
"""

JS = r"""
(() => {
  const lista = document.querySelector("#lista-rev");
  if (!lista) return;
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const dispara = (el, tipo) => el.dispatchEvent(new Event(tipo, { bubbles: true }));
  const ico = (n) => `<svg class="ic" aria-hidden="true" focusable="false"><use href="#i-${n}"/></svg>`;
  const busca = $('input[data-filtro="#lista-rev"]');
  const selects = $$('select[data-alvo="#lista-rev"]');
  const total = $$(".cartao-rev", lista).length;

  /* resultado do filtro: contagem só das revistas (cartões), vazio, colunas sem cartão */
  const atualiza = () => {
    const n = $$(".cartao-rev:not([hidden])", lista).length;
    $$('[data-contagem="#lista-rev"]').forEach((e) => (e.textContent = n));
    lista.classList.toggle("sem-resultado", n === 0);
    $("#rev-vazio").hidden = n > 0;
    $$(".col-fase", lista).forEach((c) => { $(".col-nada", c).hidden = !!$(".cartao-rev:not([hidden])", c); });
    const filtrando = !!busca.value || selects.some((s) => s.value);
    $$("[data-limpar-filtros]").forEach((b) => { if (b.closest(".rl-filtros")) b.hidden = !filtrando; });
  };
  document.addEventListener("input", (e) => { if (e.target === busca) atualiza(); });
  document.addEventListener("change", (e) => { if (selects.includes(e.target)) atualiza(); });
  document.addEventListener("click", (e) => {
    if (!e.target.closest("[data-limpar-filtros]")) return;
    busca.value = ""; selects.forEach((s) => (s.value = ""));
    dispara(busca, "input"); atualiza();
  });

  /* ?fase=3 e ?parceiro=<id> pré-selecionam os filtros; #tabela já é tratado pelas abas */
  const qs = new URLSearchParams(location.search);
  const fase = qs.get("fase");
  if (fase) { const s = $('select[data-filtra="fase"]'); if (s) { s.value = fase; dispara(s, "change"); } }
  const par = qs.get("parceiro");
  if (par) {
    const c = $(`.cartao-rev[data-parceiro="${CSS.escape(par)}"]`, lista);
    if (c) { busca.value = c.dataset.parceiroNome; dispara(busca, "input"); }
  }
  atualiza();

  /* a barra de seleção só vale na tabela: ao trocar de vista, recalcula */
  $$("[data-aba]", lista).forEach((b) => b.addEventListener("click", () => {
    const c = $("[data-sel]"); if (c) setTimeout(() => dispara(c, "change"), 0);
  }));

  /* aviso de impacto dos diálogos em massa */
  document.addEventListener("click", (e) => {
    if (!e.target.closest('[data-abrir="dlg-matriz"],[data-abrir="dlg-template"]')) return;
    const marcadas = $$("#tab-rev [data-sel]:checked").map((c) => c.closest("tr"));
    const val = marcadas.filter((tr) => Number(tr.dataset.fase) >= 4).length;
    $$("[data-aviso-val]").forEach((d) => {
      d.hidden = val === 0;
      $("[data-aviso-val-txt]", d).textContent = val === 1
        ? "1 das selecionadas está Validada: perde o Validado e volta para Conferir."
        : `${val} das selecionadas estão Validadas: perdem o Validado e voltam para Conferir.`;
    });
  });

  /* gaveta Espiar */
  document.addEventListener("click", (e) => {
    const b = e.target.closest("[data-espiar]");
    if (!b) return;
    const d = JSON.parse(b.closest("tr").dataset.espia);
    $("#g-espia-t").textContent = d.nome;
    const regua = `<span class="regua" data-f="${d.fase}" role="img" aria-label="Fase ${d.fase} de 5">${"<i></i>".repeat(5)}</span>`;
    const passos = d.passos.map((p) =>
      `<li><span class="st st-${p.ok ? "ok" : "pend"}" role="img" aria-label="${p.ok ? "Pronto" : "Pendente"}">${ico(p.ok ? "ok" : "aberto")}</span>` +
      `<a class="txt" href="${d.href}#${p.id}">${esc(p.nome)}</a><small>${p.ok ? "Pronto" : "Pendente"}</small></li>`).join("");
    const pend = d.pend.length
      ? `<div class="esp-chips">${d.pend.map((t) => `<span class="tag tag-alerta">${esc(t)}</span>`).join("")}</div>`
      : `<p class="mudo">Nenhuma pendência.</p>`;
    const nota = d.editando ? `<p class="aviso aviso-alerta" style="display:flex;gap:8px">${ico("cadeado")}<span>${esc(d.editando)} está editando. Você abre em somente leitura.</span></p>` : "";
    const val = d.validada ? `<p class="mudo">Validada por ${esc(d.validada)}.</p>` : "";
    $("#esp-corpo").innerHTML =
      `<div class="esp-fase">${regua}<span>${esc(d.faseNome)}</span></div>${nota}${val}` +
      `<div class="esp-sec"><h3>Passos</h3><ul class="checklist">${passos}</ul></div>` +
      `<div class="esp-sec"><h3>Pendências</h3>${pend}</div>`;
    $("#esp-abrir").setAttribute("href", d.href);
    $("#esp-preview").setAttribute("href", d.href + "#conferir");
  });
})();
"""
