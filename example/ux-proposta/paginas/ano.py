"""Configurar o ano (2026) e Abrir 2027. Hoje isso só existe num popover do seletor de ano; aqui é uma tela de trabalho.

Uma tela com menu de âncoras (Etapas · Componentes · Padrões do ano · Próximo ano) e a tela de confirmação de abrir o ano seguinte.
"""
import dados as D
from paginas import shell as S
from paginas.parceiros import ETAPA_NOME, PADROES_PROP, corte, pl

esc = S.esc
LP_MT = [c for c, _ in D.COMPONENTES]


def _aviso_imp(texto):
    return f'<div data-p="imp">{S.aviso(texto, "leitura")}</div>'


def _secao(id_, titulo, sub, corpo, acao=""):
    a = f'<div class="sec-acao">{acao}</div>' if acao else ""
    return f'<section class="card card-p secao-ano" id="{id_}"><div class="sec-cab"><div><h2>{titulo}</h2><p class="sub">{sub}</p></div>{a}</div>{corpo}</section>'


def _etapas():
    linhas = []
    for e, m in D.ETAPAS:
        n = len([p for p in D.PARCEIROS if any(corte(p["id"], e, c) for c in LP_MT)])
        porque = (
            f"{pl(n, 'parceiro lançou', 'parceiros lançaram')} cortes em {e}. Mudar a escala máxima deixaria esses cortes fora da régua. "
            f"Para mudar, apague antes os cortes de {e} na planilha de Parceiros."
        )
        linhas.append(
            [
                f'<b>{e}</b> <span class="mudo">{ETAPA_NOME[e]}</span>',
                f'<input class="input input-num" type="number" inputmode="numeric" value="{m}" disabled aria-label="Escala máxima de {e}" title="{esc(porque)}">',
                f'<span class="tag" title="{esc(porque)}">{S.ic("cadeado")}Travada: há cortes lançados</span>',
                f'<a href="parceiros.html#cortes">{pl(n, "parceiro", "parceiros")} com cortes</a>',
            ]
        )
    tab = S.tabela(["Etapa", "Escala máxima", "Situação", "Uso"], linhas)
    acao = S.btn("Adicionar etapa", icone="mais", attrs='data-abrir="dlg-etapa" data-edita')
    return _secao(
        "etapas",
        "Etapas",
        "A escala máxima é o fim da régua de proficiência. Ela trava quando algum parceiro lança cortes naquela etapa.",
        tab,
        acao,
    )


def _componentes():
    linhas = []
    for c, nome in D.COMPONENTES:
        n = len([r for r in D.REVISTAS if r["comp"] == c])
        linhas.append(
            [
                f"<b>{c}</b>",
                f'<input class="input" value="{esc(nome)}" data-edita data-autosave aria-label="Nome do componente {c}" autocomplete="off">',
                f'<span class="mudo">{pl(n, "revista usa", "revistas usam")}</span>',
            ]
        )
    return _secao(
        "componentes",
        "Componentes",
        "O código (LP, MT) não muda; o nome aparece nas revistas e nas telas.",
        S.tabela(["Código", "Nome", "Uso"], linhas),
    )


def _padroes():
    total = len(D.REVISTAS)
    linhas = []
    for n, nome, cor in D.PADROES:
        sobre = [pid for pid, o in PADROES_PROP.items() if n in o]
        usam = total - 2 * len(sobre)
        uso = f"{pl(usam, 'revista usa', 'revistas usam')} esta cor e este nome"
        if sobre:
            uso += f' <span class="mudo">· {pl(len(sobre), "parceiro sobrescreve", "parceiros sobrescrevem")}</span>'
        linhas.append(
            [
                f'<input class="cor-pad" type="color" value="{cor}" data-edita aria-label="Cor do Padrão 0{n}">',
                f"Padrão 0{n}",
                f'<input class="input" value="{esc(nome)}" data-edita aria-label="Nome do Padrão 0{n}" autocomplete="off">',
                uso,
            ]
        )
    tab = S.tabela(["Cor", "Padrão", "Nome", "Uso"], linhas)
    acao = S.btn("Salvar padrões", icone="ok", attrs='data-abrir="dlg-impacto-padroes" data-edita')
    return _secao(
        "padroes",
        "Padrões do ano",
        "Cor e nome de cada nível de desempenho nas escalas. Um parceiro pode sobrescrever na ficha dele, aba Matriz e cores.",
        tab,
        acao,
    )


def _proximo():
    corpo = (
        f"<p>Abrir {D.ANO_PROX} copia a estrutura de {D.ANO}: etapas, componentes, Padrões, matrizes e templates. "
        f"O novo ano começa sem parceiros, cortes, projetos nem revistas, e {D.ANO} continua guardado.</p>"
        f'<div class="linha" data-p="ped mid adm">{S.btn(f"Abrir {D.ANO_PROX}", href="ano-abrir.html", tom="prim", icone="seta")}'
        '<span class="mudo">Você confere o que será copiado antes de confirmar.</span></div>'
        + _aviso_imp(f"Você está no perfil Impresso: só a equipe Pedagógica, Mídias Digitais ou Admin abre {D.ANO_PROX}.")
    )
    return _secao("proximo", "Próximo ano", f"{D.ANO_PROX} é o próximo ano que pode ser aberto.", corpo)


