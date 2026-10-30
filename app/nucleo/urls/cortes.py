"""Grade de cortes fora do admin (protótipo da opção B): mesma regra de `nucleo/cortes.py`.

Login (redireciona ao login do admin); ver exige `view_corte` ou `change_corte` (403);
gravar exige `add_corte` + `change_corte`, sem elas a grade é só leitura.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_http_methods, require_POST

from nucleo.cortes import grade, pode_ver
from nucleo.models import Ano, Parceiro, Revista
from nucleo.servicos.resolver import hash_validado
from nucleo.servicos.validacao import validada


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


class _Simulacao(Exception):
    pass


def perdem_validado(parceiro, nome):
    """Revistas ativas do parceiro (todos os anos) validadas cujo hash muda com o nome novo.
    Simula a troca numa transação desfeita: exato, sem repetir a regra do resolver."""
    revistas = list(Revista.objects.filter(projeto__parceiro_ano__parceiro=parceiro, arquivada_em__isnull=True, hash_validado__isnull=False))
    validadas = [r for r in revistas if validada(r, hash_validado(r))]
    if not validadas:
        return []
    perdem = []
    try:
        with transaction.atomic():
            Parceiro.objects.filter(pk=parceiro.pk).update(nome=nome)
            perdem = [r for r in validadas if not validada(r, hash_validado(Revista.objects.get(pk=r.pk)))]
            raise _Simulacao  # desfaz o UPDATE
    except _Simulacao:
        pass
    return perdem


@require_POST
@login_required(login_url="admin:login")
@permission_required("nucleo.change_parceiro", raise_exception=True)
def renomear_parceiro(request, ano, pk):
    """Item 6 (D-190). O nome vale para todos os anos e entra no hash (`nome_parceiro`): revista
    validada que mudaria só é afetada com a confirmação."""
    parceiro = get_object_or_404(Parceiro, pk=pk)
    antigo = parceiro.nome
    form = modelform_factory(Parceiro, fields=["nome"])(request.POST, instance=parceiro)
    if not form.is_valid():
        messages.error(request, "Parceiro não renomeado: " + " ".join(m for erros in form.errors.values() for m in erros))
        return redirect("cortes", ano)
    perdem = perdem_validado(parceiro, form.cleaned_data["nome"])
    if perdem and not request.POST.get("confirmar"):
        messages.error(
            request,
            f"Nada foi renomeado: {antigo} → {form.cleaned_data['nome']} tira o “Validado” de "
            f"{len(perdem)} revista(s): {', '.join(map(str, perdem))}. Marque a confirmação e envie de novo.",
        )
        return redirect("cortes", ano)
    form.save()
    messages.success(request, f"Parceiro renomeado para {parceiro.nome}." + (f" {len(perdem)} revista(s) perderam o “Validado”." if perdem else ""))
    return redirect("cortes", ano)


urlpatterns = [
    path("", cortes, name="cortes_inicio"),
    path("<int:ano>/", cortes, name="cortes"),
    path("<int:ano>/parceiro/", novo_parceiro, name="cortes_novo_parceiro"),
    path("<int:ano>/parceiro/<int:pk>/renomear/", renomear_parceiro, name="cortes_renomear_parceiro"),
]
