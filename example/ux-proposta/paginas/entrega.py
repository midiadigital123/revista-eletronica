"""Entrega: Validar + Impresso + Pacotes numa seção só (demo de UI/UX, dados fictícios)."""
import html

import dados as D
from paginas import shell as S

esc = S.esc

CSS = """
/* ── Entrega ───────────────────────────────────────────────────────── */
.en-fila{display:grid;gap:12px;align-content:start}
.en-grupo{background:var(--papel);border:1px solid var(--fio);border-radius:var(--raio-g);overflow:hidden}
.en-grupo > h2,.en-grupo > summary{display:flex;align-items:center;gap:8px;padding:10px 12px;font-size:13px;font-weight:650;background:var(--tela);border-bottom:1px solid var(--fio);list-style:none;margin:0}
.en-grupo > summary{cursor:pointer}
.en-grupo > summary::-webkit-details-marker{display:none}
.en-grupo:not([open]) > summary{border-bottom:0}
.en-grupo > summary .ic:last-child{margin-left:auto;transition:transform .15s var(--ease)}
.en-grupo[open] > summary .ic:last-child{transform:rotate(180deg)}
.en-grupo .mudo{font-weight:500}
.en-item{display:flex;align-items:center;gap:10px;padding:10px 12px;border-bottom:1px solid var(--fio);min-width:0}
.en-item:last-child{border-bottom:0}
.en-item > input[type=checkbox]{width:16px;height:16px;flex:none;margin:0}
.en-nome,.en-txt{flex:1;min-width:0;display:grid;gap:4px;color:var(--txt);text-decoration:none}
.en-saida{color:inherit;text-decoration:none}
.en-saida:hover{background:var(--tela)}
.en-saida:hover .nm{color:var(--cobalto)}
.en-nome .nm,.en-txt .nm{font-weight:600;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.en-nome:hover .nm{color:var(--cobalto);text-decoration:underline}
.en-meta{display:flex;align-items:center;gap:8px;flex-wrap:wrap;font-size:12px;color:var(--txt-2)}
.en-item[aria-current="true"]{background:var(--cobalto-fundo)}
.en-item.feito .nm{text-decoration:line-through;text-decoration-color:var(--fio-2);color:var(--txt-2);font-weight:500}
.en-item.feito > input{visibility:hidden}
.en-item .en-ok{display:none}
.en-item.feito .en-ok{display:inline-grid}
.en-causa{font-size:12px;color:var(--alerta);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.en-painel{display:grid;gap:20px;padding:20px 22px}
.en-ph{display:flex;gap:12px;align-items:flex-start;justify-content:space-between;flex-wrap:wrap}
.en-ph h2{font-size:18px;letter-spacing:-.015em}
.en-ph p{margin-top:2px}
.en-sec{display:grid;gap:10px}
.en-sec > h3{font-size:14px}
.en-mud{display:grid;gap:8px}
.en-mud + .en-mud{padding-top:14px;border-top:1px solid var(--fio)}
.en-mud-cab{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.en-mud-cab .btn{margin-left:auto}
.en-diff-vazio{color:var(--txt-2);font-style:normal}
.en-barra{position:fixed;left:var(--rail);right:0;bottom:0;z-index:40;background:var(--papel);border-top:1px solid var(--fio-2);box-shadow:0 -6px 20px oklch(0.2 0.03 263 / .07)}
.en-barra-in{max-width:1240px;margin:0 auto;padding:12px 28px;display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.en-barra .linha{gap:8px}
.en-barra-txt{color:var(--txt-2);margin-left:auto;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.en-barra-txt b{color:var(--txt)}
.en-topo-det{position:sticky;top:60px;z-index:5;display:flex;gap:12px;align-items:center;justify-content:space-between;flex-wrap:wrap;
  background:var(--papel);border:1px solid var(--fio);border-radius:var(--raio-g);padding:12px 16px;box-shadow:var(--sombra-p)}
.en-topo-det h2{font-size:17px}
.en-topo-det .en-sub{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:4px;font-size:13px;color:var(--txt-2)}
.en-det{display:grid;gap:12px}
.en-fasc{display:grid;gap:12px}
.en-fasc > header{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.en-fasc > header h3{font-size:15px}
.en-fasc > header .linha{margin-left:auto;gap:6px}
.en-fasc + .en-fasc{padding-top:18px;border-top:1px solid var(--fio)}
.en-quebra{display:block;white-space:normal;min-width:260px;max-width:520px}
.en-novo{background:var(--tela);border-radius:10px;padding:12px;font-size:13px;line-height:1.6}
.en-novo h4{margin:0 0 6px;font-size:12px;color:var(--txt-2);font-weight:600}
.en-filtros{display:grid;gap:10px;padding:12px;border-bottom:1px solid var(--fio)}
.en-lista-vazia{padding:18px 12px;color:var(--txt-2);font-size:13px}
@media (min-width: 961px){
  .en-fila{position:sticky;top:64px;max-height:calc(100vh - 150px);overflow:auto}
}
@media (max-width: 960px){
  .en-barra{left:0}
  .en-barra-in{padding:10px 16px}
  .en-barra-txt{display:none}
  .en-topo-det{position:static}
}
"""

