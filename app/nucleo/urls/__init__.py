from django.shortcuts import redirect
from django.urls import include, path

from nucleo.models import Ano


def inicio(request):
    """`/` → Painel do maior ano; sem ano, a tela de anos (o login fica com cada destino)."""
    ano = Ano.objects.order_by("-ano").first()
    return redirect("painel", ano.ano) if ano else redirect("ui_anos")


urlpatterns = [
    path("", inicio, name="inicio"),
    path("bloqueio/", include("nucleo.urls.bloqueio")),
    path("conta/", include("nucleo.urls.conta")),
    path("cortes/", include("nucleo.urls.cortes")),
    path("impresso/", include("nucleo.urls.impresso")),
    path("painel/", include("nucleo.urls.ui_painel")),  # painel B (D-183): /painel/<ano>/
    path("painel/", include("nucleo.urls.painel")),  # validar em lote do admin: /painel/<ano>/validar/
    path("preview/", include("nucleo.urls.preview")),
    path("templates/", include("nucleo.urls.templates")),
    # Telas B (D-183, D-186): um módulo por tela, já incluído para os agentes não disputarem este arquivo.
    path("ui/validar/", include("nucleo.urls.ui_validar")),
    path("ui/variaveis/", include("nucleo.urls.ui_variaveis")),
    path("ui/projeto/", include("nucleo.urls.ui_projeto")),
    path("ui/templates/", include("nucleo.urls.ui_templates")),
    path("ui/matriz/", include("nucleo.urls.ui_matriz")),
    path("ui/revista/", include("nucleo.urls.ui_revista")),
    path("ui/impresso/", include("nucleo.urls.ui_impresso")),
    path("ui/lotes/", include("nucleo.urls.ui_lotes")),
    path("ui/anos/", include("nucleo.urls.ui_anos")),
]
