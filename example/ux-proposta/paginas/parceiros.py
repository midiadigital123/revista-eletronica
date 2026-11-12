"""Parceiros: a lista única (Geral · Cortes · Variáveis) e a ficha de cada parceiro (Resumo · Cortes · Matriz e cores · Variáveis).

Substitui o cadastro de parceiros e as abas Cortes e Variáveis do hub "Projetos". Dados 100% fictícios (ver dados.py).
Funções públicas usadas por outros módulos: corte(), valor_var(), estado(), ETAPA_NOME, pl().
"""
import dados as D
from paginas import shell as S

esc = S.esc

ETAPA_NOME = {
    "2EF": "2º ano do Ensino Fundamental",
    "5EF": "5º ano do Ensino Fundamental",
    "9EF": "9º ano do Ensino Fundamental",
    "3EM": "3ª série do Ensino Médio",
}
MAT = {m["id"]: m for m in D.MATRIZES}
LP_MT = [c for c, _ in D.COMPONENTES]
NOME_PADRAO_ANO = {n: nome for n, nome, _ in D.PADROES}

# Sobrescritas de Padrões por parceiro (dado fictício): número do Padrão -> (nome, cor).
PADROES_PROP = {
    "vale-verde": {2: ("Em desenvolvimento", "#ff8d43")},
    "serra-alta": {3: ("Proficiente", "#7fa8ff")},
}
# Passos de escala sobrescritos (dado fictício): (parceiro, etapa, componente) -> valor.
PASSOS_PROP = {("vale-verde", "2EF", "MT"): 40, ("serra-alta", "5EF", "LP"): 20}
PASSO_MATRIZ = {"2EF": 50, "5EF": 25, "9EF": 25, "3EM": 25}


def pl(n, um, varios):
    return f"{n} {um if n == 1 else varios}"


# ── Dados derivados ───────────────────────────────────────────────────────
# Células de corte sem dado: escolhidas para casar com as pendências das revistas em Preparar.
_FALTAM = {
    ("rio-claro", "9EF", "LP"), ("rio-claro", "9EF", "MT"), ("rio-claro", "3EM", "LP"), ("rio-claro", "3EM", "MT"),
    ("ouro-velho", "3EM", "LP"), ("ouro-velho", "3EM", "MT"), ("ilha-branca", "5EF", "MT"),
}


def corte(pid, etapa, comp):
    """'a, b, c' ou '' (sem corte). D.cortes deixaria Foz do Lago · MT vazio, mas essa revista já está em Conferir: completamos."""
    if (pid, etapa, comp) in _FALTAM:
        return ""
    return D.cortes(pid, etapa, comp) or D.cortes("campo-largo", etapa, comp)


def _formula_var(pid, chave):
    i = [p["id"] for p in D.PARCEIROS].index(pid)
    p = D.PARCEIRO_POR_ID[pid]
    return {
        "colecao": f"2596-{1000 + i * 13}",
        "pat_m": p["nome"].split()[0].lower() + "ense",
        "pat_f": p["nome"].split()[0].lower() + "ense",
        "programa": f"Avalia {p['nome']}",
        "secretaria": f"Secretaria de Educação de {p['nome']}",
        "regional": f"Regional {i % 5 + 1}",
        "pd01": "Baixo",
        "pd02": "Básico",
    }[chave]


def valor_var(pid, chave):
    """Vazio só para quem ainda está em Preparar/Montar; revista em Conferir ou além já tem os dados."""
    v = D.variavel(pid, chave)
    if v or any(D.POR_ID[f"{pid}-{c.lower()}"]["fase"] <= 2 for c in LP_MT):
        return v
    return _formula_var(pid, chave)


def valor_2025(pid, chave):
    return "" if chave == "colecao" else _formula_var(pid, chave)  # o ISSN é novo em 2026


def revistas_de(pid):
    return [D.POR_ID[f"{pid}-{c.lower()}"] for c in LP_MT]


def validadas(pid):
    return [r for r in revistas_de(pid) if r["fase"] >= 4]


def edicao(pid):
    """[(revista, quem)] das revistas do parceiro abertas por alguém."""
    return [(D.POR_ID[rid], quem) for rid, quem in D.EDITANDO.items() if D.POR_ID[rid]["parceiro"] == pid]


def estado(pid):
    p = D.PARCEIRO_POR_ID[pid]
    f_cortes = [(e, c) for e, _ in D.ETAPAS for c in LP_MT if not corte(pid, e, c)]
    f_vars = [v for v in D.VARIAVEIS if not valor_var(pid, v[0])]
    sit = "sem-matriz" if not p["matriz"] else "cortes" if f_cortes else "variaveis" if f_vars else "completo"
    return {"p": p, "f_cortes": f_cortes, "f_vars": f_vars, "sit": sit, "matriz": MAT.get(p["matriz"])}


def pend_revista(r):
    """Pendências da revista, coerentes com os dados desta tela (as de Preparar nascem dos cortes e variáveis do parceiro)."""
    e = estado(r["parceiro"])
    if r["fase"] == 1:
        t = []
        if not e["matriz"]:
            t.append("Sem matriz")
        falt = [et for et, c in e["f_cortes"] if c == r["comp"]]
        if falt:
            t.append(f"Cortes de {', '.join(falt)} {r['comp']} faltando")
        if e["f_vars"]:
            t.append(pl(len(e["f_vars"]), "variável vazia", "variáveis vazias"))
        return t or r["pend"]
    return r["pend"] if r["fase"] == 2 else []


def _id_imp(pid):
    return "dlg-impacto-var" if pid == "serra-alta" else f"dlg-impacto-{pid}"


def _atrib(pid, impacto_id=None):
    """Atributos de um campo que grava: bloqueado se a revista está em edição; modal de impacto se há revista validada."""
    if edicao(pid):
        return "disabled"
    if impacto_id and validadas(pid):
        return f'data-edita data-impacto="{impacto_id}"'
    return "data-edita data-autosave"