JS = """
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const plural = (n, um, varios) => n + " " + (n === 1 ? um : varios);
  /* troca o hash sem o navegador rolar até o painel */
  const marca = (rid) => { const y = window.scrollY; try { history.replaceState(null, "", "#" + rid); } catch (e) {} const volta = () => window.scrollTo(0, y); volta(); requestAnimationFrame(volta); setTimeout(volta, 60); };
  const sobe = () => { if (location.hash) window.addEventListener("load", () => setTimeout(() => window.scrollTo(0, 0), 0)); };
  const celular = () => window.matchMedia("(max-width: 960px)").matches;

  /* ── Entrega › Validar ─────────────────────────────────────────── */
  const val = $("[data-validar]");
  if (val) {
    const itens = $$(".en-item[data-rid]", val);
    const paineis = $$("[data-rev]", val);
    const barra = $(".en-barra");
    const feito = (i) => i.classList.contains("feito");
    const pendentes = () => itens.filter((i) => !feito(i));
    const nome = (i) => $(".nm", i).textContent;
    let atual = null;

    function contagens() {
      const n = pendentes().length;
      $$("[data-n-fila]", val).forEach((e) => (e.textContent = n));
      const aba = $('.abas a[aria-current="page"] .n');
      if (aba) aba.textContent = n;
      const m = $$("[data-marca]:checked", val).filter((c) => !feito(c.closest(".en-item"))).length;
      $$("[data-n-marcadas]").forEach((e) => (e.textContent = m));
    }
    function mostra(rid, url) {
      const item = itens.find((i) => i.dataset.rid === rid);
      if (!item) return;
      atual = item;
      const bt = $("[data-validar-prox]");
      if (bt && !document.body.classList.contains("so-leitura")) {
        bt.disabled = item.dataset.bloq === "1";
        bt.title = bt.disabled ? "Outra pessoa está editando esta revista; valide quando ela terminar" : "";
      }
      itens.forEach((i) => i.setAttribute("aria-current", String(i === item)));
      paineis.forEach((p) => (p.hidden = p.dataset.rev !== rid));
      $$("[data-atual]").forEach((e) => (e.textContent = nome(item)));
      if (barra) barra.hidden = false;
      if (url) {
        marca(rid);
        if (celular()) $(`[data-rev="${rid}"]`, val).scrollIntoView({ block: "start" });
      }
    }
    function fim() {
      atual = null;
      paineis.forEach((p) => (p.hidden = p.dataset.rev !== "fim"));
      itens.forEach((i) => i.setAttribute("aria-current", "false"));
      if (barra) barra.hidden = true;
    }
    function proxima() {
      const p = pendentes();
      if (!p.length) return null;
      const k = atual ? itens.indexOf(atual) : -1;
      return p.find((i) => itens.indexOf(i) > k) || p[0];
    }
    function valida(item) {
      item.classList.add("feito");
      const c = $("[data-marca]", item); c.checked = false; c.disabled = true;
      $(".en-estado", item).innerHTML = '<span class="tag tag-ok">Validada</span>';
      const r = $(".regua", item);
      r.dataset.f = "4"; r.setAttribute("aria-label", "Fase 4 de 5: Validada");
    }
    const vai = (i) => (i ? mostra(i.dataset.rid, true) : fim());

    val.addEventListener("click", (e) => {
      const a = e.target.closest(".en-nome");
      if (a) { e.preventDefault(); mostra(a.closest(".en-item").dataset.rid, true); }
    });
    document.addEventListener("click", (e) => {
      if (e.target.closest("[data-validar-prox]") && atual) {
        const v = atual; valida(v);
        const prox = proxima();
        window.toast(nome(v) + " validada");
        vai(prox); contagens();
      } else if (e.target.closest("[data-validar-marcadas]")) {
        const alvo = pendentes().filter((i) => $("[data-marca]", i).checked);
        if (!alvo.length) { window.toast("Marque ao menos uma revista na fila"); return; }
        $("[data-lote-lista]").innerHTML = alvo.map((i) => '<li><span class="txt">' + nome(i) + "</span></li>").join("");
        $("[data-lote-n]").textContent = plural(alvo.length, "revista marcada", "revistas marcadas");
        $("#dlg-lote").showModal();
      } else if (e.target.closest("[data-lote-ok]")) {
        const alvo = pendentes().filter((i) => $("[data-marca]", i).checked);
        alvo.forEach(valida);
        $("#dlg-lote").close();
        window.toast(plural(alvo.length, "revista validada", "revistas validadas"));
        if (atual && feito(atual)) vai(proxima());
        contagens();
      } else if (e.target.closest("[data-pular]")) {
        const prox = proxima();
        if (prox && prox !== atual) vai(prox);
        else window.toast("Não há outra revista pendente na fila");
      }
    });
    val.addEventListener("change", (e) => { if (e.target.matches("[data-marca]")) contagens(); });
    const inicial = () => { const h = location.hash.slice(1); return itens.find((i) => i.dataset.rid === h && !feito(i)) || pendentes()[0]; };
    window.addEventListener("hashchange", () => { const i = inicial(); if (i && location.hash.slice(1) === i.dataset.rid) mostra(i.dataset.rid, false); });
    const ini = inicial();
    if (ini) mostra(ini.dataset.rid, false);
    if (!celular()) sobe();
    contagens();
  }

  /* ── Entrega › Impresso ────────────────────────────────────────── */
  const imp = $("[data-impresso]");
  if (imp) {
    const itens = $$(".en-item[data-rid]", imp);
    const paineis = $$("[data-rev]", imp);
    const filtro = $("select[data-alvo='#fila-imp']");
    const ROT = { "": "Todas", atualizar: "Para atualizar", aguardando: "Aguardando Validado", dia: "Em dia" };
    const SIT = {
      atualizar: '<span class="tag tag-cobalto">Para atualizar</span>',
      aguardando: '<span class="tag tag-alerta">Aguardando Validado</span>',
      dia: '<span class="tag tag-ok">Em dia</span>',
    };
    let atual = null;
    const refiltra = () => filtro && filtro.dispatchEvent(new Event("change", { bubbles: true }));
    function recontar() {
      if (filtro) $$("option", filtro).forEach((o) => {
        const n = o.value ? itens.filter((i) => i.dataset.sit === o.value).length : itens.length;
        o.textContent = ROT[o.value] + " (" + n + ")";
      });
      const aba = $('.abas a[aria-current="page"] .n');
      if (aba) aba.textContent = itens.filter((i) => i.dataset.sit === "atualizar").length;
    }
    function mostra(rid, url) {
      const item = itens.find((i) => i.dataset.rid === rid);
      if (!item) return;
      atual = item;
      if (item.hidden && filtro) { filtro.value = item.dataset.sit; refiltra(); }
      itens.forEach((i) => i.setAttribute("aria-current", String(i === item)));
      paineis.forEach((p) => (p.hidden = p.dataset.rev !== rid));
      if (url) {
        marca(rid);
        if (window.matchMedia("(max-width: 960px)").matches) $(`[data-rev="${rid}"]`, imp).scrollIntoView({ block: "start" });
      }
    }
    imp.addEventListener("click", (e) => {
      const a = e.target.closest(".en-nome");
      if (a) { e.preventDefault(); mostra(a.closest(".en-item").dataset.rid, true); }
    });
    document.addEventListener("click", (e) => {
      const b = e.target.closest("[data-marcar]");
      if (!b || b.disabled) return;
      const p = b.closest("[data-rev]"), item = itens.find((i) => i.dataset.rid === p.dataset.rev);
      item.dataset.sit = "dia";
      $(".en-sit", item).innerHTML = SIT.dia;
      $$("[data-sit-tag]", p).forEach((t) => (t.innerHTML = SIT.dia));
      $$("[data-marcar], [data-leitura-imp]", p).forEach((t) => (t.hidden = true));
      const ok = $("[data-feito-msg]", p); if (ok) ok.hidden = false;
      window.toast($(".nm", item).textContent + " marcada como impressa");
      recontar(); refiltra();
      const prox = itens.find((i) => i.dataset.sit === "atualizar");
      if (prox) mostra(prox.dataset.rid, false);
    });
    const h = location.hash.slice(1);
    const ini = itens.find((i) => i.dataset.rid === h) || itens.find((i) => i.dataset.sit === "atualizar") || itens[0];
    if (filtro) { filtro.value = ini.dataset.sit; refiltra(); }
    mostra(ini.dataset.rid, false);
    if (!celular()) sobe();
    window.addEventListener("hashchange", () => { if (itens.some((i) => i.dataset.rid === location.hash.slice(1))) mostra(location.hash.slice(1), false); });
    recontar();
  }
})();
"""

