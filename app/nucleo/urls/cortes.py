"""Grade de cortes fora do admin (protótipo da opção B): mesma regra de `nucleo/cortes.py`.

Login (redireciona ao login do admin); ver exige `view_corte` ou `change_corte` (403);
gravar exige `add_corte` + `change_corte`, sem elas a grade é só leitura.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_http_methods, require_POST

from nucleo.cortes import grade, pode_ver
from nucleo.models import Ano, Parceiro


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
def cortes(request, ano=None):
    if not pode_ver(request.user):
        raise PermissionDenied
    anos = list(Ano.objects.order_by("-ano"))
    if ano is None:  # /cortes/ → ano mais recente
        return redirect("cortes", anos[0].ano) if anos else TemplateResponse(request, "ui/cortes.html", {"anos": anos})
    ano = get_object_or_404(Ano, ano=ano)
    contexto, gravou = grade(request, ano)
    if gravou:
        return redirect("cortes", ano.ano)
    return TemplateResponse(request, "ui/cortes.html", {**contexto, "ano": ano, "anos": anos, "secao": "cortes"})


@require_POST
@login_required(login_url="admin:login")
@permission_required("nucleo.add_parceiro", raise_exception=True)
def novo_parceiro(request, ano):
    """Nova linha da grade: o parceiro nasce sem cortes; o projeto nasce quando os cortes forem salvos."""
    form = modelform_factory(Parceiro, fields=["nome"])(request.POST)
    if form.is_valid():
        messages.success(request, f"Parceiro {form.save()} criado. Preencha os cortes da linha e salve.")
    else:
        messages.error(request, "Parceiro não criado: " + " ".join(m for erros in form.errors.values() for m in erros))
    return redirect("cortes", ano)


urlpatterns = [
    path("", cortes, name="cortes_inicio"),
    path("<int:ano>/", cortes, name="cortes"),
    path("<int:ano>/parceiro/", novo_parceiro, name="cortes_novo_parceiro"),
]