# ── Peças ─────────────────────────────────────────────────────────────────
def _dlg_impacto(id_, pid, o_que):
    rs = validadas(pid)
    nome = D.PARCEIRO_POR_ID[pid]["nome"]
    itens = ""
    for r in rs:
        quem, quando = D.VALIDADAS[r["id"]]
        extra = f"validada por {quem} em {quando}" + (" · o impresso fica desatualizado" if r["fase"] == 5 else "")
        itens += f'<li><b>{esc(S.nome_revista(r))}</b>{S.regua_mini(r["fase"])}<span class="mudo">{extra}</span></li>'
    corpo = (
        f'<p>Mudar {o_que} de <b>{esc(nome)}</b> altera o que já foi validado. '
        f'{"Esta revista volta" if len(rs) == 1 else "Estas revistas voltam"} para <b>{D.FASE_NOME[3]}</b> e precisa{"" if len(rs) == 1 else "m"} ser validada{"" if len(rs) == 1 else "s"} de novo:</p>'
        f'<ul class="lista-imp">{itens}</ul>'
    )
    rod = S.btn("Cancelar", attrs="data-fechar") + S.btn("Gravar e tirar o Validado", tom="perigo", attrs="data-impacto-ok")
    return S.dialogo(id_, f"Isto tira o Validado de {pl(len(rs), 'revista', 'revistas')}", corpo, rod)


def _dialogos_gerais():
    novo = (
        S.campo("Nome do parceiro", "nome", attrs='required placeholder="Ex.: Vale do Sol" autocomplete="off"')
        + S.selecao("Tipo", "tipo", [("Estado", "Estado"), ("Município", "Município")])
        + '<p class="ajuda">O projeto e as revistas nascem quando o primeiro corte for lançado.</p>'
    )
    rod_novo = S.btn("Cancelar", attrs="data-fechar") + S.btn(
        "Criar parceiro", tom="prim", attrs='data-toast="Parceiro criado. Lance o primeiro corte para gerar as revistas." data-fechar'
    )
    ren = S.campo("Novo nome", "nome", attrs='required autocomplete="off"', ajuda="O nome aparece nas revistas, nas listas e na busca. O endereço das telas não muda.")
    rod_ren = S.btn("Cancelar", attrs="data-fechar") + S.btn("Renomear", tom="prim", attrs='data-toast="Parceiro renomeado." data-fechar')
    des = (
        '<p>Desativar <b data-nome-alvo>o parceiro</b> tira o parceiro das listas e das telas de trabalho de 2026. '
        "As revistas, os cortes e o histórico ficam guardados, e dá para reativar depois.</p>"
    )
    rod_des = S.btn("Cancelar", attrs="data-fechar") + S.btn("Desativar parceiro", tom="perigo", attrs='data-toast="Parceiro desativado. Reative quando precisar." data-fechar')
    return (
        S.dialogo("dlg-novo-parceiro", "Novo parceiro", novo, rod_novo)
        + S.dialogo("dlg-renomear", "Renomear parceiro", ren, rod_ren)
        + S.dialogo("dlg-desativar", "Desativar parceiro?", des, rod_des)
    )


def _menu_parceiro(p):
    uso = any(r["fase"] >= 2 for r in revistas_de(p["id"]))
    return S.menu_ic(
        [
            S.item_menu("Renomear", icone="lapis", attrs=f'data-abrir="dlg-renomear" data-nome-atual="{esc(p["nome"])}" data-edita'),
            S.item_menu("Desativar parceiro", icone="cadeado", attrs=f'data-abrir="dlg-desativar" data-nome-atual="{esc(p["nome"])}" data-edita'),
            "<hr>",
            S.item_menu("Excluir", href="excluir-em-uso.html" if uso else "excluir-livre.html", icone="lixeira", perigo=True, attrs="data-edita"),
        ],
        rotulo=f"Mais ações de {p['nome']}",
    )


def _aviso_imp(o_que):
    return f'<div data-p="imp">{S.aviso(f"Você está no perfil Impresso: vê tudo, mas não altera {o_que}. Para editar, peça acesso à equipe Pedagógica.", "leitura")}</div>'


def _conta(pid, aba, n, total, falta):
    if n == total:
        return f'<span class="conta">{S.st("ok")}{n} de {total}</span>'
    return f'<a class="conta conta-pend" href="parceiro-{pid}.html#{aba}" title="{esc(falta)}">{S.st("pend", falta)}{n} de {total}</a>'


def _fase_mini(r):
    return f'<a class="fase-mini" href="{S.href_revista(r["id"])}" title="Abrir {esc(S.nome_revista(r))}">{S.regua_mini(r["fase"])}<small>{D.FASE_NOME[r["fase"]]}</small></a>'


# ── parceiros.html ────────────────────────────────────────────────────────
def _aba_geral():
    linhas = []
    for p in D.PARCEIROS:
        pid = p["id"]
        e = estado(pid)
        rl, rm = revistas_de(pid)
        m = (
            S.tag(e["matriz"]["nome"], "cobalto")
            if e["matriz"]
            else f'<a class="conta" href="parceiro-{pid}.html#matriz" title="Escolher a matriz">{S.tag("sem matriz", "alerta", "alerta")}</a>'
        )
        ed = " ".join(S.tag(f"{quem} · {r['comp']}", "alerta", "lapis") for r, quem in edicao(pid)) or '<span class="mudo">—</span>'
        busca = f'{p["nome"]} {p["sigla"]} {p["tipo"]} {e["matriz"]["nome"] if e["matriz"] else "sem matriz"}'
        linhas.append(
            (
                f'data-busca="{esc(busca)}" data-tipo="{p["tipo"]}" data-situacao="{e["sit"]}"',
                [
                    f'<a class="nome" href="{S.href_parceiro(pid)}">{esc(p["nome"])}</a> <span class="mudo">{p["sigla"]}</span> {S.tag(p["tipo"])}',
                    m,
                    _conta(pid, "cortes", 8 - len(e["f_cortes"]), 8, "Faltam " + pl(len(e["f_cortes"]), "corte", "cortes")),
                    _conta(pid, "variaveis", 8 - len(e["f_vars"]), 8, "Faltam " + pl(len(e["f_vars"]), "variável", "variáveis")),
                    _fase_mini(rl),
                    _fase_mini(rm),
                    ed,
                    _menu_parceiro(p),
                ],
            )
        )
    cab = ["Parceiro", "Matriz", "Cortes", "Variáveis", "LP", "MT", "Em edição", ('<span class="so-leitor">Ações</span>', "acoes")]
    filtros = (
        '<div class="barra-filtros">'
        '<input class="input" type="search" data-filtro="#tab-parceiros" placeholder="Buscar parceiro, sigla ou matriz" aria-label="Buscar parceiro">'
        '<select class="select" data-alvo="#tab-parceiros" data-filtra="tipo" aria-label="Tipo de parceiro"><option value="">Todos os tipos</option><option>Estado</option><option>Município</option></select>'
        '<select class="select" data-alvo="#tab-parceiros" data-filtra="situacao" aria-label="Situação">'
        '<option value="">Toda situação</option><option value="completo">Pronto para as revistas</option><option value="sem-matriz">Sem matriz</option>'
        '<option value="cortes">Cortes incompletos</option><option value="variaveis">Variáveis incompletas</option></select>'
        f'<span class="contagem-geral"><b data-contagem="#tab-parceiros">{len(D.PARCEIROS)}</b> de {len(D.PARCEIROS)} parceiros</span></div>'
    )
    return filtros + S.tabela(cab, linhas, id_="tab-parceiros")