PRIMEIRA_VALIDAR = {"vale-verde-lp", "campo-largo-lp", "foz-do-lago-mt"}
PRIMEIRA_IMPRESSO = {"monte-sereno-lp", "tres-cruzes-mt"}
ULTIMA = {
    "serra-alta-lp": "06/11",
    "serra-alta-mt": "06/11",
    "planalto-central-lp": "07/11",
    "planalto-central-mt": "07/11",
    "tres-cruzes-lp": "09/11",
    "porto-alvo-lp": "09/11",
}


# ── Mudanças em linguagem humana (dados fictícios, deterministas) ─────────
def _pool_f1(r):
    p, c = r["nome_parceiro"], r["comp"]
    d, dtxt = ("D04", "Inferir uma informação implícita em um texto.") if c == "LP" else ("D12", "Resolver problema que envolva porcentagem.")
    base, extra = dtxt[:-1], (" verbal ou multissemiótico" if c == "LP" else " ou juros simples")
    return [
        dict(kind="alterado", escopo="Introdução", desc="texto alterado",
             antes=f"Esta revista apresenta os resultados do <del>programa de avaliação</del> para a rede de {esc(p)}.",
             depois=f"Esta revista apresenta os resultados do <ins>Avalia {esc(p)}</ins> para a rede de {esc(p)}.",
             novo=f"Esta revista apresenta os resultados do Avalia {p} para a rede de {p}."),
        dict(kind="alterado", escopo=f"5EF {c}", desc="corte 2 passou de 195 para 200",
             antes="Cortes: 150 · <del>195</del> · 250", depois="Cortes: 150 · <ins>200</ins> · 250", novo="150 · 200 · 250"),
        dict(kind="alterado", escopo=f"9EF {c} · {d}", desc="descrição ajustada",
             antes=esc(base) + ".", depois=esc(base) + "<ins>" + esc(extra) + "</ins>.", novo=base + extra + "."),
        dict(kind="novo", escopo=f"3EM {c} · D13", desc="descritor novo",
             antes=None, depois="<ins>Interpretar gráfico de colunas com duas ou mais séries.</ins>", novo="Interpretar gráfico de colunas com duas ou mais séries."),
        dict(kind="removido", escopo="Fechamento", desc="parágrafo removido",
             antes="<del>Em 2025, a Secretaria definiu metas de recomposição por escola.</del>", depois=None, novo=None),
        dict(kind="alterado", escopo=f"2EF {c}", desc="corte 1 passou de 450 para 475",
             antes="Cortes: <del>450</del> · 500 · 550", depois="Cortes: <ins>475</ins> · 500 · 550", novo="475 · 500 · 550"),
    ]


