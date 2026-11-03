"""Projeto B (T15/T16: nome, variáveis, passo e cor): /ui/projeto/<pk>/, rota ui_projeto. Convenções: docs/telas/design-system.md.

Regra em `nucleo/projeto.py` (os mesmos forms do change form do admin); bloqueio pela peça comum
(`ui_bloqueio.com_bloqueio`). Hub Projetos (U7a) em /ui/projeto/ano/<ano>/: abas Lista (projetos,
revistas e ações em massa; substitui Revistas e Lotes), Cortes e Variáveis (as telas antigas, que
redirecionam o GET para cá).
"""

import re

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import F, Prefetch
from django.forms.utils import pretty_name
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from nucleo import lotes, planilha_variaveis
from nucleo.contexto import ano_da_sessao
from nucleo.lotes import escrever_travado
from nucleo.models import (
    Ano, Componente, CorPadrao, Fasciculo, Matriz, MatrizEtapaCC, ParceiroAno, Projeto, ProjetoCor, ProjetoPasso, Revista, Template,
)  # fmt: skip
from nucleo.projeto import MAX_CORES, CorForm, PassoForm, ProjetoForm, formsets
from nucleo.servicos.resolver import cores_efetivas, valores_das_variaveis
from nucleo.ui_autosave import Conflito, form_de_um_campo, responder_campo
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


def pode_ver(user):
    return user.has_perm("nucleo.view_projeto") or user.has_perm("nucleo.change_projeto")


def pode_gravar(user):
    return user.has_perms(ESCRITA)


def _alvo(request, pk, **kwargs):
    """Trava o projeto; arquivado (D-093) não trava: a view mostra só leitura."""
    projeto = get_object_or_404(Projeto, pk=pk)
    return None if projeto.arquivado_em else projeto


@require_GET
@login_required(login_url="admin:login")
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


def _linhas(ano):
    """Lista (U7a): uma linha por projeto (ativos primeiro), com as revistas como selos, mais uma por
    parceiro do ano sem projeto. A caixa de marcar (valor = ParceiroAno, o alvo dos lotes) vai na
    primeira linha de cada parceiro: o projeto ativo ou, sem ele, o mais recente."""
    projetos = list(
        Projeto.objects.filter(ano=ano)
        .select_related("parceiro_ano__parceiro", "parceiro_ano__matriz", "ano")
        .prefetch_related(Prefetch("revista_set", Revista.objects.select_related("componente", "projeto__ano", "projeto__parceiro_ano__parceiro").order_by("componente__codigo")))
        .order_by(F("arquivado_em").asc(nulls_first=True), "parceiro_ano__parceiro__nome", "-arquivado_em")
    )  # fmt: skip
    editando = lotes.em_edicao([p for p in projetos if not p.arquivado_em])
    ativos = {p.parceiro_ano_id for p in projetos if not p.arquivado_em}
    linhas, vistos = [], set()
    for p in projetos:
        selos = []
        for r in p.revista_set.all():
            if r.arquivada_em or p.arquivado_em:
                selos.append({"revista": r, "arquivada": True})
            else:
                faltas = [c["dica"] for c in painel.linha(r)["faltas"].values() if not c["ok"]]
                selos.append({"revista": r, "faltas": faltas})
        linhas.append({
            "pa": p.parceiro_ano, "projeto": p, "selos": selos, "editando": editando.get(p.pk, ""),
            "marcar": p.parceiro_ano_id not in vistos, "ativo": p.parceiro_ano_id in ativos,
        })  # fmt: skip
        vistos.add(p.parceiro_ano_id)
    sem = ParceiroAno.objects.filter(ano=ano).exclude(pk__in=vistos).select_related("parceiro", "matriz").order_by("parceiro__nome")
    linhas += [{"pa": pa, "projeto": None, "selos": [], "editando": "", "marcar": True, "ativo": False} for pa in sem]
    return linhas


