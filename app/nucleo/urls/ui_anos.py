"""Anos (tela B, S3 de D-190): lista dos anos e "Abrir ano", mesma regra do admin (`AnoAdmin.abrir_view`).

Ver exige `view_ano` (403); abrir exige `abrir_ano` (403 no POST, formulário escondido no GET).
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_http_methods

from nucleo.models import Ano
from nucleo.servicos.abrir_ano import AnoRecusado, abrir_ano


class AbrirAnoForm(forms.Form):  # cópia do form do admin: importá-lo daria import circular (admin → urls)
    ano = forms.IntegerField(label="Ano novo")


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@permission_required("nucleo.view_ano", raise_exception=True)
def anos(request):
    if request.method == "POST" and not request.user.has_perm("nucleo.abrir_ano"):
        raise PermissionDenied
    anos = list(Ano.objects.order_by("-ano"))
    form = AbrirAnoForm(request.POST or None)  # sem valor inicial: não há desfazer, o usuário digita
    if request.method == "POST" and form.is_valid():
        try:
            novo, origem = abrir_ano(form.cleaned_data["ano"], request.user)
        except AnoRecusado as e:
            form.add_error("ano", str(e))
        else:
            messages.success(request, f"Ano {novo} aberto a partir de {origem}.")
            return redirect("ui_anos")
    contexto = {
        "anos": anos, "ano": anos[0] if anos else None, "proximo": anos[0].ano + 1 if anos else None,
        "form": form, "secao": "anos",
    }  # fmt: skip
    return TemplateResponse(request, "ui/anos/anos.html", contexto)


urlpatterns = [path("", anos, name="ui_anos")]
