from django.shortcuts import redirect
from django.urls import include, path

from nucleo.models import Ano


def inicio(request):
    """`/` → Painel do maior ano; sem ano, o índice do admin (o login fica com cada destino)."""
    ano = Ano.objects.order_by("-ano").first()
    return redirect("painel", ano.ano) if ano else redirect("admin:index")


urlpatterns = [
    path("", inicio, name="inicio"),
    path("bloqueio/", include("nucleo.urls.bloqueio")),
    path("cortes/", include("nucleo.urls.cortes")),
    path("impresso/", include("nucleo.urls.impresso")),
    path("painel/", include("nucleo.urls.painel")),
    path("preview/", include("nucleo.urls.preview")),
    path("templates/", include("nucleo.urls.templates")),
]