def _aba_cortes():
    th1 = '<th class="col-fixa rot" rowspan="2">Parceiro</th>' + "".join(
        f'<th class="ctr ini-grupo" colspan="2">{e} · até {m}</th>' for e, m in D.ETAPAS
    )
    th2 = "".join(f'<th class="ctr{" ini-grupo" if c == "LP" else ""}">{c}</th>' for _ in D.ETAPAS for c in LP_MT)
    corpo = ""
    n_vazias = 0
    parc_vazias = set()
    for p in D.PARCEIROS:
        pid = p["id"]
        trava = edicao(pid)
        nome_td = f'<a class="nome" href="{S.href_parceiro(pid)}">{esc(p["nome"])}</a>'
        if trava:
            r, quem = trava[0]
            nome_td += f'<small class="mudo bloco">Em edição por {esc(quem)} · {r["comp"]}</small>'
        celulas = ""
        for e, m in D.ETAPAS:
            for c in LP_MT:
                v = corte(pid, e, c)
                rot = f"Cortes de {e} {c} em {p['nome']}"
                ini = " ini-grupo" if c == "LP" else ""
                attr = _atrib(pid, _id_imp(pid))
                if not v:
                    n_vazias += 1
                    parc_vazias.add(pid)
                if (pid, e, c) == ("campo-largo", "5EF", "LP"):
                    celulas += (
                        f'<td class="td-conflito{ini}"><input class="cel cel-corte cel-conflito" value="155, 180, 205" data-corte data-max="{m}" '
                        f'data-rot="{e} · {c} · {esc(p["nome"])}" aria-label="{esc(rot)} (conflito: outra pessoa gravou)" aria-invalid="true" {attr}>'
                        '<div class="conf"><span>agora: <b>160, 185, 210</b></span><small>Elisa Prado gravou às 10:42</small>'
                        '<button type="button" class="btn btn-sm" data-conflito="155, 180, 205" data-edita>Tentar de novo</button></div></td>'
                    )
                    continue
                celulas += (
                    f'<td class="{ini.strip()}"><input class="cel cel-corte{"" if v else " cel-vazia"}" value="{esc(v)}" placeholder="sem corte" '
                    f'data-corte data-vazio data-max="{m}" data-rot="{e} · {c} · {esc(p["nome"])}" aria-label="{esc(rot)}" autocomplete="off" {attr}></td>'
                )
        corpo += f'<tr><td class="col-fixa rot">{nome_td}</td>{celulas}</tr>'
    tabela = (
        '<div class="tab-caixa rolagem"><table class="tabela grade" aria-label="Cortes por parceiro, etapa e componente">'
        f"<thead><tr>{th1}</tr><tr>{th2}</tr></thead><tbody>{corpo}</tbody></table></div>"
    )
    regra = f'<p class="regra">{S.ic("info")}<span>De 1 a 4 cortes inteiros e crescentes, separados por vírgula; célula vazia apaga o corte.</span></p>'
    aviso_vazias = (
        f'<div data-vazias=".cel-corte" data-um="célula sem dado" data-varios="células sem dado">'
        + S.aviso(
            f'<b data-n>{pl(n_vazias, "célula sem dado", "células sem dado")}</b> em {pl(len(parc_vazias), "parceiro", "parceiros")}. Sem corte, a revista daquela etapa não monta a escala.',
            "alerta",
            acao=S.btn("Ir para a primeira", icone="seta", attrs='data-ir-cel="[data-painel=\'cortes\'] .cel-vazia"'),
        )
        + "</div>"
    )
    aviso_conf = (
        '<div data-aviso-conflito>'
        + S.aviso(
            "<b>Elisa Prado gravou antes de você</b> em Campo Largo · 5EF · LP. Seu valor (155, 180, 205) não foi salvo: confira a célula destacada e tente de novo para sobrescrever.",
            "erro",
            acao=S.btn("Ver a célula", attrs='data-ir-cel=".cel-conflito"'),
        )
        + "</div>"
    )
    return f'<div class="pilha pilha-p">{regra}{aviso_vazias}{aviso_conf}</div>' + tabela, n_vazias