def _pool_f2(r):
    p = r["nome_parceiro"]
    return [
        dict(kind="alterado", escopo="Passo 2 · Referencial por etapa", desc="texto alterado",
             antes="Veja como a habilidade evolui do <del>2º ano</del> ao 3º ano do Ensino Médio.",
             depois="Veja como a habilidade evolui do <ins>2º ano do Ensino Fundamental</ins> ao 3º ano do Ensino Médio.",
             novo="Veja como a habilidade evolui do 2º ano do Ensino Fundamental ao 3º ano do Ensino Médio."),
        dict(kind="novo", escopo="Infográfico Alfa", desc="habilidade preenchida",
             antes=None, depois="<ins>Reconhecer o efeito de sentido decorrente da pontuação (D08)</ins>",
             novo="Reconhecer o efeito de sentido decorrente da pontuação (D08)"),
        dict(kind="alterado", escopo="Abertura", desc="título alterado",
             antes="<del>Avaliação e Currículo</del>", depois=f"<ins>Avaliação e currículo em {esc(p)}</ins>", novo=f"Avaliação e currículo em {p}"),
        dict(kind="removido", escopo="Diálogo do descritor", desc="nota removida",
             antes="<del>Fonte: matriz 2025.</del>", depois=None, novo=None),
    ]


def mudancas(r):
    i = D.REVISTAS.index(r)
    p1, p2 = _pool_f1(r), _pool_f2(r)
    n1 = 2 + (i % 3 == 0)
    n2 = 1 + (i % 2)
    return {"F1": [p1[(i + k) % len(p1)] for k in range(n1)], "F2": [p2[(i + k) % len(p2)] for k in range(n2)]}


_TAG = {"novo": ("Novo", "ok"), "alterado": ("Alterado", "cobalto"), "removido": ("Removido", "erro")}


def _diff(m, ant="No último impresso", dep="Agora"):
    a = m["antes"] or '<span class="en-diff-vazio">Não existia.</span>'
    d = m["depois"] or '<span class="en-diff-vazio">Foi removido.</span>'
    return f'<div class="diff"><div><h4>{ant}</h4><p>{a}</p></div><div><h4>{dep}</h4><p>{d}</p></div></div>'


