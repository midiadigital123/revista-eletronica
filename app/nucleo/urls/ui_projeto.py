"""Projeto B (T15/T16: nome, variáveis, passo e cor): /ui/projeto/<pk>/, rota ui_projeto. Convenções: docs/telas/design-system.md.

Regra em `nucleo/projeto.py` (os mesmos forms do change form do admin); bloqueio pela peça comum
(`ui_bloqueio.com_bloqueio`). Abas do projeto (U7b, `?aba=`): Dados, Matriz, Cortes, Passos e cores e
Revistas. Hub Projetos (U7a) em /ui/projeto/ano/<ano>/: abas Lista (projetos,
revistas e ações em massa; substitui Revistas e Lotes), Cortes e Variáveis (as telas antigas, que
redirecionam o GET para cá).
"""

import re

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F, Prefetch
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from nucleo import cortes as regra_cortes
from nucleo import lotes, planilha_variaveis
from nucleo.contexto import ano_da_sessao
from nucleo.lotes import escrever_travado
from nucleo.models import (
    Ano, Componente, CorPadrao, Etapa, Fasciculo, Matriz, MatrizEtapaCC, ParceiroAno, Projeto, ProjetoCor, ProjetoPasso, Revista,
    Template,
)  # fmt: skip
from nucleo.projeto import MAX_CORES, ProjetoForm
from nucleo.servicos import matriz as matrizes
from nucleo.servicos.resolver import valores_das_variaveis
from nucleo.ui_autosave import Conflito, form_de_um_campo, responder_campo
from nucleo.ui_autosave import erros as erros_campo
from nucleo.ui_bloqueio import CAMPO_SESSAO, com_bloqueio
from nucleo.urls import cortes as aba_cortes
from nucleo.urls import painel, ui_lotes
from nucleo.urls import ui_variaveis as aba_variaveis
from nucleo.variaveis import EDITAVEIS, VARIAVEIS

# ponytail: exige também add/change/delete de passo e cor (os perfis dão tudo junto); o admin
# deixaria quem só tem change_projeto editar nome e variáveis. Separar se surgir esse perfil.
ESCRITA = [f"nucleo.{a}_{m}" for m in ("projetopasso", "projetocor") for a in ("add", "change", "delete")]
ESCRITA.append("nucleo.change_projeto")
GRUPOS = list(dict.fromkeys(v.grupo for v in VARIAVEIS if not v.automatica))
ABAS = [("dados", "Dados"), ("matriz", "Matriz"), ("cortes", "Cortes"), ("passos", "Passos e cores"), ("revistas", "Revistas")]


def pode_ver(user):
    return user.has_perm("nucleo.view_projeto") or user.has_perm("nucleo.change_projeto")


def pode_gravar(user):
    return user.has_perms(ESCRITA)


def _alvo(request, pk, **kwargs):
    """Trava o projeto; arquivado (D-093) não trava: a view mostra só leitura."""
    projeto = get_object_or_404(Projeto, pk=pk)
    return None if projeto.arquivado_em else projeto


@require_GET
@login_required
def inicio(request):
    """Ano da sessão; sem ano nenhum, a página vazia com o caminho para abrir um (U7a: é para cá que
    as rotas `_inicio` de Cortes, Variáveis, Revistas e Lotes mandam)."""
    ano = ano_da_sessao(request)
    if ano:
        return redirect("ui_projeto_lista", ano.ano)
    return TemplateResponse(request, "ui/projeto/lista.html", {"ano": None, "secao": "projetos"})


def pode_massa(user):
    """(matriz, template): quem vê a barra de ações em massa da Lista (as permissões dos Lotes)."""
    return user.has_perm("nucleo.change_parceiroano"), user.has_perm("nucleo.change_revistafasciculo")