def _aba_variaveis():
    grupos = []
    for v in D.VARIAVEIS:
        if grupos and grupos[-1][0] == v[2]:
            grupos[-1][1] += 1
        else:
            grupos.append([v[2], 1])
    th1 = '<th class="col-fixa rot" rowspan="2">Parceiro</th>' + "".join(f'<th class="ini-grupo" colspan="{n}">{esc(g)}</th>' for g, n in grupos)
    th2 = "".join(f'<th class="{"ini-grupo" if i == 0 or D.VARIAVEIS[i][2] != D.VARIAVEIS[i - 1][2] else ""}">{esc(v[1])}</th>' for i, v in enumerate(D.VARIAVEIS))
    corpo = ""
    n_vazias = 0
    parc_vazias = set()
    for p in D.PARCEIROS:
        pid = p["id"]
        trava = edicao(pid)
        val = validadas(pid)
        nome_td = f'<a class="nome" href="{S.href_parceiro(pid)}">{esc(p["nome"])}</a>'
        if trava:
            nome_td += f'<small class="mudo bloco">Em edição por {esc(trava[0][1])} · {trava[0][0]["comp"]}</small>'
        elif val:
            nome_td += f'<small class="mudo bloco">{pl(len(val), "revista validada", "revistas validadas")}</small>'
        celulas = ""
        for i, v in enumerate(D.VARIAVEIS):
            chave, nome, grupo = v[0], v[1], v[2]
            valor = valor_var(pid, chave)
            ini = "ini-grupo" if i == 0 or D.VARIAVEIS[i - 1][2] != grupo else ""
            if not valor:
                n_vazias += 1
                parc_vazias.add(pid)
            attr = _atrib(pid, _id_imp(pid))
            celulas += (
                f'<td class="{ini}"><input class="cel cel-var{"" if valor else " cel-vazia"}" value="{esc(valor)}" placeholder="sem valor" data-vazio '
                f'data-v25="{esc(valor_2025(pid, chave))}" aria-label="{esc(nome)} de {esc(p["nome"])}" autocomplete="off" {attr}></td>'
            )
        corpo += f'<tr><td class="col-fixa rot">{nome_td}</td>{celulas}</tr>'
    tabela = (
        '<div class="tab-caixa rolagem"><table class="tabela grade" aria-label="Variáveis por parceiro">'
        f"<thead><tr>{th1}</tr><tr>{th2}</tr></thead><tbody>{corpo}</tbody></table></div>"
    )
    defs = "".join(
        f'<div class="def-var"><span><b>{esc(nome)}</b> <span class="var">{esc(marc)}</span></span><span class="mudo">Aparece em: {esc(onde)}</span></div>'
        for _, nome, _, marc, onde in D.VARIAVEIS
    )
    painel = (
        f'<details class="card card-p painel-var" open><summary>{S.ic("baixo", "seta")}<span>O que é cada variável</span></summary>'
        '<p class="mudo">O texto dos templates troca cada marcador pelo valor do parceiro. Marcador sem valor deixa o trecho em branco na revista.</p>'
        f'<div class="def-vars">{defs}</div></details>'
    )
    aviso = (
        '<div data-vazias=".cel-var" data-um="célula vazia" data-varios="células vazias">'
        + S.aviso(
            f'<b data-n>{pl(n_vazias, "célula vazia", "células vazias")}</b> em {pl(len(parc_vazias), "parceiro", "parceiros")}. '
            "Se a variável já existia em 2025, copie os valores de lá; o que já está preenchido não muda.",
            "alerta",
            acao=S.btn("Copiar valores vazios de 2025", icone="copiar", attrs="data-copiar-2025 data-edita"),
        )
        + "</div>"
    )
    return f'<div class="pilha pilha-p">{aviso}{painel}</div>' + tabela, n_vazias


def _dialogos_impacto_lista():
    return "".join(_dlg_impacto(_id_imp(p["id"]), p["id"], "um valor") for p in D.PARCEIROS if validadas(p["id"]) and not edicao(p["id"]))


def pagina_lista():
    cortes_html, n_c = _aba_cortes()
    vars_html, n_v = _aba_variaveis()
    acoes = (
        S.btn("Baixar planilha de grupos", icone="baixar", attrs='data-toast="Planilha de grupos baixada: grupos-2026.xlsx"')
        + S.btn("Novo parceiro", tom="prim", icone="mais", attrs='data-abrir="dlg-novo-parceiro" data-edita')
    )
    abas = S.abas_js([("geral", "Geral", len(D.PARCEIROS)), ("cortes", "Cortes", n_c or None), ("variaveis", "Variáveis", n_v or None)])
    corpo = (
        S.cab("Parceiros", f"Cadastro, cortes e variáveis de cada parceiro em {D.ANO}.", acoes)
        + _aviso_imp("cortes nem variáveis")
        + abas
        + f'<section data-painel="geral">{_aba_geral()}</section>'
        + f'<section data-painel="cortes">{cortes_html}</section>'
        + f'<section data-painel="variaveis">{vars_html}</section>'
        + _dialogos_gerais()
        + _dialogos_impacto_lista()
    )
    return S.Pagina("parceiros.html", "Parceiros", "parceiros", corpo, trilha=[("Parceiros", None)], largura="larga", status=True)