def _mud(m, prefixo="", copiar=False):
    rot, tom = _TAG[m["kind"]]
    cp = ""
    if copiar and m["novo"]:
        cp = S.btn("Copiar texto novo", tom="fan", icone="copiar", cls="btn-sm", attrs=f'data-copiar="{esc(m["novo"])}"')
    return (
        f'<div class="en-mud"><div class="en-mud-cab">{S.tag(rot, tom)}<b>{esc(prefixo)}{esc(m["escopo"])}</b>'
        f'<span class="mudo">· {esc(m["desc"])}</span>{cp}</div>{_diff(m)}</div>'
    )


def _t(msg):
    return f'data-toast="{esc(msg)}"'


def _abas(atual):
    n3 = len(D.revistas_na_fase(3))
    n4 = len(D.revistas_na_fase(4))
    nval = n4 + len(D.revistas_na_fase(5))
    return S.abas_links(
        [("Validar", "entrega-validar.html", n3), ("Impresso", "entrega-impresso.html", n4), ("Pacotes", "entrega-pacotes.html", nval)],
        atual,
    )


def _topo(rotulo):
    return [("Entrega", "entrega-validar.html"), (rotulo, None)]


# ── Validar ───────────────────────────────────────────────────────────────
_DESATUALIZADAS = [
    None,
    ("Introdução", "o texto foi escrito sobre o template v3; o LP · F1 está na v4"),
    ("Introdução e Fechamento", "os textos usam variáveis que mudaram de valor desde o último salvamento"),
    ("Passo 3", "o texto não acompanhou a troca do infográfico Alfa"),
]


def _painel_validar(r):
    rid = r["id"]
    i = D.REVISTAS.index(r)
    nome = S.nome_revista(r)
    primeira = rid in PRIMEIRA_VALIDAR
    mat = next((m["nome"] for m in D.MATRIZES if m["id"] == r["matriz"]), "Comunitária 2026")
    cab = (
        f'<header class="en-ph"><div><h2>{esc(nome)}</h2><p class="mudo">{esc(mat)} · F1 e F2 · {D.COMP_NOME[r["comp"]]}</p></div>'
        f'<div class="linha">{S.btn("Abrir revista", S.href_revista(rid), icone="seta", cls="btn-sm")}'
        f'{S.btn("Preview", S.href_revista(rid) + "#conferir", icone="olho", cls="btn-sm")}</div></header>'
    )
    pronto = S.aviso("<b>Pronta para validar.</b> Os 6 passos estão completos. Validar registra seu nome e a hora, libera o zip e avisa o Impresso.", "ok")
    if r.get("editando"):
        pronto += S.aviso(
            f'<b>{esc(r["editando"])} está editando esta revista agora.</b> Se ela gravar antes de você validar, o servidor recusa o Validado e pede nova conferência.',
            "alerta",
            "cadeado",
            S.btn("Ver quem edita", S.href_revista(rid) + "#textos", cls="btn-sm"),
        )
    d = _DESATUALIZADAS[i % len(_DESATUALIZADAS)]
    if d:
        desat = S.aviso(
            f"<b>{d[0]} desatualizada:</b> {d[1]}. Não impede validar; atualize antes se o texto novo importa.",
            "alerta",
            acao=S.btn("Ver na revista", S.href_revista(rid) + "#textos", cls="btn-sm"),
        )
    else:
        desat = f'<p class="mudo">{S.tag("Nenhuma seção desatualizada", "ok", "ok")}</p>'
    if primeira:
        mud = (
            S.aviso("<b>Primeira entrega: tudo é novo.</b> Não há impressão anterior para comparar. O Impresso recebe a revista inteira.", "info")
            + '<ul class="checklist">'
            + "".join(
                f'<li>{S.st("ok")}<span class="txt">{t}</span></li>'
                for t in ["F1 com 4 etapas: 2EF, 5EF, 9EF e 3EM", "F2 com os infográficos Alfa e Outras Etapas", "Capa e textos das 7 seções"]
            )
            + "</ul>"
        )
    else:
        m = mudancas(r)
        mud = '<p class="mudo">Comparado com o impresso de 06/11.</p>'
        mud += "".join(_mud(x, prefixo=f) for f, xs in (("F1 · ", m["F1"]), ("F2 · ", m["F2"])) for x in xs)
    return (
        f'<section data-rev="{rid}" id="{rid}" hidden><div class="card en-painel">{cab}'
        f'<div class="en-sec">{pronto}</div>'
        f'<div class="en-sec"><h3>Seções desatualizadas</h3>{desat}</div>'
        f'<div class="en-sec"><h3>O que mudou desde a última impressão</h3>{mud}</div></div></section>'
    )