def _linhas(ano, usuario):
    """Lista (U7a): uma linha por projeto (ativos primeiro), com uma sublinha por revista, mais uma por
    parceiro do ano sem projeto. A caixa de marcar (valor = ParceiroAno, o alvo dos lotes) vai na
    primeira linha de cada parceiro: o projeto ativo ou, sem ele, o mais recente."""
    projetos = list(
        Projeto.objects.filter(ano=ano)
        .select_related("parceiro_ano__parceiro", "parceiro_ano__matriz", "ano")
        .prefetch_related(Prefetch("revista_set", Revista.objects.select_related("componente", "projeto__ano", "projeto__parceiro_ano__parceiro").order_by("componente__codigo")))
        .order_by(F("arquivado_em").asc(nulls_first=True), "parceiro_ano__parceiro__nome", "-arquivado_em")
    )  # fmt: skip
    editando = lotes.em_edicao([p for p in projetos if not p.arquivado_em], usuario)
    ativos = {p.parceiro_ano_id for p in projetos if not p.arquivado_em}
    linhas, vistos = [], set()
    for p in projetos:
        revistas = []
        for r in p.revista_set.all():
            if r.arquivada_em or p.arquivado_em:
                revistas.append({"revista": r, "arquivada": True})
            else:
                cel = painel.linha(r)["faltas"]
                # Balão = o que falta preparar; Validado e Impresso são etapas, e vão para a Situação.
                faltas = [c["dica"] for k, c in cel.items() if k not in ("validado", "impresso") and not c["ok"]]
                situacao = ("Em preparo" if faltas else "Pronta para validar" if not cel["validado"]["ok"]
                            else "Validada" if not cel["impresso"]["ok"] else "Impressa")
                tag = {"Em preparo": "", "Pronta para validar": "tag-ambar", "Validada": "tag-azul", "Impressa": "tag-verde"}[situacao]
                revistas.append({"revista": r, "faltas": faltas, "situacao": situacao, "situacao_tag": tag})
        linhas.append({
            "pa": p.parceiro_ano, "projeto": p, "revistas": revistas, "editando": editando.get(p.pk, ""),
            "marcar": p.parceiro_ano_id not in vistos, "ativo": p.parceiro_ano_id in ativos,
        })  # fmt: skip
        vistos.add(p.parceiro_ano_id)
    sem = ParceiroAno.objects.filter(ano=ano).exclude(pk__in=vistos).select_related("parceiro", "matriz").order_by("parceiro__nome")
    linhas += [{"pa": pa, "projeto": None, "revistas": [], "editando": "", "marcar": True, "ativo": False} for pa in sem]
    return linhas


def _pagina_lista(request, ano, *, post=None, acao=None, perdem=()):
    """A Lista; depois de um envio em massa recusado (erro ou impacto), com a seleção e as escolhas do envio."""
    linhas = _linhas(ano, request.user)
    marcados = set(post.getlist("alvos")) if post else set()
    for l in linhas:
        l["marcado"] = str(l["pa"].pk) in marcados
    p_matriz, p_template = pode_massa(request.user)
    contexto = {
        "ano": ano, "anos": Ano.objects.order_by("-ano"), "secao": "projetos", "aba": "lista", "linhas": linhas,
        "pode_matriz": p_matriz, "pode_template": p_template, "pode_massa": p_matriz or p_template,
        "marcados": sum(l["marcado"] for l in linhas),
        "matrizes": Matriz.objects.filter(ano=ano).order_by("nome") if p_matriz else (),
        "componentes": Componente.objects.filter(ano=ano).order_by("codigo") if p_template else (),
        "templates": Template.objects.filter(ano=ano).select_related("componente").order_by("componente__codigo", "fasciculo", "nome")
        if p_template else (),
        "escolha": {k: (post or {}).get(k, "") for k in ("matriz", "componente")},
        "fasciculos": [(f, f"template_{f.lower()}", (post or {}).get(f"template_{f.lower()}", "")) for f in Fasciculo.values],
        "acao": acao, "perdem": perdem, "acao_titulo": {"matriz": "Atribuir matriz", "template": "Atribuir template"}.get(acao),
    }  # fmt: skip
    return TemplateResponse(request, "ui/projeto/lista.html", contexto)


@require_GET
@login_required
def lista(request, ano):
    """Hub Projetos (U7a), aba Lista: substitui a lista de Revistas e os Lotes (ações em massa)."""
    if not pode_ver(request.user):
        raise PermissionDenied
    return _pagina_lista(request, get_object_or_404(Ano, ano=ano))