# ── parceiro-<id>.html ────────────────────────────────────────────────────
def _resumo(p, e):
    pid = p["id"]
    nf, nv = len(e["f_cortes"]), len(e["f_vars"])

    def item(ok, aba, titulo, detalhe, acao):
        btn = "" if ok else S.btn(acao, href=f"#{aba}", attrs=f'data-ir-aba="{aba}" data-edita', cls="btn-sm")
        return (
            f'<li>{S.st("ok" if ok else "pend")}<a href="#{aba}" data-ir-aba="{aba}">{titulo} <small>{detalhe}</small></a>{btn}</li>'
        )

    falt_c = ", ".join(f"{et} {c}" for et, c in e["f_cortes"][:3]) + (f" e mais {nf - 3}" if nf > 3 else "")
    falt_v = ", ".join(v[1] for v in e["f_vars"][:2]) + (f" e mais {nv - 2}" if nv > 2 else "")
    itens = (
        item(bool(e["matriz"]), "matriz", "Matriz escolhida", esc(e["matriz"]["nome"]) if e["matriz"] else "nenhuma escolhida", "Escolher matriz")
        + item(not nf, "cortes", "Cortes lançados", f"{8 - nf} de 8" + (f" · faltam {falt_c}" if nf else " · 4 etapas, LP e MT"), "Lançar cortes")
        + item(not nv, "variaveis", "Variáveis preenchidas", f"{8 - nv} de 8" + (f" · faltam {esc(falt_v)}" if nv else ""), "Preencher")
    )
    pendentes = (not e["matriz"]) + (nf > 0) + (nv > 0)
    sub = "Tudo pronto: as duas revistas podem avançar." if not pendentes else f"Faltam {pl(pendentes, 'item', 'itens')} para as revistas montarem sem lacunas."
    bloco1 = f'<section class="card card-p"><h2>Pronto para as revistas?</h2><p class="sub">{sub}</p><ul class="checklist">{itens}</ul></section>'

    rs = revistas_de(pid)
    mais_atrasada = min(rs, key=lambda r: r["fase"])
    primaria = mais_atrasada["fase"] < 3
    linhas = ""
    for r in rs:
        nome_comp = D.COMP_NOME[r["comp"]]
        if r["fase"] <= 2:
            pend = " ".join(S.tag(t, "alerta") for t in pend_revista(r)) or S.tag("Falta começar a montar", "alerta")
        elif r["fase"] == 3:
            pend = f'{S.st("ok")} <span>Pronta para validar</span>'
        elif r["fase"] == 4:
            quem, quando = D.VALIDADAS[r["id"]]
            pend = f'{S.st("ok")} <span>Validada por {esc(quem)} em {quando}; falta atualizar o impresso</span>'
        else:
            quem, quando = D.VALIDADAS[r["id"]]
            pend = f'{S.st("ok")} <span>Impresso em dia · validada por {esc(quem)} em {quando}</span>'
        ed = [q for rr, q in edicao(pid) if rr["id"] == r["id"]]
        if ed:
            pend += " " + S.tag(f"{ed[0]} está editando", "alerta", "lapis")
        prim = "prim" if (primaria and r is mais_atrasada) else "sec"
        linhas += (
            f'<div class="rev-linha"><div class="rev-id"><b>{esc(nome_comp)}</b>{S.regua(r["fase"])}</div>'
            f'<div class="rev-pend">{pend}</div>'
            f'<div class="rev-acoes">{S.btn("Preview", href=S.href_revista(r["id"]) + "#conferir", icone="olho")}'
            f'{S.btn("Abrir revista", href=S.href_revista(r["id"]), tom=prim, icone="seta")}</div></div>'
        )
    bloco2 = f'<section class="card card-p"><h2>As revistas de {esc(p["nome"])}</h2><div class="rev-linhas">{linhas}</div></section>'
    return f'<div class="pilha">{bloco1}{bloco2}</div>'


def _in_corte_ficha(pid, nome, e, m, c, attr, alvo=""):
    v = corte(pid, e, c)
    return (
        f'<input class="input{"" if v else " cel-vazia"}" value="{esc(v)}" placeholder="sem corte" data-corte data-vazio data-max="{m}" {alvo} '
        f'data-rot="{e} · {c} · {esc(nome)}" aria-label="Cortes de {e} {c}" autocomplete="off" {attr}>'
    )


def _ficha_cortes(p):
    pid, nome = p["id"], p["nome"]
    attr = _atrib(pid, "dlg-impacto")
    linhas = []
    for e, m in D.ETAPAS:
        lp = corte(pid, e, "LP")
        escala = (
            f'<div data-escala id="esc-{e}" data-max="{m}">{S.escala([int(x) for x in lp.split(",")], m)}</div>'
            if lp
            else '<span class="mudo">Sem cortes de LP: a escala aparece quando houver.</span>'
        )
        linhas.append(
            [
                f'<b>{e}</b> <span class="mudo">até {m}</span><small class="mudo bloco">{ETAPA_NOME[e]}</small>',
                escala,
                _in_corte_ficha(pid, nome, e, m, "LP", attr, alvo=f'data-escala-alvo="#esc-{e}"'),
                _in_corte_ficha(pid, nome, e, m, "MT", attr),
            ]
        )
    tab = S.tabela(["Etapa", "Escala de LP", "Cortes de LP", "Cortes de MT"], linhas, cls="tab-cortes")
    regra = f'<p class="regra">{S.ic("info")}<span>De 1 a 4 cortes inteiros e crescentes, separados por vírgula; campo vazio apaga o corte.</span></p>'
    return regra + tab


def _origem_cel(ov, base="da matriz", sobre="sobrescrito", voltar="Voltar ao da matriz"):
    """Tag de origem (base x sobrescrito) + botão de voltar. ov: já está sobrescrito?"""
    return (
        f'<span class="tag tag-cobalto" data-so-ov{"" if ov else " hidden"}>{sobre}</span>'
        f'<span class="tag" data-so-base{" hidden" if ov else ""}>{base}</span>'
        f'<button type="button" class="btn btn-fan btn-sm" data-voltar{"" if ov else " hidden"} data-edita>{voltar}</button>'
    )