def validar():
    fila3 = D.revistas_na_fase(3)
    fila2 = D.revistas_na_fase(2)
    itens = ""
    for r in fila3:
        rid, nome = r["id"], S.nome_revista(r)
        bloq = r.get("editando")
        marca_attrs = 'data-bloq="1"' if bloq else ""
        dis = " disabled" if bloq else ""
        estado_tag = S.tag(f"{bloq} está editando", "alerta", "cadeado") if bloq else S.tag("Sem pendências", "ok")
        itens += (
            f'<div class="en-item" data-rid="{rid}" {marca_attrs}>'
            f'<input type="checkbox" data-marca data-edita{dis} aria-label="Marcar {esc(nome)} para validar">'
            f'<a class="en-nome" href="#{rid}"><span class="nm">{esc(nome)}</span>'
            f'<span class="en-meta">{S.regua_mini(3)}<span class="en-estado">{estado_tag}</span></span></a>'
            f'<span class="en-ok">{S.st("ok", "Validada")}</span></div>'
        )
    pend = ""
    for r in fila2:
        pend += (
            f'<a class="en-item en-saida" href="{S.href_revista(r["id"])}"><span class="en-txt">'
            f'<span class="nm">{esc(S.nome_revista(r))}</span><span class="en-causa">{esc("; ".join(r["pend"]))}</span></span>{S.ic("dir")}</a>'
        )
    fila = (
        '<div class="en-fila">'
        f'<div class="en-grupo"><h2>Prontas para validar <span class="mudo">(<span data-n-fila>{len(fila3)}</span>)</span></h2>{itens}</div>'
        f'<details class="en-grupo"><summary>Ainda com pendência <span class="mudo">({len(fila2)})</span>{S.ic("baixo")}</summary>{pend}</details>'
        "</div>"
    )
    paineis = "".join(_painel_validar(r) for r in fila3)
    fim = (
        '<section data-rev="fim" hidden>'
        + S.vazio(
            "Fila zerada",
            "Todas as revistas prontas foram validadas. As pendentes aparecem aqui quando chegarem à fase Conferir.",
            S.btn("Ir para o Impresso", "entrega-impresso.html", icone="seta"),
        )
        + "</section>"
    )
    barra = (
        '<div class="en-barra" role="region" aria-label="Ações de validação"><div class="en-barra-in"><div class="linha">'
        + S.btn("Validar e ir para a próxima", tom="prim", icone="ok", attrs="data-validar-prox data-edita")
        + S.btn('<span>Validar marcadas (<span data-n-marcadas>0</span>)</span>', attrs="data-validar-marcadas data-edita")
        + S.btn("Pular", tom="fan", attrs="data-pular")
        + '</div><span class="en-barra-txt">Conferindo <b data-atual></b></span></div></div>'
        + S.dialogo(
            "dlg-lote",
            "Validar as revistas marcadas?",
            '<p>Cada uma recebe seu nome e a hora no Validado e entra na fila do impresso. Confira a lista antes de seguir.</p>'
            '<p><b data-lote-n></b></p><ul class="checklist" data-lote-lista></ul>',
            S.btn("Voltar", attrs="data-fechar") + S.btn("Validar", tom="prim", icone="ok", attrs="data-lote-ok"),
        )
    )
    leitura = (
        '<div data-p="imp">'
        + S.aviso(
            "Você está no perfil Impresso: vê a fila e as mudanças, mas não valida. Quem valida é a equipe Pedagógica; peça a Ana Souza ou a Elisa Prado.",
            "leitura",
        )
        + "</div>"
    )
    corpo = (
        S.cab("Entrega", "Valide as revistas prontas, atualize o impresso e baixe os pacotes.")
        + _abas("Validar")
        + f'<div class="pilha" data-validar>{leitura}<div class="dividido">{fila}<div>{paineis}{fim}</div></div></div>{barra}'
    )
    return S.Pagina("entrega-validar.html", "Entrega", "entrega", corpo, trilha=_topo("Validar"))


# ── Impresso ──────────────────────────────────────────────────────────────
_SIT = {
    4: ("atualizar", "Para atualizar", "cobalto"),
    3: ("aguardando", "Aguardando Validado", "alerta"),
    5: ("dia", "Em dia", "ok"),
}


