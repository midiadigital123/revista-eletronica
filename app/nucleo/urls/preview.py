"""Preview da revista (S08): a página única F1 + F2, só leitura, para usuário logado.

Mostra as faixas vermelhas (D-116); arquivada mostra a foto de arquivamento (D-117).
A capa sai por rota própria com Content-Type fixo e nosniff (D-145).
"""

from pathlib import PurePosixPath

from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.urls import path, reverse
from django.views.decorators.http import require_GET

from nucleo.models import Revista
from nucleo.servicos import resolver
from nucleo.servicos.html import contexto_pagina

# Extensões que receber_capa grava (tipo pela assinatura mágica, D-137).
TIPOS_CAPA = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}
entrar = login_required(login_url="admin:login")


@require_GET
@entrar
def pagina(request, revista_id):
    try:
        revista = resolver.carregar(revista_id)
    except Revista.DoesNotExist:
        raise Http404
    capa = reverse("preview_capa", args=[revista.pk]) if revista.capa else None
    contexto = contexto_pagina(revista, preview=True, estaticos=static("revista/"), capa=capa)
    return render(request, "revista/index.html", contexto)


@require_GET
@entrar
def capa(request, revista_id):
    revista = get_object_or_404(Revista, pk=revista_id)
    tipo = TIPOS_CAPA.get(PurePosixPath(revista.capa or "").suffix)
    if tipo is None:
        raise Http404
    resposta = FileResponse(default_storage.open(revista.capa), content_type=tipo)
    resposta["X-Content-Type-Options"] = "nosniff"
    return resposta


urlpatterns = [
    path("<int:revista_id>/", pagina, name="preview"),
    path("<int:revista_id>/capa", capa, name="preview_capa"),
]