def _pagina_lista(request, ano, *, post=None, acao=None, perdem=()):
    """A Lista; depois de um envio em massa recusado (erro ou impacto), com a seleção e as escolhas do envio."""
    linhas = _linhas(ano)
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
@login_required(login_url="admin:login")
def lista(request, ano):
    """Hub Projetos (U7a), aba Lista: substitui a lista de Revistas e os Lotes (ações em massa)."""
    if not pode_ver(request.user):
        raise PermissionDenied
    return _pagina_lista(request, get_object_or_404(Ano, ano=ano))


@require_POST
@login_required(login_url="admin:login")
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


def _vestir(*forms, desabilitar=False):
    """Classes do design system nos widgets, `aria-invalid` no campo com erro; só leitura: disabled.

    Linha de formset (prefixo `passos-0`): o <th> não rotula o controle, então vai `aria-label`.
    O checkbox Remover já tem <label>."""
    for f in forms:
        for nome, campo in f.fields.items():
            tipo = campo.widget.attrs.get("type") or getattr(campo.widget, "input_type", "")
            classe = {"select": "select", "checkbox": "", "color": "pj-cor"}.get(tipo, "input")
            if classe:
                campo.widget.attrs["class"] = classe
            if "-" in (f.prefix or "") and tipo not in ("checkbox", "hidden"):
                campo.widget.attrs.setdefault("aria-label", campo.label or pretty_name(nome))
            if f.is_bound and nome in f.errors:
                campo.widget.attrs["aria-invalid"] = "true"
            campo.disabled |= desabilitar


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@com_bloqueio(_alvo, pode_gravar)
def projeto(request, pk):
    if not pode_ver(request.user):
        raise PermissionDenied
    projeto = get_object_or_404(Projeto.objects.select_related("ano", "parceiro_ano__parceiro", "parceiro_ano__matriz"), pk=pk)
    arquivado = projeto.arquivado_em is not None
    if arquivado and request.method == "POST":
        raise PermissionDenied  # arquivado é congelado (D-093, D-167)
    pode = request.pode_gravar and not arquivado

    if request.method == "POST":
        form = ProjetoForm(request.POST, instance=projeto)
        passos, cores = formsets(projeto, request.POST)
        if all([form.is_valid(), passos.is_valid(), cores.is_valid()]):  # all([...]): valida os três
            form.save()
            passos.save()
            cores.save()
            messages.success(request, f"Projeto {projeto.nome} salvo.")
            return redirect("ui_projeto", projeto.pk)
        messages.error(request, "Nada foi gravado: corrija os erros marcados.")
    else:
        form = ProjetoForm(instance=projeto)
        passos, cores = formsets(projeto)
    _vestir(form, *passos.forms, *cores.forms, desabilitar=not pode)

    efetivas = cores_efetivas(projeto, projeto, MAX_CORES)  # mesma regra da revista (D-060)
    nomes = valores_das_variaveis(projeto)
    sobrescritas = {c.instance.padrao for c in cores.forms if c.instance.pk}
    contexto = {
        "projeto": projeto,
        "arquivado": arquivado,
        "pode_gravar": pode,
        "form": form,
        "tem_permissao": pode_gravar(request.user),
        "grupos": [(g, [(form[v.nome], v) for v in VARIAVEIS if v.grupo == g and not v.automatica]) for g in GRUPOS],
        "passos": passos,
        "cores": cores,
        "max_cores": MAX_CORES,
        "faixa": [
            {"padrao": k, "cor": efetivas[f"padrao-{k}"], "nome": nomes.get(f"pd{k:02d}", ""), "projeto": k in sobrescritas}
            for k in range(1, MAX_CORES + 1) if f"padrao-{k}" in efetivas
        ],
        "matrizes": Matriz.objects.filter(ano_id=projeto.ano_id).order_by("nome")
        if request.bloqueio and pode_matriz(request.user) else None,
        "passos_matriz": MatrizEtapaCC.objects.filter(matriz_id=projeto.parceiro_ano.matriz_id)
        .select_related("etapa", "componente").order_by("etapa__ordem", "componente__codigo"),
        "ano": projeto.ano,
        "secao": "projetos",
    }
    return TemplateResponse(request, "ui/projeto/projeto.html", contexto)