def _painel_impresso(r):
    rid, nome, f = r["id"], S.nome_revista(r), r["fase"]
    sit, sit_rot, tom = _SIT[f]
    quem, quando = r["validada"] or (None, None)
    primeira = rid in PRIMEIRA_IMPRESSO or (f == 3 and rid in PRIMEIRA_VALIDAR)
    if f == 3:
        sub = "Ainda não validada"
    else:
        sub = f"Validada por {quem} em {quando}"
    if f == 5:
        acao = f'<span class="tag tag-ok" data-sit-tag>Em dia</span>'
    elif f == 4:
        acao = S.btn("Marcar como impressa", tom="prim", icone="ok", attrs='data-marcar data-p="imp adm"')
    else:
        acao = S.btn("Marcar como impressa", tom="prim", icone="ok", attrs='data-p="imp adm" disabled title="Aguarda a validação desta revista"')
    topo = (
        f'<div class="en-topo-det"><div><h2>{esc(nome)}</h2><div class="en-sub"><span data-sit-tag>{S.tag(sit_rot, tom)}</span><span>{esc(sub)}</span></div></div>'
        f'<div class="linha">{acao}</div></div>'
    )
    avisos = ""
    if f == 4:
        avisos += f'<div data-p="ped mid" data-leitura-imp>{S.aviso("Só o perfil Impresso marca a revista como impressa. Você pode conferir o que mudou e baixar as planilhas.", "leitura")}</div>'
        avisos += '<div data-feito-msg hidden>' + S.aviso("Marcada como impressa. A revista saiu da fila de atualização.", "ok") + "</div>"
    if f == 3:
        avisos += S.aviso(
            "<b>Aguardando Validado.</b> Esta revista só entra no impresso depois de validada. Abaixo está a prévia do que vai mudar.",
            "alerta",
            acao=S.btn("Ir para Validar", f"entrega-validar.html#{rid}", cls="btn-sm"),
        )
    if f == 5:
        ultima = ULTIMA.get(rid, "08/11")
        entrega = f"Última entrega: {ultima} por Carla Mendes"
    elif primeira:
        entrega = "Primeira entrega"
    else:
        entrega = f"Última entrega: {ULTIMA.get(rid, '06/11')} por Carla Mendes"
    corpo = f'<p><b>{entrega}.</b>'
    if f == 5:
        corpo += ' <span class="mudo">O impresso está igual à versão validada.</span>'
    corpo += "</p>"
    m = mudancas(r)
    for fasc, titulo in (("F1", "F1 · Escalas por etapa"), ("F2", "F2 · Infográficos")):
        xs = m[fasc]
        if f == 5:
            conta = '<span class="mudo">· nada mudou desde a última entrega</span>'
            lista = f'<p class="mudo">{S.tag("Sem alterações", "ok", "ok")}</p>'
        elif primeira:
            conta = '<span class="mudo">· tudo é novo</span>'
            novos = [dict(kind="novo", escopo=x["escopo"], desc="incluído na primeira entrega", antes=None, depois=x["depois"] or x["antes"], novo=x["novo"]) for x in xs if x["kind"] != "removido"]
            lista = "".join(_mud(x, copiar=True) for x in novos)
        else:
            conta = f'<span class="mudo">· {len(xs)} {"item mudou" if len(xs) == 1 else "itens mudaram"}</span>'
            lista = "".join(_mud(x, copiar=True) for x in xs)
        fim_txt = (
            f'<header><h3>{titulo}</h3>{conta}<div class="linha">'
            f'{S.btn("Baixar planilhas", tom="fan", icone="baixar", cls="btn-sm", attrs=_t(f"Planilhas {fasc} de {nome} baixadas"))}'
            f'{S.btn("Abrir preview", S.href_revista(rid) + "#conferir", tom="fan", icone="olho", cls="btn-sm")}</div></header>{lista}'
        )
        corpo += f'<section class="en-fasc">{fim_txt}</section>'
    return (
        f'<section data-rev="{rid}" id="{rid}" class="en-det" hidden>{topo}'
        f'<div class="card en-painel">{avisos}{corpo}</div></section>'
    )


