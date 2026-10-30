"""Validar B (T24 em lote e o Validado 1 a 1 de T21): /ui/validar/<ano>/, rota ui_validar. Convenções: docs/telas/design-system.md.

Mesma regra do admin (`urls/painel.py`: `itens_validar`, `validar_pares`). Login (vai ao login do
admin); ver exige `view_revista` (403); validar exige `validar_revista`, sem ela é só leitura e o
POST dá 403. Sem `com_bloqueio`: é lote, cada revista trava o projeto só ao gravar (D-121).
"Validar esta" (campo `so`) grava um par; pelo HTMX devolve só o cartão (ficha: docs/telas/fichas/validar.md).
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.http import urlencode
from django.views.decorators.http import require_http_methods

from nucleo.models import Ano
from nucleo.templatetags.ui import rota_b
from nucleo.ui_bloqueio import e_htmx
from nucleo.urls.painel import itens_validar, validar_pares

NADA = "Nada foi validado: nenhuma revista marcada. Marque ao menos uma e envie de novo."


def ids_de(lista):
    return [int(x) for x in lista if x.isdigit()]


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@permission_required("nucleo.view_revista", raise_exception=True)
def validar(request, ano):
    ano = get_object_or_404(Ano, ano=ano)
    pode = request.user.has_perm("nucleo.validar_revista")
    if request.method == "POST":
        if not pode:
            raise PermissionDenied
        so = request.POST.get("so")  # "Validar esta": só o par do cartão, ignora as outras marcadas
        pares = [so] if so else request.POST.getlist("par")
        if not pares:
            messages.warning(request, NADA)
        feitos = validar_pares(request, ano, pares)
        if e_htmx(request):
            itens = itens_validar(ano, feitos)
            if not itens:  # saiu da lista (arquivada): recarrega e mostra o aviso
                return HttpResponse(headers={"HX-Refresh": "true"})
            ctx = {"i": itens[0], "pode_validar": True, "ano": ano, "oob": True}
            return TemplateResponse(request, "ui/parciais/validar_cartao.html", ctx)
        consulta = urlencode({"revista": ids_de(request.POST.getlist("revista"))}, doseq=True)
        return redirect(reverse("ui_validar", args=[ano.ano]) + (f"?{consulta}" if consulta else ""))
    pedidos = set(ids_de(request.GET.getlist("revista")))
    itens = itens_validar(ano, pedidos)
    painel = rota_b("ui_painel", ano.ano) or reverse("painel", args=[ano.ano])
    ctx = {
        "ano": ano, "secao": "painel", "itens": itens, "pode_validar": pode,
        "fora": len(pedidos) - len(itens), "url_painel": painel,
    }  # fmt: skip
    return TemplateResponse(request, "ui/validar/pagina.html", ctx)


urlpatterns = [
    path("<int:ano>/", validar, name="ui_validar"),
]