@require_POST
@login_required
def massa(request, ano, acao):
    """Barra da Lista (U7a): "Atribuir matriz…" e "Atribuir template…" aos parceiros marcados
    (`alvos` = ParceiroAno). Mesma regra dos Lotes (`nucleo/lotes.py`): projeto em edição é pulado e
    listado, e quem perde o "Validado" passa pelo modal de impacto (U2) antes de gravar."""
    if acao not in ("matriz", "template"):
        raise Http404
    ano = get_object_or_404(Ano, ano=ano)
    if not pode_massa(request.user)[acao == "template"]:
        raise PermissionDenied
    if acao == "matriz":
        form, gravar, perdem_de = lotes.MatrizLoteForm(request.POST, ano=ano), lotes.gravar_matriz, lotes.perdem_matriz
    else:
        componente = Componente.objects.filter(ano=ano, pk=_pk(request.POST.get("componente"))).first()
        if componente is None:
            messages.error(request, "Nada foi gravado: Escolha o componente.")
            return _pagina_lista(request, ano, post=request.POST)
        dados = request.POST.copy()  # alvos: parceiros → as revistas ativas deles neste componente
        pas = [_pk(v) for v in request.POST.getlist("alvos")]
        dados.setlist("alvos", Revista.objects.filter(projeto__parceiro_ano__in=[p for p in pas if p], componente=componente,
                                                      arquivada_em__isnull=True, projeto__arquivado_em__isnull=True).values_list("pk", flat=True))
        form, gravar, perdem_de = lotes.TemplateLoteForm(dados, ano=ano, componente=componente), lotes.gravar_template, lotes.perdem_template
    form, resposta = ui_lotes.aplicar(request, form, gravar, None, perdem_de, ano)
    if resposta:
        return resposta
    for erro in (e for erros in form.errors.values() for e in erros):
        messages.error(request, erro)
    return _pagina_lista(request, ano, post=request.POST, acao=acao, perdem=form.perdem)


def _pk(valor):
    return int(valor) if valor and valor.isascii() and valor.isdigit() and len(valor) < 10 else None


def _vestir(form, desabilitar=False):
    """Classe do design system nos widgets, `aria-invalid` no campo com erro; só leitura: disabled."""
    for nome, campo in form.fields.items():
        campo.widget.attrs["class"] = "input"
        if form.is_bound and nome in form.errors:
            campo.widget.attrs["aria-invalid"] = "true"
        campo.disabled |= desabilitar


@require_http_methods(["GET", "POST"])
@login_required
@com_bloqueio(_alvo, pode_gravar)
def projeto(request, pk):
    if not pode_ver(request.user):
        raise PermissionDenied
    projeto = get_object_or_404(Projeto.objects.select_related("ano", "parceiro_ano__parceiro", "parceiro_ano__matriz"), pk=pk)
    arquivado = projeto.arquivado_em is not None
    if arquivado and request.method == "POST":
        raise PermissionDenied  # arquivado é congelado (D-093, D-167)
    pode = request.pode_gravar and not arquivado

    aba = request.GET.get("aba") if request.GET.get("aba") in dict(ABAS) else "dados"
    # O POST da página só leva nome e variáveis; passo e cor gravam pelo autosave (`campo`).
    form = ProjetoForm(request.POST if request.method == "POST" else None, instance=projeto)
    if form.is_bound:
        if form.is_valid():
            form.save()
            messages.success(request, f"Projeto {projeto.nome} salvo.")
            return redirect("ui_projeto", projeto.pk)
        messages.error(request, "Nada foi gravado: corrija os erros marcados.")
    _vestir(form, desabilitar=not pode)

    contexto = {
        "projeto": projeto,
        "arquivado": arquivado,
        "pode_gravar": pode,
        "form": form,
        "tem_permissao": pode_gravar(request.user),
        "grupos": [(g, [(form[v.nome], v) for v in VARIAVEIS if v.grupo == g and not v.automatica]) for g in GRUPOS],
        "revistas_ativas": _revistas(projeto).select_related("componente").order_by("componente__codigo"),
        "matrizes": Matriz.objects.filter(ano_id=projeto.ano_id).order_by("nome")
        if request.bloqueio and pode_matriz(request.user) else None,
        "passos_matriz": MatrizEtapaCC.objects.filter(matriz_id=projeto.parceiro_ano.matriz_id)
        .select_related("etapa", "componente").order_by("etapa__ordem", "componente__codigo"),
        "ano": projeto.ano,
        "secao": "projetos",
        "abas": ABAS,
        "aba": aba,
    }
    if aba == "passos":
        contexto["etapas_passo"] = _passos(projeto)
        contexto["amostras"] = _amostras(projeto)
    elif aba == "cortes":
        contexto["grade"] = _grade_do_parceiro(request, projeto)
    elif aba == "revistas":
        contexto["cartoes"] = _cartoes(projeto)
    return TemplateResponse(request, "ui/projeto/projeto.html", contexto)