def impresso():
    revs = D.revistas_na_fase(4) + D.revistas_na_fase(3) + D.revistas_na_fase(5)
    itens = ""
    for r in revs:
        sit, rot, tom = _SIT[r["fase"]]
        rid, nome = r["id"], S.nome_revista(r)
        meta = f'Validada {r["validada"][1]}' if r["validada"] else "Na fila de validação"
        itens += (
            f'<div class="en-item" data-rid="{rid}" data-busca="{esc(nome)} {esc(r["nome_parceiro"])}" data-sit="{sit}">'
            f'<a class="en-nome" href="#{rid}"><span class="nm">{esc(nome)}</span>'
            f'<span class="en-meta"><span class="en-sit">{S.tag(rot, tom)}</span><span>{esc(meta)}</span></span></a></div>'
        )
    filtros = (
        '<div class="en-filtros">'
        + '<label class="campo"><span class="rot">Buscar revista</span><input class="input" type="search" data-filtro="#fila-imp" placeholder="Parceiro ou componente" autocomplete="off"></label>'
        + '<label class="campo"><span class="rot">Situação</span><select class="select" data-alvo="#fila-imp" data-filtra="sit">'
        + '<option value="">Todas (16)</option><option value="atualizar" selected>Para atualizar (4)</option>'
        + '<option value="aguardando">Aguardando Validado (8)</option><option value="dia">Em dia (4)</option></select></label></div>'
    )
    fila = f'<div class="en-fila"><div class="en-grupo" id="fila-imp">{filtros}{itens}</div></div>'
    paineis = "".join(_painel_impresso(r) for r in revs)
    corpo = (
        S.cab("Entrega", "Veja o que mudou em cada revista validada e marque a que já foi impressa.")
        + _abas("Impresso")
        + f'<div class="dividido" data-impresso>{fila}<div>{paineis}</div></div>'
    )
    return S.Pagina("entrega-impresso.html", "Entrega", "entrega", corpo, trilha=_topo("Impresso"))


# ── Pacotes ───────────────────────────────────────────────────────────────
def _mb(i):
    return f"{12 + ((i * 37) % 90) / 10:.1f}".replace(".", ",") + " MB"


def pacotes():
    validadas = D.revistas_na_fase(4) + D.revistas_na_fase(5)
    n = len(validadas)
    linhas = []
    for r in validadas:
        rid, nome = r["id"], S.nome_revista(r)
        i = D.REVISTAS.index(r)
        quem, quando = r["validada"]
        linhas.append(
            [
                f'<a class="nome" href="{S.href_revista(rid)}">{esc(nome)}</a>',
                f'{esc(quem)} <span class="mudo">· {esc(quando)}</span>',
                S.regua(r["fase"]),
                _mb(i),
                S.tag("F1", "ok", "ok") + " " + S.tag("F2", "ok", "ok"),
                f'<div class="linha" style="justify-content:flex-end;flex-wrap:nowrap">'
                f'{S.btn("Baixar zip", icone="baixar", cls="btn-sm", attrs=_t(f"Baixando {rid}.zip"))}'
                f'{S.btn("Baixar planilhas", tom="fan", icone="baixar", cls="btn-sm", attrs=_t(f"Planilhas de {nome} baixadas"))}</div>',
            ]
        )
    validadas_tab = S.tabela(["Revista", "Validada por", "Situação", "Zip", "Planilhas", ("Ações", "acoes")], linhas)
    outras = [r for r in D.REVISTAS if r["fase"] <= 3]
    linhas2 = []
    for r in outras:
        rid, nome = r["id"], S.nome_revista(r)
        if r["fase"] == 3:
            motivo = f'Valide a revista para gerar o zip. <a href="entrega-validar.html#{rid}">Ir para Validar</a>'
        else:
            motivo = f'Valide a revista para gerar o zip. Antes falta: {esc("; ".join(r["pend"]).lower())}. <a href="{S.href_revista(rid)}">Abrir revista</a>'
        dis = 'disabled title="Valide a revista para gerar o zip"'
        linhas2.append(
            [
                f'<a class="nome" href="{S.href_revista(rid)}">{esc(nome)}</a>',
                S.regua(r["fase"]),
                f'<span class="en-quebra">{motivo}</span>',
                f'<div class="linha" style="justify-content:flex-end;flex-wrap:nowrap">{S.btn("Baixar zip", icone="baixar", cls="btn-sm", attrs=dis)}'
                f'{S.btn("Baixar planilhas", tom="fan", icone="baixar", cls="btn-sm", attrs=dis)}</div>',
            ]
        )
    nao = len(outras)
    nao_tab = S.tabela(["Revista", "Situação", "Por que não dá", ("Ações", "acoes")], linhas2)
    corpo = (
        S.cab(
            "Entrega",
            "Zips e planilhas das revistas validadas. Só o que está validado gera pacote.",
            S.btn(f"Baixar todos os zips ({n})", tom="prim", icone="baixar", attrs=_t(f"Preparando {n} zips: o download começa em instantes")),
        )
        + _abas("Pacotes")
        + f'<div class="pilha">{validadas_tab}'
        + f'<details class="en-grupo"><summary>Ainda não validadas <span class="mudo">({nao})</span>{S.ic("baixo")}</summary>'
        + f'<div style="padding:12px">{nao_tab}</div></details></div>'
    )
    return S.Pagina("entrega-pacotes.html", "Entrega", "entrega", corpo, trilha=_topo("Pacotes"))


def paginas():
    return [validar(), impresso(), pacotes()]
