"""Planilha de variáveis B (T17): /ui/variaveis/<ano>/, rota ui_variaveis. Convenções: docs/telas/design-system.md.

Mesma regra da aba Variáveis do admin (`nucleo/planilha_variaveis.py`). Login (vai ao login do
admin); ver exige `view_projeto` ou `change_projeto` (403); gravar e copiar exigem `change_projeto`,
sem ela a planilha é só leitura. Cada projeto grava com o bloqueio dele; travado é pulado (D-121).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_POST, require_http_methods

from nucleo.models import Ano
from nucleo.planilha_variaveis import VariaveisForm, copiar, pk_do_post, planilha, pode_gravar, pode_ver, projetos_do_ano
from nucleo.ui_bloqueio import e_htmx
from nucleo.variaveis import VARIAVEIS

# Colunas agrupadas como os fieldsets do form do projeto (ordem da 1ª aparição do grupo).
_GRUPOS = list(dict.fromkeys(v.grupo for v in VARIAVEIS if not v.automatica))
COLUNAS = sorted((v for v in VARIAVEIS if not v.automatica), key=lambda v: _GRUPOS.index(v.grupo))
GRUPOS = [(g, sum(v.grupo == g for v in COLUNAS)) for g in _GRUPOS]
INICIOS = {next(v.nome for v in COLUNAS if v.grupo == g) for g in _GRUPOS}  # 1ª coluna do grupo: borda


def celulas(form):
    """Campos da linha na ordem das colunas, com os atributos da grade (classe, rótulo, erro)."""
    saida = []
    for v in COLUNAS:
        campo = form[v.nome]
        attrs = campo.field.widget.attrs
        attrs.pop("size", None)
        attrs.update({"class": "input", "autocomplete": "off", "aria-label": f"{form.instance} {v.rotulo}"})
        if campo.errors:
            attrs["aria-invalid"] = "true"
        saida.append({"campo": campo, "inicio": v.nome in INICIOS})
    return saida


def erros(form):
    rotulos = {v.nome: v.rotulo for v in COLUNAS}
    return [f"{rotulos.get(nome, nome)}: {e}" for nome, lista in form.errors.items() for e in lista]


def linha(form, indice):
    return {"form": form, "indice": indice, "celulas": celulas(form), "erros": erros(form)}


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
def variaveis(request, ano=None):
    if not pode_ver(request.user):
        raise PermissionDenied
    anos = list(Ano.objects.order_by("-ano"))
    if ano is None:  # /ui/variaveis/ → ano mais recente
        if anos:
            return redirect("ui_variaveis", anos[0].ano)
        return TemplateResponse(request, "ui/variaveis/pagina.html", {"anos": anos, "secao": "variaveis"})
    ano = get_object_or_404(Ano, ano=ano)
    contexto, gravou = planilha(request, ano)
    if gravou:
        return redirect("ui_variaveis", ano.ano)
    formset = contexto["formset"]
    if formset.is_bound:  # chegou aqui com POST = formset inválido
        messages.error(request, "Nada foi gravado: corrija os erros marcados.")
    return TemplateResponse(
        request,
        "ui/variaveis/pagina.html",
        {
            **contexto,
            "linhas": [linha(f, i) for i, f in enumerate(formset.forms)],
            "colunas": COLUNAS, "grupos": GRUPOS, "cabecalho": [(v, v.nome in INICIOS) for v in COLUNAS],
            "ano": ano, "anos": anos, "secao": "variaveis",
        },
    )  # fmt: skip


@require_POST
@login_required(login_url="admin:login")
def copiar_linha(request, ano, pk):
    """Copia do ano anterior (só vazias) e devolve a linha nova (HTMX) ou volta à página."""
    if not pode_gravar(request.user):
        raise PermissionDenied
    copiar(request, pk)
    if not e_htmx(request):
        return redirect("ui_variaveis", ano)
    projeto = projetos_do_ano(get_object_or_404(Ano, ano=ano)).filter(pk=pk).first()
    indice = pk_do_post(request.GET.get("i", ""))
    if projeto is None or indice >= 1000:  # sumiu ou arquivou: a mensagem sai na página recarregada
        return HttpResponse(headers={"HX-Refresh": "true"})
    # Mesmo prefixo da linha na página ("form-<i>"): o "initial-" novo vira o original do formset.
    form = VariaveisForm(instance=projeto, prefix=f"form-{indice}")
    return TemplateResponse(
        request,
        "ui/parciais/variaveis_linha.html",
        {"l": linha(form, indice), "ano": projeto.ano, "pode_editar": True, "colunas": COLUNAS, "oob": True},
    )


urlpatterns = [
    path("", variaveis, name="ui_variaveis_inicio"),
    path("<int:ano>/", variaveis, name="ui_variaveis"),
    path("<int:ano>/copiar/<int:pk>/", copiar_linha, name="ui_variaveis_copiar"),
]