def _ficha_matriz(p, e):
    pid, nome = p["id"], p["nome"]
    attr_m = _atrib(pid, "dlg-impacto")
    ops = [("", "Escolha uma matriz")] + [(m["id"], m["nome"]) for m in D.MATRIZES]
    ajuda = ""
    if e["matriz"]:
        m = e["matriz"]
        ajuda = f'{pl(m["parceiros"], "parceiro usa", "parceiros usam")} esta matriz · {m["descritores"]} descritores · <a href="matriz-{m["id"]}.html">abrir a matriz</a>'
    sel = S.selecao("Matriz do parceiro", "matriz", ops, p["matriz"] or "", attrs=f'{attr_m} aria-describedby="ajuda-matriz"')
    bloco1 = (
        f'<section class="card card-p"><h2>Matriz</h2><p class="sub">Define os descritores e o passo de cada escala.</p>'
        f'<div class="campos campo-estreito">{sel}<span class="ajuda" id="ajuda-matriz">{ajuda or "Sem matriz, as revistas não montam as escalas."}</span></div></section>'
    )
    # passo da escala
    linhas = []
    for et, _ in D.ETAPAS:
        cels = []
        for c in LP_MT:
            base = PASSO_MATRIZ[et]
            ov = PASSOS_PROP.get((pid, et, c)) if e["matriz"] else None
            attr = "disabled" if (not e["matriz"] or edicao(pid)) else _atrib(pid, "dlg-impacto")
            if not e["matriz"]:
                cels.append('<span class="mudo">Escolha uma matriz para ver o passo.</span>')
                continue
            cels.append(
                f'<div class="passo-cel" data-origem-cel><input class="input" type="number" inputmode="numeric" min="1" placeholder="{base}" value="{ov or ""}" '
                f'data-ano="" data-origem aria-label="Passo da escala de {et} {c}" {attr}>{_origem_cel(bool(ov))}</div>'
            )
        linhas.append([f"<b>{et}</b>", *cels])
    bloco2 = (
        f'<section class="card card-p"><h2>Passo da escala</h2><p class="sub">De quanto em quanto a escala anda em cada etapa. Vale o da matriz, a menos que você sobrescreva.</p>'
        + S.tabela(["Etapa", "Língua Portuguesa", "Matemática"], linhas)
        + "</section>"
    )
    # Padrões do ano (cor = dado do sistema)
    prop = PADROES_PROP.get(pid, {})
    attr = _atrib(pid, "dlg-impacto")
    corpo_pad = ""
    for n, nm, cor in D.PADROES:
        nome_p, cor_p = prop.get(n, (nm, cor))
        corpo_pad += (
            f'<tr data-origem-cel><td><input class="cor-pad" type="color" value="{cor_p}" data-ano="{cor}" data-origem aria-label="Cor do Padrão 0{n}" {attr}></td>'
            f"<td>Padrão 0{n}</td>"
            f'<td><input class="input" value="{esc(nome_p)}" data-ano="{esc(nm)}" data-origem aria-label="Nome do Padrão 0{n}" autocomplete="off" {attr}></td>'
            f'<td><div class="passo-cel">{_origem_cel((nome_p, cor_p) != (nm, cor), "do ano", "sobrescrita", "Voltar ao do ano")}</div></td></tr>'
        )
    tab_pad = (
        '<div class="tab-caixa"><table class="tabela"><thead><tr><th>Cor</th><th>Padrão</th><th>Nome</th><th>Origem</th></tr></thead>'
        f"<tbody>{corpo_pad}</tbody></table></div>"
    )
    bloco3 = (
        '<section class="card card-p"><h2>Cores e nomes dos Padrões</h2>'
        f'<p class="sub">Vêm da configuração de {D.ANO}. Sobrescreva só o que {esc(nome)} usa diferente do ano.</p>{tab_pad}</section>'
    )
    return f'<div class="pilha">{bloco1}{bloco2}{bloco3}</div>'


def _ficha_variaveis(p, e):
    pid, nome = p["id"], p["nome"]
    attr = _atrib(pid, "dlg-impacto")
    grupos = []
    for v in D.VARIAVEIS:
        if not grupos or grupos[-1][0] != v[2]:
            grupos.append((v[2], []))
        grupos[-1][1].append(v)
    cards = ""
    for g, vs in grupos:
        campos = ""
        for chave, rot, _, marc, onde in vs:
            valor = valor_var(pid, chave)
            vazio = "" if valor else " cel-vazia"
            aj = f'Aparece em: {esc(onde)}' + ("" if valor else " · <b>vazio</b>: o trecho fica em branco na revista")
            campos += (
                f'<label class="campo"><span class="rot">{esc(rot)} <span class="var">{esc(marc)}</span></span>'
                f'<input class="input{vazio}" value="{esc(valor)}" placeholder="Sem valor" data-vazio autocomplete="off" {attr}>'
                f'<span class="ajuda{"" if valor else " ajuda-pend"}">{aj}</span></label>'
            )
        cards += f'<section class="card card-p"><h3>{esc(g)}</h3><div class="campos-2">{campos}</div></section>'
    aviso = ""
    if e["f_vars"]:
        aviso = S.aviso(
            f"<b>{pl(len(e['f_vars']), 'variável vazia', 'variáveis vazias')}.</b> Preencha para a revista não sair com lacunas ou copie os valores de 2025 pela planilha de Parceiros.",
            "alerta",
            acao=S.btn("Abrir a planilha", href="parceiros.html#variaveis"),
        )
    return f'<div class="pilha">{aviso}{cards}</div>'


def pagina_parceiro(p):
    pid, nome = p["id"], p["nome"]
    e = estado(pid)
    rl, rm = revistas_de(pid)
    sub = " · ".join(
        [
            f'Matriz {e["matriz"]["nome"]}' if e["matriz"] else "Sem matriz",
            f"LP ({D.FASE_NOME[rl['fase']]})",
            f"MT ({D.FASE_NOME[rm['fase']]})",
        ]
    )
    titulo = f'{esc(nome)} {S.tag(p["sigla"])} {S.tag(p["tipo"])}'
    acoes = _menu_parceiro(p)
    avisos = ""
    if not e["matriz"]:
        avisos += S.aviso(
            f"<b>Sem matriz.</b> As revistas de {esc(nome)} não montam as escalas sem uma matriz. Escolha uma na aba Matriz e cores.",
            "alerta",
            acao=S.btn("Escolher matriz", href="#matriz", attrs='data-ir-aba="matriz"'),
        )
    for r, quem in edicao(pid):
        avisos += S.aviso(
            f"<b>{esc(quem)} está editando {esc(S.nome_revista(r))}.</b> Você vê tudo, mas só grava quando ela sair da revista (o bloqueio expira em 30 s sem atividade).",
            "leitura",
            "lapis",
        )
    avisos += _aviso_imp("matriz, cortes nem variáveis")
    abas = S.abas_js([("resumo", "Resumo", None), ("cortes", "Cortes", None), ("matriz", "Matriz e cores", None), ("variaveis", "Variáveis", None)])
    corpo = (
        S.cab(titulo, esc(sub), acoes)
        + f'<div class="pilha pilha-p">{avisos}</div>'
        + abas
        + f'<section data-painel="resumo">{_resumo(p, e)}</section>'
        + f'<section data-painel="cortes">{_ficha_cortes(p)}</section>'
        + f'<section data-painel="matriz">{_ficha_matriz(p, e)}</section>'
        + f'<section data-painel="variaveis">{_ficha_variaveis(p, e)}</section>'
        + _dialogos_gerais()
        + (_dlg_impacto("dlg-impacto", pid, "a matriz, os cortes, os Padrões ou as variáveis") if validadas(pid) and not edicao(pid) else "")
    )
    return S.Pagina(S.href_parceiro(pid), nome, "parceiros", corpo, trilha=[("Parceiros", "parceiros.html"), (esc(nome), None)], status=True)