def pode_matriz(user):
    return user.has_perm("nucleo.change_parceiroano")


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
def matriz(request, pk):
    """GET volta à ficha: é para onde o com_bloqueio manda quem perdeu o bloqueio (o caminho do POST)."""
    if request.method == "GET":
        return redirect("ui_projeto", pk)
    return _gravar_matriz(request, pk)


@com_bloqueio(_alvo, pode_matriz)
def _gravar_matriz(request, pk):
    """Item 19 (D-190): matriz do parceiro no ano, a partir da ficha. Grava direto, sob a sessão de
    bloqueio da ficha (via com_bloqueio); `lotes.aplicar` abriria outra sessão no mesmo projeto."""
    projeto = get_object_or_404(Projeto.objects.select_related("ano", "parceiro_ano__parceiro"), pk=pk)
    if projeto.arquivado_em:
        raise PermissionDenied  # arquivado é congelado (D-093)
    escolhida = Matriz.objects.filter(pk=request.POST.get("matriz") or None, ano_id=projeto.ano_id).first()
    if escolhida is None:
        messages.error(request, f"Matriz não gravada: escolha uma matriz de {projeto.ano.ano}.")
    else:
        pa = projeto.parceiro_ano
        pa.matriz = escolhida
        pa.save(update_fields=["matriz"])
        messages.success(request, f"Matriz {escolhida.nome} escolhida para {pa.parceiro}.")
    return redirect("ui_projeto", projeto.pk)


@require_GET
@login_required(login_url="admin:login")
@com_bloqueio(_alvo, pode_gravar)
def linha(request, pk, tipo):
    """Fragmento HTMX: uma linha nova de passo ou cor, no índice TOTAL_FORMS, e o contador atualizado."""
    if tipo not in ("passos", "cores"):
        raise Http404
    if not request.pode_gravar:
        raise PermissionDenied
    projeto = get_object_or_404(Projeto, pk=pk, arquivado_em__isnull=True)
    passos, cores = formsets(projeto)
    fs = passos if tipo == "passos" else cores
    total = request.GET.get(f"{tipo}-TOTAL_FORMS", "")
    i = int(total) if total.isascii() and total.isdigit() and len(total) < 4 else fs.total_form_count()
    nova = fs.empty_form
    nova.prefix = fs.add_prefix(i)
    if tipo == "cores":
        # Sugere o primeiro padrão ainda sem cor no form, já com a cor da paleta do ano.
        usados = {request.GET.get(f"cores-{n}-padrao", "") for n in range(i)}
        livre = next((k for k in range(1, MAX_CORES + 1) if str(k) not in usados), None)
        paleta = dict(CorPadrao.objects.filter(ano_id=projeto.ano_id).values_list("padrao", "cor"))
        nova.initial = {"padrao": livre, "cor": paleta.get(livre, "#000000")}
    _vestir(nova)
    contexto = {"projeto": projeto, "f": nova, "tipo": tipo, "total": i + 1, "cheio": tipo == "cores" and i + 1 >= MAX_CORES, "nova": True}
    return TemplateResponse(request, "ui/parciais/projeto_linha.html", contexto)


LINHA = re.compile(r"^(passos|cores)-(\d{1,4})-")


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
@login_required(login_url="admin:login")
def campo(request, pk):
    """Autosave de um campo (U3), ponto único de escrita da ficha e da planilha de variáveis.
    Com a sessão de bloqueio (ficha): `com_bloqueio`, e vale todo campo da ficha. Sem ela
    (planilha): só as variáveis, e o projeto fica travado só durante a escrita (D-121)."""
    if CAMPO_SESSAO in request.POST:
        return _campo_na_ficha(request, pk)
    if not planilha_variaveis.pode_gravar(request.user):
        raise PermissionDenied
    projeto = get_object_or_404(Projeto, pk=pk)
    nome, form = _form_campo(request, projeto, EDITAVEIS)

    def gravar(dados):
        if motivo := escrever_travado(projeto, request.user, lambda: _salvar_campo(projeto.pk, nome, dados[nome])):
            raise Conflito(f"Não salvo: {motivo}. Tente de novo quando a outra pessoa fechar o projeto.")

    return responder_campo(request, form=form, gravar=gravar, revistas=lambda: _revistas(projeto), titulo=_titulo(form, nome))


