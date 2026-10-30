"""Preview da revista (S08): a página única F1 + F2, só leitura.

Exige login e `nucleo.view_revista` (sem a permissão: 403). Mostra as faixas
vermelhas (D-116); arquivada mostra a foto de arquivamento (D-117).
A capa sai por rota própria com Content-Type fixo, nosniff, sem cache e CSP de
sandbox (D-145). Arquivo sumido do storage (SVG ou capa) = 404.
O item da tarefa sai em `arquivos/itens/<nome>` (o caminho relativo que o JS do F1 abre, como
no zip): só um item de tarefa da matriz e do componente da revista (D-180).
"""

from pathlib import PurePosixPath

from django.contrib.auth.decorators import login_required, permission_required
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.urls import path, reverse
from django.views.decorators.clickjacking import xframe_options_sameorigin
from django.views.decorators.http import require_GET

from nucleo.models import Revista, Tarefa
from nucleo.servicos import resolver
from nucleo.servicos.html import contexto_pagina

# Extensões que receber_capa grava (tipo pela assinatura mágica, D-137).
TIPOS_CAPA = {".png": "image/png", ".jpg": "image/jpeg", ".webp": "image/webp"}
TIPOS_ITEM = {".pdf": "application/pdf", ".png": "image/png", ".jpg": "image/jpeg"}


def protegida(view):
    """GET, login (redireciona ao admin) e view_revista (403)."""
    view = permission_required("nucleo.view_revista", raise_exception=True)(view)
    return require_GET(login_required(view, login_url="admin:login"))


@protegida
def pagina(request, revista_id):
    try:
        revista = resolver.carregar(revista_id)
    except Revista.DoesNotExist:
        raise Http404
    capa = reverse("preview_capa", args=[revista.pk]) if revista.capa else None
    try:
        contexto = contexto_pagina(revista, preview=True, estaticos=static("revista/"), capa=capa)
    except FileNotFoundError:
        raise Http404("SVG do F2 não encontrado no storage. Envie o SVG de novo na revista.")
    return render(request, "revista/index.html", contexto)


@protegida
def capa(request, revista_id):
    revista = get_object_or_404(Revista, pk=revista_id)
    tipo = TIPOS_CAPA.get(PurePosixPath(revista.capa or "").suffix)
    if tipo is None:
        raise Http404
    try:
        arquivo = default_storage.open(revista.capa)
    except FileNotFoundError:
        raise Http404
    return servir(arquivo, tipo)


def servir(arquivo, tipo, sandbox=True, as_attachment=False):
    resposta = FileResponse(arquivo, content_type=tipo, as_attachment=as_attachment)
    resposta["X-Content-Type-Options"] = "nosniff"
    resposta["Cache-Control"] = "private, no-store"
    # sandbox no PDF impede o visualizador do Chrome de abrir; o PDF só pode ir num frame da origem.
    resposta["Content-Security-Policy"] = "default-src 'none'; " + ("sandbox" if sandbox else "frame-ancestors 'self'")
    return resposta


@xframe_options_sameorigin  # o PDF abre no iframe do modal "Ver item" (o padrão do Django é DENY)
@protegida
def item(request, revista_id, nome):
    revista = get_object_or_404(Revista.objects.select_related("projeto__parceiro_ano"), pk=revista_id)
    tipo = TIPOS_ITEM.get(PurePosixPath(nome).suffix)
    caminho = (
        Tarefa.objects.filter(
            descritor__matriz_etapa_cc__matriz_id=revista.projeto.parceiro_ano.matriz_id,
            descritor__matriz_etapa_cc__componente_id=revista.componente_id,
            arquivo__endswith=f"/{nome}",
        )
        .values_list("arquivo", flat=True)
        .first()
    )
    if tipo is None or caminho is None:
        raise Http404
    try:
        arquivo = default_storage.open(caminho)
    except FileNotFoundError:
        raise Http404
    return servir(arquivo, tipo, sandbox=tipo != "application/pdf")


urlpatterns = [
    path("<int:revista_id>/", pagina, name="preview"),
    path("<int:revista_id>/capa", capa, name="preview_capa"),
    path("<int:revista_id>/arquivos/itens/<str:nome>", item, name="preview_item"),
]