def paginas():
    return [pagina_lista()] + [pagina_parceiro(p) for p in D.PARCEIROS]


CSS = """
/* ── Parceiros ───────────────────────────────────────────────────────── */
.so-leitor{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.bloco{display:block}
.pilha{grid-template-columns:minmax(0,1fr)}
.pilha-p{gap:10px;margin-bottom:14px}
.pilha-p:empty{display:none;margin:0}
.cab h1 .tag{margin-left:6px;vertical-align:middle}
.barra-filtros{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:12px}
.barra-filtros .input{width:290px}
.barra-filtros .select{width:auto;min-width:170px}
.contagem-geral{margin-left:auto;color:var(--txt-2)}
.conta{display:inline-flex;align-items:center;gap:8px;color:var(--txt);text-decoration:none}
a.conta-pend{color:var(--alerta);font-weight:600}
a.conta:hover{text-decoration:underline}
.fase-mini{display:inline-flex;align-items:center;gap:8px;color:var(--txt);text-decoration:none}
.fase-mini small{color:var(--txt-2);font-size:12px}
a.fase-mini:hover small{text-decoration:underline}
.tabela tbody tr:nth-last-child(-n+3) .menu-lista{top:auto;bottom:calc(100% + 6px)}
.regra{display:flex;gap:8px;align-items:center;color:var(--txt-2);margin:0 0 12px}
.regra .ic{color:var(--cobalto)}
.tab-caixa.rolagem{max-height:calc(100vh - 250px);min-height:280px}
.tabela .col-fixa{position:sticky;left:0;z-index:2;background:var(--papel);min-width:190px;box-shadow:1px 0 0 var(--fio)}
.tabela thead th.col-fixa{z-index:4;background:var(--tela)}
.grade thead tr:nth-child(2) th{top:34px}
.grade td.col-fixa a.nome{display:block}
.grade td.col-fixa small{font-size:12px;line-height:1.3}
.grade .ini-grupo{border-left:1px solid var(--fio)}
.grade th.ctr{text-align:center}
.cel-corte{min-width:136px}
.cel-var{min-width:220px}
.cel-erro{outline:2px solid var(--erro);outline-offset:-2px;background:var(--erro-fundo)}
.td-conflito{background:var(--erro-fundo);vertical-align:top}
.td-conflito .cel{background:transparent;outline:2px solid var(--erro);outline-offset:-2px}
.conf{display:grid;gap:3px;padding:6px 10px 8px;font-size:12px;color:var(--erro)}
.conf small{color:var(--txt-2)}
.conf .btn{justify-self:start}
.painel-var{padding:12px 18px}
.painel-var > summary{display:flex;align-items:center;gap:8px;cursor:pointer;font-weight:650;font-size:15px;list-style:none}
.painel-var > summary::-webkit-details-marker{display:none}
.painel-var .seta{transition:transform .15s var(--ease);transform:rotate(-90deg)}
.painel-var[open] .seta{transform:none}
.painel-var > p{margin:6px 0 0}
.def-vars{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px 28px;margin-top:12px}
.def-var{display:grid;gap:1px;font-size:13px}
.card > .sub + .tab-caixa,.card > .sub + .campos,.card > .sub + .campos-2{margin-top:12px}
.rev-linhas{margin-top:6px}
.rev-linha{display:grid;grid-template-columns:minmax(190px,250px) minmax(0,1fr) auto;gap:8px 18px;align-items:center;padding:14px 0;border-top:1px solid var(--fio)}
.rev-linha:first-child{border-top:0}
.rev-id{display:grid;gap:4px}
.rev-pend{display:flex;gap:6px 8px;flex-wrap:wrap;align-items:center}
.rev-acoes{display:flex;gap:8px;justify-content:flex-end}
.tab-cortes td{vertical-align:middle}
.tab-cortes .input{min-width:150px}
.tab-cortes td:nth-child(2){width:48%}
.tab-cortes td:first-child{white-space:nowrap}
.checklist li > a.btn{flex:none;margin-left:auto}
.campo-estreito{max-width:420px}
.passo-cel{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.passo-cel .input{width:96px}
.cor-pad{width:46px;height:32px;padding:2px;border:1px solid var(--fio-2);border-radius:6px;background:var(--papel);cursor:pointer}
.cor-pad:disabled{cursor:not-allowed;opacity:.6}
.ajuda-pend{color:var(--alerta)}
.lista-imp{list-style:none;margin:0;padding:0;display:grid;max-height:280px;overflow:auto;border:1px solid var(--fio);border-radius:8px}
.lista-imp li{display:flex;align-items:center;gap:12px;flex-wrap:wrap;padding:9px 12px;border-bottom:1px solid var(--fio)}
.lista-imp li:last-child{border-bottom:0}
.lista-imp .mudo{font-size:12px}
@media (max-width:960px){
  .rev-linha{grid-template-columns:1fr}
  .rev-acoes{justify-content:flex-start}
  .def-vars{grid-template-columns:1fr}
  .contagem-geral{margin-left:0;width:100%}
  .barra-filtros .input{width:100%}
}
"""