def _dialogos():
    et = (
        S.campo("Código da etapa", "codigo", attrs='required placeholder="Ex.: 7EF" autocomplete="off"')
        + S.campo("Nome", "nome", attrs='placeholder="Ex.: 7º ano do Ensino Fundamental" autocomplete="off"')
        + S.campo("Escala máxima", "max", tipo="number", attrs='required placeholder="500" inputmode="numeric"', ajuda="Fica travada quando o primeiro parceiro lançar cortes nesta etapa.")
    )
    rod_et = S.btn("Cancelar", attrs="data-fechar") + S.btn("Adicionar etapa", attrs='data-toast="Etapa adicionada." data-salva data-fechar')
    itens = ""
    for r in D.REVISTAS:
        if r["fase"] >= 4:
            quem, quando = D.VALIDADAS[r["id"]]
            itens += f'<li><b>{esc(S.nome_revista(r))}</b>{S.regua_mini(r["fase"])}<span class="mudo">validada por {esc(quem)} em {quando}</span></li>'
    n = len([r for r in D.REVISTAS if r["fase"] >= 4])
    imp = (
        f'<p>Mudar cor ou nome de um Padrão altera as escalas já validadas. As {n} revistas abaixo voltam para <b>{D.FASE_NOME[3]}</b> e precisam ser validadas de novo; as impressas ficam desatualizadas.</p>'
        f'<ul class="lista-imp">{itens}</ul>'
    )
    rod_imp = S.btn("Cancelar", attrs="data-fechar") + S.btn(
        f"Salvar e tirar o Validado de {n} revistas",
        tom="perigo",
        attrs=f'data-toast="Padrões salvos. {n} revistas voltaram para Conferir." data-salva data-fechar',
    )
    return S.dialogo("dlg-etapa", "Adicionar etapa", et, rod_et) + S.dialogo("dlg-impacto-padroes", f"Isto tira o Validado de {pl(n, 'revista', 'revistas')}", imp, rod_imp)


def pagina_ano():
    ancoras = (
        '<nav class="lista-sel ancoras" data-ancoras aria-label="Nesta página">'
        f'<a href="#etapas" aria-current="true">Etapas<span class="mudo">{len(D.ETAPAS)}</span></a>'
        f'<a href="#componentes">Componentes<span class="mudo">{len(D.COMPONENTES)}</span></a>'
        f'<a href="#padroes">Padrões do ano<span class="mudo">{len(D.PADROES)}</span></a>'
        f'<a href="#proximo">Próximo ano<span class="mudo">{D.ANO_PROX}</span></a></nav>'
    )
    corpo = (
        S.cab(
            f'Configurar o ano <span class="tag tag-cobalto">{D.ANO}</span>',
            f"O que vale para todos os parceiros de {D.ANO}. Mudanças aqui chegam a todas as revistas do ano.",
        )
        + '<div class="pilha pilha-p">'
        + _aviso_imp("Você está no perfil Impresso: vê a configuração do ano, mas não altera. Para editar, peça acesso à equipe Pedagógica.")
        + "</div>"
        + f'<div class="dividido ano">{ancoras}<div class="pilha">{_etapas()}{_componentes()}{_padroes()}{_proximo()}</div></div>'
        + _dialogos()
    )
    return S.Pagina("ano.html", "Configurar o ano", "ano", corpo, trilha=[("Configurar o ano", None)], status=True)


