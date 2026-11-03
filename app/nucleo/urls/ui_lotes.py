"""Lotes B (T18/T19): "Escolher matriz" e "Escolher template F1/F2" fora do admin.

U7a: a tela virou a barra de ações em massa da Lista de Projetos (`ui_projeto.massa`, que usa
`aplicar` daqui). O GET destas rotas redireciona para a Lista; o POST continua funcionando.

/ui/lotes/<ano>/matriz/ (ui_lotes_matriz) e /ui/lotes/<ano>/template/?componente= (ui_lotes_template).
Mesma regra do admin (`nucleo/lotes.py`). Ver: permissão de ver ou de alterar o modelo gravado;
sem a de alterar, só leitura e POST 403. Aplicar via HTMX devolve o próprio form (parcial) com
as mensagens oob; sem JS, PRG. Ficha: docs/telas/fichas/lotes.md; convenções: docs/telas/design-system.md.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Exists, OuterRef, Prefetch
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_http_methods

from nucleo import lotes
from nucleo.contexto import ano_da_sessao
from nucleo.models import Ano, Componente, Fasciculo, RevistaFasciculo, RevistaSecao
from nucleo.servicos.impacto import avisar_perdidos
from nucleo.ui_bloqueio import e_htmx

INVALIDO = "Nada foi gravado: corrija os erros marcados."


def permissoes(request, modelo):
    """pode_gravar; 403 se não pode nem ver, ou se é POST sem poder gravar."""
    pode_gravar = request.user.has_perm(f"nucleo.change_{modelo}")
    if not (pode_gravar or request.user.has_perm(f"nucleo.view_{modelo}")):
        raise PermissionDenied
    if request.method == "POST" and not pode_gravar:
        raise PermissionDenied
    return pode_gravar


def aplicar(request, form, gravar, novo_form, perdem_de, ano):
    """POST: grava pela regra comum. Devolve (form a mostrar, resposta de redirect ou None).
    Revista validada que perderia o "Validado" só grava com `confirmar_impacto`; sem ele, nada
    grava e `form.perdem` lista quem perde (modal de impacto, U2)."""
    form.perdem = []
    if request.method != "POST":
        return form, None
    if not form.is_valid():
        messages.error(request, INVALIDO)
        return form, None
    perdem = perdem_de(form)
    if perdem and not request.POST.get("confirmar_impacto"):
        form.perdem = perdem
        return form, None
    gravar(request, form)
    if perdem:
        avisar_perdidos(request, perdem, ano.ano)
    if e_htmx(request):
        return novo_form(), None  # tabela com os valores novos, seleção limpa
    return form, redirect("ui_projeto_lista", ano.ano)  # U7a: a lista com as ações em massa


def marcados(form):
    return {str(v) for v in (form["alvos"].value() or [])}


def responder(request, pagina, parcial, contexto):
    contexto["htmx"] = e_htmx(request)
    return TemplateResponse(request, parcial if e_htmx(request) else pagina, contexto)


@require_http_methods(["GET"])
@login_required(login_url="admin:login")
def inicio(request):
    """/ui/lotes/ → Lista de Projetos do ano da sessão (U7a); sem ano, `/`."""
    ano = ano_da_sessao(request)
    return redirect("ui_projeto_lista", ano.ano) if ano else redirect("inicio")


def para_a_lista(view):
    """U7a: o GET dos lotes vai à Lista de Projetos (barra de ações em massa); o POST continua."""
    @wraps(view)
    def envolta(request, ano):
        return view(request, ano) if request.method == "POST" else redirect("ui_projeto_lista", ano)
    return envolta


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@para_a_lista
def matriz(request, ano):
    pode_gravar = permissoes(request, "parceiroano")
    ano = get_object_or_404(Ano, ano=ano)
    novo = lambda: lotes.MatrizLoteForm(ano=ano)  # noqa: E731
    form, resposta = aplicar(
        request, lotes.MatrizLoteForm(request.POST or None, ano=ano), lotes.gravar_matriz, novo, lotes.perdem_matriz, ano
    )
    if resposta:
        return resposta
    parceiros = list(form.fields["alvos"].queryset)
    editando = lotes.em_edicao([p for pa in parceiros for p in pa.ativos])
    sel = marcados(form)
    linhas = [
        {"pa": pa, "marcado": str(pa.pk) in sel, "projeto": pa.ativos[0] if pa.ativos else None,
         "editando": next((editando[p.pk] for p in pa.ativos if p.pk in editando), "")}
        for pa in parceiros
    ]  # fmt: skip
    contexto = {
        "ano": ano, "anos": Ano.objects.order_by("-ano"), "secao": "lotes", "aba": "matriz",
        "form": form, "linhas": linhas, "pode_gravar": pode_gravar,
    }  # fmt: skip
    return responder(request, "ui/lotes/matriz.html", "ui/parciais/lotes_matriz.html", contexto)


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@para_a_lista
def template(request, ano):
    pode_gravar = permissoes(request, "revistafasciculo")
    ano = get_object_or_404(Ano, ano=ano)
    componentes = list(Componente.objects.filter(ano=ano).order_by("codigo"))
    pedido = request.GET.get("componente", "")
    componente = next((c for c in componentes if str(c.pk) == pedido), componentes[0] if componentes else None)
    contexto = {
        "ano": ano, "anos": Ano.objects.order_by("-ano"), "secao": "lotes", "aba": "template",
        "componentes": componentes, "componente": componente, "pode_gravar": pode_gravar,
    }  # fmt: skip
    if componente is None:  # ano sem componente: só o estado vazio
        return TemplateResponse(request, "ui/lotes/template.html", contexto)
    novo = lambda: lotes.TemplateLoteForm(ano=ano, componente=componente)  # noqa: E731
    form, resposta = aplicar(
        request, lotes.TemplateLoteForm(request.POST or None, ano=ano, componente=componente), lotes.gravar_template, novo,
        lotes.perdem_template, ano,
    )  # fmt: skip
    if resposta:
        return resposta
    copias = RevistaSecao.objects.filter(revista_fasciculo=OuterRef("pk"))
    fasciculos = RevistaFasciculo.objects.select_related("template").annotate(tem_copias=Exists(copias))
    revistas = list(form.fields["alvos"].queryset.prefetch_related(Prefetch("revistafasciculo_set", fasciculos)))
    editando = lotes.em_edicao([r.projeto for r in revistas])
    sel = marcados(form)
    linhas = []
    for r in revistas:
        por_fasc = {rf.fasciculo: rf for rf in r.revistafasciculo_set.all()}
        linhas.append({
            "revista": r, "marcado": str(r.pk) in sel, "editando": editando.get(r.projeto_id, ""),
            "fasciculos": [(f, por_fasc.get(f)) for f in Fasciculo.values],
        })  # fmt: skip
    contexto.update(form=form, linhas=linhas)
    return responder(request, "ui/lotes/template.html", "ui/parciais/lotes_template.html", contexto)


urlpatterns = [
    path("", inicio, name="ui_lotes_inicio"),
    path("<int:ano>/matriz/", matriz, name="ui_lotes_matriz"),
    path("<int:ano>/template/", template, name="ui_lotes_template"),
]