JS = r"""
(() => {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* Cortes: 1 a 4 inteiros crescentes, abaixo da escala máxima. Valida antes do autosave/impacto. */
  function checaCortes(el) {
    const t = el.value.trim();
    if (!t) return { ok: true, vals: [] };
    const partes = t.split(",").map((s) => s.trim());
    if (partes.length > 4) return { ok: false, msg: `${partes.length} cortes passam do limite de 4. Apague os que sobram.` };
    if (!partes.every((p) => /^\d+$/.test(p))) return { ok: false, msg: "use só números inteiros separados por vírgula, como 150, 175, 200." };
    const v = partes.map(Number);
    for (let i = 1; i < v.length; i++) if (v[i] <= v[i - 1]) return { ok: false, msg: `${v[i]} não é maior que ${v[i - 1]}. Os cortes precisam crescer.` };
    const max = Number(el.dataset.max || 0);
    if (max && v[v.length - 1] >= max) return { ok: false, msg: `${v[v.length - 1]} chega ao fim da escala (${max}). Use um valor menor.` };
    return { ok: true, vals: v };
  }
  document.addEventListener("change", (e) => {
    const el = e.target;
    if (!el.matches || !el.matches("[data-corte]")) return;
    const r = checaCortes(el);
    el.classList.toggle("cel-erro", !r.ok);
    el.setAttribute("aria-invalid", String(!r.ok));
    if (!r.ok) { e.stopImmediatePropagation(); window.toast(`Cortes de ${el.dataset.rot} não gravados: ${r.msg}`); return; }
    if (r.vals.length) el.value = r.vals.join(", ");
  }, true);

  /* Células vazias: destaque e contagem ao vivo */
  function conta() {
    $$("[data-vazias]").forEach((w) => {
      const n = $$(w.dataset.vazias + ".cel-vazia").length;
      w.hidden = n === 0;
      const b = $("[data-n]", w);
      if (b) b.textContent = `${n} ${n === 1 ? w.dataset.um : w.dataset.varios}`;
    });
  }
  document.addEventListener("input", (e) => {
    const el = e.target;
    if (el.matches && el.matches("[data-vazio]")) { el.classList.toggle("cel-vazia", !el.value.trim()); conta(); }
    /* escala ao vivo (mesmo número de cortes) */
    const alvo = el.dataset && el.dataset.escalaAlvo;
    if (alvo) {
      const r = checaCortes(el), box = $(alvo);
      if (!box || !r.ok || !r.vals.length) return;
      const segs = $$(".esc-seg", box);
      if (segs.length !== r.vals.length + 1) return;
      const max = Number(box.dataset.max), pts = [0, ...r.vals, max];
      segs.forEach((s, k) => { s.style.flex = String(pts[k + 1] - pts[k]); s.title = s.title.replace(/:.*$/, `: ${pts[k]} a ${pts[k + 1]}`); });
      $$(".esc-rot span", box).forEach((sp, k) => { sp.style.left = (r.vals[k] / max * 100).toFixed(2) + "%"; sp.textContent = r.vals[k]; });
    }
    /* origem: "da matriz"/"do ano" x "sobrescrito/sobrescrita" */
    const cel = el.closest && el.closest("[data-origem-cel]");
    if (cel && el.matches("[data-origem]")) {
      const ov = $$("[data-origem]", cel).some((i) => i.value !== i.dataset.ano);
      $$("[data-so-ov],[data-voltar]", cel).forEach((x) => (x.hidden = !ov));
      $$("[data-so-base]", cel).forEach((x) => (x.hidden = ov));
    }
  });

  document.addEventListener("click", (e) => {
    const ir = e.target.closest("[data-ir-cel]");
    if (ir) {
      const alvo = $(ir.dataset.irCel);
      if (alvo) { alvo.scrollIntoView({ block: "center", inline: "center", behavior: "smooth" }); setTimeout(() => alvo.focus({ preventScroll: true }), 350); }
      return;
    }
    /* conflito: sobrescrever o valor de quem gravou antes */
    const rt = e.target.closest("[data-conflito]");
    if (rt) {
      const td = rt.closest("td"), i = $("input", td);
      i.value = rt.dataset.conflito;
      i.classList.remove("cel-conflito"); i.removeAttribute("aria-invalid");
      td.classList.remove("td-conflito");
      const c = rt.closest(".conf"); if (c) c.remove();
      const av = $("[data-aviso-conflito]"); if (av) av.hidden = true;
      window.toast("Salvo: seu valor substituiu o de Elisa Prado.");
      i.dispatchEvent(new Event("change", { bubbles: true }));
      return;
    }
    /* copiar valores vazios de 2025 */
    if (e.target.closest("[data-copiar-2025]")) {
      let ok = 0, sem = 0, ultimo = null;
      $$(".cel-var.cel-vazia").forEach((i) => {
        if (i.dataset.v25) { i.value = i.dataset.v25; i.classList.remove("cel-vazia"); ok++; ultimo = i; } else sem++;
      });
      conta();
      if (ultimo) ultimo.dispatchEvent(new Event("change", { bubbles: true }));
      window.toast(ok ? `${ok} ${ok === 1 ? "valor copiado" : "valores copiados"} de 2025.` + (sem ? ` ${sem} ${sem === 1 ? "ficou vazio" : "ficaram vazios"}: não existiam em 2025.` : "") : "Nada para copiar: esses valores não existiam em 2025.");
      return;
    }
    /* voltar ao da matriz / do ano */
    const v = e.target.closest("[data-voltar]");
    if (v) {
      const cel = v.closest("[data-origem-cel]");
      $$("[data-origem]", cel).forEach((i) => { i.value = i.dataset.ano; i.dispatchEvent(new Event("input", { bubbles: true })); i.dispatchEvent(new Event("change", { bubbles: true })); });
      return;
    }
    /* renomear e desativar: preenche o diálogo com o nome da linha */
    const nm = e.target.closest("[data-nome-atual]");
    if (nm) {
      const n = nm.dataset.nomeAtual, i = $("#dlg-renomear input[name=nome]");
      if (i) i.value = n;
      $$("[data-nome-alvo]").forEach((el) => (el.textContent = n));
    }
    const it = e.target.closest(".menu-lista button, .menu-lista a");
    if (it) { const m = it.closest("details.menu"); if (m) m.removeAttribute("open"); }
  });
})();
"""