@com_bloqueio(_alvo, pode_gravar)
def _campo_na_ficha(request, pk):
    projeto = get_object_or_404(Projeto, pk=pk)
    if projeto.arquivado_em:
        raise PermissionDenied  # arquivado é congelado (D-093, D-167)
    if m := LINHA.match(request.POST.get("campo", "")):
        return _linha_na_ficha(request, projeto, *m.groups())
    nome, form = _form_campo(request, projeto, ProjetoForm._meta.fields)
    gravar = lambda dados: _salvar_campo(projeto.pk, nome, dados[nome])  # noqa: E731
    return responder_campo(request, form=form, gravar=gravar, revistas=lambda: _revistas(projeto), titulo=_titulo(form, nome))


def _linha_na_ficha(request, projeto, tipo, i):
    """Linha de passo ou de cor (a linha inteira vem no POST, com o prefixo do formset da página).
    Sem `id`: cria (a resposta leva o `id`). Com `DELETE`: remove (volta ao valor da matriz/do ano)."""
    prefixo = f"{tipo}-{i}"
    Modelo, Form = (ProjetoPasso, PassoForm) if tipo == "passos" else (ProjetoCor, CorForm)
    pk_linha = request.POST.get(f"{prefixo}-id", "")
    if pk_linha and not (pk_linha.isascii() and pk_linha.isdigit()):
        raise Http404
    instancia = get_object_or_404(Modelo, pk=pk_linha, projeto=projeto) if pk_linha else Modelo(projeto=projeto)
    revistas = lambda: _revistas(projeto)  # noqa: E731
    titulo = "Salvar o passo" if tipo == "passos" else "Salvar a cor"
    if request.POST.get(f"{prefixo}-DELETE"):
        def remover(_):
            if instancia.pk:
                Modelo.objects.filter(pk=instancia.pk).delete()
            return {"removida": True}

        return responder_campo(request, form=forms.Form({}), gravar=remover, revistas=revistas, titulo="Remover a linha")
    kwargs = {"ano_id": projeto.ano_id} if tipo == "passos" else {}
    form = Form(request.POST, instance=instancia, prefix=prefixo, **kwargs)

    def gravar(_):
        obj = form.save(commit=False)
        if not pk_linha:  # a simulação do impacto (savepoint desfeito) já deu um pk a esta instância
            obj.pk, obj._state.adding = None, True
        obj.save()
        return {"id": obj.pk}

    return responder_campo(request, form=form, gravar=gravar, revistas=revistas, titulo=titulo)


urlpatterns = [
    path("", inicio, name="ui_projeto_inicio"),
    path("ano/<int:ano>/", lista, name="ui_projeto_lista"),
    # Abas Cortes e Variáveis (U7a): herdam os nomes das telas antigas, que agora redirecionam para cá.
    path("ano/<int:ano>/cortes/", aba_cortes.cortes, name="cortes"),
    path("ano/<int:ano>/variaveis/", aba_variaveis.variaveis, name="ui_variaveis"),
    path("ano/<int:ano>/massa/<str:acao>/", massa, name="ui_projeto_massa"),
    path("<int:pk>/", projeto, name="ui_projeto"),
    path("<int:pk>/linha/<str:tipo>/", linha, name="ui_projeto_linha"),
    path("<int:pk>/campo/", campo, name="ui_projeto_campo"),
    path("<int:pk>/matriz/", matriz, name="ui_projeto_matriz"),
]