def pagina_abrir():
    copiado = [
        ("Etapas", f"{len(D.ETAPAS)}: " + ", ".join(e for e, _ in D.ETAPAS) + ", com a escala máxima de cada uma"),
        ("Componentes", f"{len(D.COMPONENTES)}: " + " e ".join(f"{c} ({n})" for c, n in D.COMPONENTES)),
        ("Nomes e cores dos Padrões", f"{len(D.PADROES)} Padrões do ano"),
        ("Matrizes", f"{len(D.MATRIZES)}: " + ", ".join(m["nome"] for m in D.MATRIZES)),
        ("Templates", f"{len(D.TEMPLATES)}, cada um com a última versão"),
    ]
    nao = [
        ("Parceiros", f"{len(D.PARCEIROS)} em {D.ANO}. Cadastre os de {D.ANO_PROX} depois."),
        ("Cortes", f"Cada parceiro lança os seus em {D.ANO_PROX}."),
        ("Projetos", f"Nascem quando o primeiro corte de {D.ANO_PROX} for lançado."),
        ("Revistas", f"{len(D.REVISTAS)} em {D.ANO}. Continuam guardadas, só para leitura."),
    ]
    li = lambda st, t, d: f'<li>{S.st(st)}<span class="txt"><b>{t}</b><small class="bloco">{d}</small></span></li>'
    col1 = (
        '<section class="card card-p"><h2>O que será copiado</h2><p class="sub">Vira o ponto de partida de '
        f'{D.ANO_PROX}.</p><ul class="checklist">' + "".join(li("ok", t, d) for t, d in copiado) + "</ul></section>"
    )
    col2 = (
        '<section class="card card-p"><h2>O que NÃO será copiado</h2><p class="sub">Começa vazio em '
        f'{D.ANO_PROX}.</p><ul class="checklist">' + "".join(li("na", t, d) for t, d in nao) + "</ul></section>"
    )
    ano = S.campo("Ano a abrir", "ano", str(D.ANO_PROX), attrs="readonly", ajuda=f"O próximo ano que pode ser aberto é {D.ANO_PROX}.")
    confirmar = (
        '<div class="confirma" data-p="ped mid adm">'
        + S.aviso(
            f"<b>Não há desfazer.</b> Depois de aberto, {D.ANO_PROX} não pode ser apagado. O que foi copiado vira ponto de partida; o que ficou de fora precisa ser criado lá.",
            "alerta",
        )
        + '<div class="linha">'
        + S.btn(f"Abrir {D.ANO_PROX}", href="index.html", tom="prim", icone="seta", attrs=f'data-toast="{D.ANO_PROX} aberto. Você está na temporada {D.ANO_PROX}." data-atraso')
        + S.btn("Voltar sem abrir", href="ano.html#proximo", tom="fan")
        + "</div></div>"
        + _aviso_imp(f"Você está no perfil Impresso: só a equipe Pedagógica, Mídias Digitais ou Admin abre {D.ANO_PROX}.")
    )
    corpo = (
        S.cab(f"Abrir {D.ANO_PROX} a partir de {D.ANO}", f"Confira o que será copiado. {D.ANO} não muda e continua disponível para consulta.")
        + f'<div class="pilha"><div class="campo-ano">{ano}</div><div class="duas">{col1}{col2}</div>{confirmar}</div>'
    )
    return S.Pagina(
        "ano-abrir.html",
        f"Abrir {D.ANO_PROX}",
        "ano",
        corpo,
        trilha=[("Configurar o ano", "ano.html"), (f"Abrir {D.ANO_PROX}", None)],
    )


def paginas():
    return [pagina_ano(), pagina_abrir()]


CSS = """
/* ── Configurar o ano ────────────────────────────────────────────────── */
.pilha-p{gap:10px;margin-bottom:14px}
.pilha-p:empty{display:none;margin:0}
.bloco{display:block}
.cab h1 .tag{margin-left:6px;vertical-align:middle}
.dividido.ano{grid-template-columns:210px minmax(0,1fr)}
.dividido.ano .pilha,.duas > *{min-width:0}
.dividido.ano .pilha{grid-template-columns:minmax(0,1fr)}
.ancoras{position:sticky;top:72px}
.ancoras a{justify-content:space-between}
.secao-ano{scroll-margin-top:72px}
.sec-cab{display:flex;gap:16px;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;margin-bottom:12px}
.sec-cab .sub{max-width:62ch;margin-top:2px}
.secao-ano > p{margin-bottom:14px;max-width:70ch}
.secao-ano .linha{margin-top:4px}
.input-num{width:110px}
.cor-pad{width:46px;height:32px;padding:2px;border:1px solid var(--fio-2);border-radius:6px;background:var(--papel);cursor:pointer}
.lista-imp{list-style:none;margin:0;padding:0;display:grid;max-height:280px;overflow:auto;border:1px solid var(--fio);border-radius:8px}
.lista-imp li{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:9px 12px;border-bottom:1px solid var(--fio)}
.lista-imp li:last-child{border-bottom:0}
.lista-imp .mudo{font-size:12px}
.campo-ano{max-width:340px}
.duas{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;align-items:start}
.duas .checklist li{align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--fio)}
.duas .checklist li:last-child{border-bottom:0}
.duas .checklist .st{margin-top:1px}
.confirma{display:grid;gap:10px;background:var(--papel);border:1px solid var(--fio);border-radius:var(--raio-g);padding:14px}
@media (max-width:960px){
  .dividido.ano{grid-template-columns:minmax(0,1fr)}
  .ancoras{position:static;display:flex;overflow-x:auto}
  .ancoras a{border-bottom:0;white-space:nowrap}
  .ancoras .mudo{display:none}
  .duas{grid-template-columns:1fr}
}
"""

JS = r"""
(() => {
  /* menu de âncoras: marca a seção que está no topo */
  const nav = document.querySelector("[data-ancoras]");
  if (nav) {
    const links = [...nav.querySelectorAll("a")];
    const secoes = links.map((a) => document.querySelector(a.getAttribute("href")));
    const marca = () => {
      let i = 0;
      secoes.forEach((s, k) => { if (s && s.getBoundingClientRect().top <= 140) i = k; });
      if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) i = secoes.length - 1;
      links.forEach((a, k) => a.setAttribute("aria-current", String(k === i)));
    };
    window.addEventListener("scroll", marca, { passive: true });
    marca();
  }
  /* "Abrir": deixa o aviso aparecer antes de seguir para a próxima página */
  document.addEventListener("click", (e) => {
    const a = e.target.closest("[data-atraso]");
    if (!a) return;
    e.preventDefault();
    setTimeout(() => { location.href = a.getAttribute("href"); }, 1100);
  });
})();
"""