def _passos(projeto):
    """Aba Passos e cores: um bloco por etapa do ano, com uma célula por componente. Cada célula traz
    o passo da matriz (o herdado) e a sobrescrita do projeto, se houver (D-053, D-091): sem linha =
    herda; linha com passo nulo = sem linhas vazias, de propósito."""
    matriz = {
        (m.etapa_id, m.componente_id): m.passo
        for m in MatrizEtapaCC.objects.filter(matriz_id=projeto.parceiro_ano.matriz_id)
    }
    proprios = {(p.etapa_id, p.componente_id): p.passo for p in ProjetoPasso.objects.filter(projeto=projeto)}
    componentes = list(Componente.objects.filter(ano_id=projeto.ano_id).order_by("codigo"))

    def celula(e, c):
        k = (e.pk, c.pk)
        da_matriz = "fora da matriz" if k not in matriz else matriz[k] or "sem linhas vazias"
        return {
            "chave": f"{e.pk}-{c.pk}", "componente": c, "matriz": matriz.get(k), "da_matriz": da_matriz,
            "sobrescrito": k in proprios, "passo": proprios.get(k), "sem_vazias": k in proprios and proprios[k] is None,
        }  # fmt: skip

    etapas = Etapa.objects.filter(ano_id=projeto.ano_id).order_by("ordem")
    return [{"etapa": e, "celulas": [celula(e, c) for c in componentes]} for e in etapas]


def _amostras(projeto):
    """Aba Passos e cores: uma amostra por padrão do ano, com a cor efetiva (do projeto, senão do ano:
    D-060) e o nome efetivo (`pdNN`, senão o nome do ano: D-175)."""
    proprias = dict(ProjetoCor.objects.filter(projeto=projeto).values_list("padrao", "cor"))
    nomes = valores_das_variaveis(projeto)
    return [
        {"padrao": cp.padrao, "nome": nomes.get(f"pd{cp.padrao:02d}", ""),
         "cor_ano": cp.cor.lower(), "cor": proprias.get(cp.padrao, cp.cor).lower(), "sobrescrita": cp.padrao in proprias}
        for cp in CorPadrao.objects.filter(ano_id=projeto.ano_id, padrao__lte=MAX_CORES).order_by("padrao")
    ]  # fmt: skip


def _grade_do_parceiro(request, projeto):
    """Aba Cortes (U7b): a grade do ano (`cortes.grade`) só com a linha deste parceiro; grava pela
    mesma rota da grade (`cortes_celula`, sem bloqueio: conflito otimista pelo `original`)."""
    grade, _ = regra_cortes.grade(request, projeto.ano, ler_post=False)
    grade["linhas"] = [l for l in grade["linhas"] if l["parceiro"].pk == projeto.parceiro_ano.parceiro_id]
    # Um parceiro só: a grade transposta, um bloco por etapa com os componentes lado a lado.
    grade["blocos"] = []
    for linha in grade["linhas"]:
        for (e, c), cel in zip(grade["colunas"], linha["celulas"]):
            if not grade["blocos"] or grade["blocos"][-1]["etapa"] != e:
                grade["blocos"].append({"etapa": e, "campos": []})
            grade["blocos"][-1]["campos"].append((c, cel))
    return grade


def _cartoes(projeto):
    """Aba Revistas (U7b): um cartão por componente com templates F1/F2, SVG, capa e "Validado"
    (a situação do painel); a página da revista continua sendo onde se edita."""
    cartoes = []
    revistas = projeto.revista_set.select_related("componente", "projeto__ano", "projeto__parceiro_ano__parceiro")
    for r in revistas.prefetch_related("revistafasciculo_set__template").order_by("componente__codigo"):
        templates = {rf.fasciculo: rf.template for rf in r.revistafasciculo_set.all()}
        ativa = not (r.arquivada_em or projeto.arquivado_em)
        faltas = painel.linha(r)["faltas"] if ativa else None
        cartoes.append({
            "revista": r, "ativa": ativa, "faltas": faltas,
            "templates": [(f, templates.get(f)) for f in Fasciculo.values],
        })  # fmt: skip
    return cartoes


def pode_matriz(user):
    return user.has_perm("nucleo.change_parceiroano")


@require_http_methods(["GET", "POST"])
@login_required
def matriz(request, pk):
    """GET volta à aba Matriz: é para onde o com_bloqueio manda quem perdeu o bloqueio (o caminho do POST)."""
    if request.method == "GET":
        return redirect(reverse("ui_projeto", args=[pk]) + "?aba=matriz")
    return _gravar_matriz(request, pk)


class MatrizForm(forms.Form):
    matriz = forms.ModelChoiceField(queryset=None, label="Matriz")

    def __init__(self, *args, ano, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["matriz"].queryset = Matriz.objects.filter(ano=ano)
        erro = f"Escolha uma matriz de {ano.ano}."
        self.fields["matriz"].error_messages.update(required=erro, invalid_choice=erro)


@com_bloqueio(_alvo, pode_matriz)
def _gravar_matriz(request, pk):
    """Aba Matriz (U7b): autosave do select (protocolo de `ui_autosave`), sob a sessão de bloqueio da
    ficha. Revista validada que mudaria passa pelo modal de impacto antes de gravar. Grava por
    `servicos.matriz.atribuir_matriz`, o mesmo serviço da ação em massa da Lista."""
    projeto = get_object_or_404(Projeto.objects.select_related("ano", "parceiro_ano"), pk=pk)
    if projeto.arquivado_em:
        raise PermissionDenied  # arquivado é congelado (D-093)
    form = MatrizForm({"matriz": request.POST.get("valor")}, ano=projeto.ano) if request.POST.get("campo") == "matriz" else None
    pa = projeto.parceiro_ano
    gravar = lambda dados: matrizes.atribuir_matriz(pa, dados["matriz"], request.user)  # noqa: E731
    return responder_campo(request, form=form, gravar=gravar, revistas=lambda: _revistas(projeto), titulo="Trocar a matriz")


PASSO = re.compile(r"^(passo|sem)-(\d{1,9})-(\d{1,9})$")  # célula etapa × componente da aba Passos e cores
COR = re.compile(r"^cor-(\d)$")  # amostra do padrão


def _revistas(projeto):
    return Revista.objects.filter(projeto=projeto, arquivada_em__isnull=True)


def _salvar_campo(pk, nome, valor):
    projeto = Projeto.objects.get(pk=pk)  # relido: o form mexeu na instância da view
    setattr(projeto, nome, valor)
    projeto.save(update_fields=[nome])


def _form_campo(request, projeto, nomes):
    nome = request.POST.get("campo", "")
    if nome not in nomes:
        return nome, None
    return nome, form_de_um_campo(ProjetoForm, nome, request.POST.get("valor", ""), instance=projeto)


def _titulo(form, nome):
    return f"Salvar “{form.fields[nome].label}”" if form else "Salvar"


@require_POST
@login_required
def campo(request, pk):
    """Autosave de um campo (U3), ponto único de escrita da ficha e da planilha de variáveis.
    Com a sessão de bloqueio (ficha): `com_bloqueio`, e vale todo campo da ficha. Sem ela
    (planilha): só as variáveis, e o projeto fica travado só durante a escrita (D-121). Sem bloqueio
    de página, duas abas na planilha são resolvidas como na grade de Cortes: `original` diferente do
    gravado é 409 com `atual`, sem gravar (U10d)."""
    if CAMPO_SESSAO in request.POST:
        return _campo_na_ficha(request, pk)
    if not planilha_variaveis.pode_gravar(request.user):
        raise PermissionDenied
    projeto = get_object_or_404(Projeto, pk=pk)
    nome, form = _form_campo(request, projeto, EDITAVEIS)
    original = request.POST.get("original", "")

    def gravar(dados):
        mudou = []

        def escrever():  # sob a trava do projeto (select_for_update em escrever_travado): relê e compara
            if (atual := getattr(Projeto.objects.get(pk=projeto.pk), nome)) != original:
                mudou.append(atual)
                return "mudou"
            _salvar_campo(projeto.pk, nome, dados[nome])

        if motivo := escrever_travado(projeto, request.user, escrever):
            if mudou:
                raise Conflito(
                    f"{projeto.parceiro_ano.parceiro}: outra pessoa mudou este valor depois que a página abriu "
                    f"(agora: {mudou[0] or 'vazio'}). Seu valor ficou na célula; Tentar de novo grava por cima.",
                    mudou[0],
                )
            raise Conflito(f"Não salvo: {motivo}. Tente de novo quando a outra pessoa fechar o projeto.")
        return {"valor": dados[nome]}

    return responder_campo(request, form=form, gravar=gravar, revistas=lambda: _revistas(projeto), titulo=_titulo(form, nome))


@com_bloqueio(_alvo, pode_gravar)
def _campo_na_ficha(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    if projeto.arquivado_em:
        raise PermissionDenied  # arquivado é congelado (D-093, D-167)
    if m := PASSO.match(request.POST.get("campo", "")):
        return _passo_na_ficha(request, projeto, *m.groups())
    if m := COR.match(request.POST.get("campo", "")):
        return _cor_na_ficha(request, projeto, int(m[1]))
    nome, form = _form_campo(request, projeto, ProjetoForm._meta.fields)
    gravar = lambda dados: _salvar_campo(projeto.pk, nome, dados[nome])  # noqa: E731
    return responder_campo(request, form=form, gravar=gravar, revistas=lambda: _revistas(projeto), titulo=_titulo(form, nome))


class _PassoForm(forms.Form):
    valor = forms.IntegerField(required=False, min_value=1, label="Passo")


class _CorForm(forms.Form):
    valor = forms.RegexField(r"^#[0-9A-Fa-f]{6}$", label="Cor", error_messages={"invalid": "Use uma cor no formato #RRGGBB."})


def _passo_na_ficha(request, projeto, tipo, etapa_pk, componente_pk):
    """Célula de passo: `passo-E-C` com um número sobrescreve; vazio volta ao passo da matriz.
    `sem-E-C` marcado = "sem linhas vazias" (a linha existe com passo nulo, D-091); desmarcado volta à matriz."""
    filtro = {
        "projeto": projeto,
        "etapa": get_object_or_404(Etapa, pk=etapa_pk, ano_id=projeto.ano_id),
        "componente": get_object_or_404(Componente, pk=componente_pk, ano_id=projeto.ano_id),
    }
    valor = request.POST.get("valor", "").strip()
    form = _PassoForm({"valor": valor}) if tipo == "passo" else forms.Form({})

    def gravar(dados):
        herdar = dados["valor"] is None if tipo == "passo" else valor != "on"
        if herdar:
            for linha in ProjetoPasso.objects.filter(**filtro):
                linha.delete()  # um a um: o histórico registra
            return {}
        passo = dados["valor"] if tipo == "passo" else None
        ProjetoPasso.objects.update_or_create(**filtro, defaults={"passo": passo, "ano_id": projeto.ano_id})
        return {}

    return responder_campo(request, form=form, gravar=gravar, revistas=lambda: _revistas(projeto), titulo="Salvar o passo")


def _cor_na_ficha(request, projeto, padrao):
    """Amostra do padrão: a cor escolhida sobrescreve a do ano; a própria cor do ano apaga a
    sobrescrita ("Voltar à cor do ano"). Só a caixa diferente não é mudança: o seletor do navegador
    manda minúsculas e a carga gravou maiúsculas (trocar a caixa mudaria o hash da revista)."""
    do_ano = CorPadrao.objects.filter(ano_id=projeto.ano_id, padrao=padrao).values_list("cor", flat=True).first()
    if do_ano is None:
        return erros_campo(["Este padrão não existe no ano. Recarregue a página."])
    form = _CorForm({"valor": request.POST.get("valor", "").strip()})

    def gravar(dados):
        cor = dados["valor"].lower()
        atual = ProjetoCor.objects.filter(projeto=projeto, padrao=padrao).first()
        if cor == do_ano.lower():
            if atual:
                atual.delete()
        elif atual is None:
            ProjetoCor.objects.create(projeto=projeto, padrao=padrao, cor=cor)
        elif atual.cor.lower() != cor:
            atual.cor = cor
            atual.save(update_fields=["cor"])
        return {}

    return responder_campo(request, form=form, gravar=gravar, revistas=lambda: _revistas(projeto), titulo="Salvar a cor")


urlpatterns = [
    path("", inicio, name="ui_projeto_inicio"),
    path("ano/<int:ano>/", lista, name="ui_projeto_lista"),
    # Abas Cortes e Variáveis (U7a): herdam os nomes das telas antigas, que agora redirecionam para cá.
    path("ano/<int:ano>/cortes/", aba_cortes.cortes, name="cortes"),
    path("ano/<int:ano>/variaveis/", aba_variaveis.variaveis, name="ui_variaveis"),
    path("ano/<int:ano>/massa/<str:acao>/", massa, name="ui_projeto_massa"),
    path("<int:pk>/", projeto, name="ui_projeto"),
    path("<int:pk>/campo/", campo, name="ui_projeto_campo"),
    path("<int:pk>/matriz/", matriz, name="ui_projeto_matriz"),
]
