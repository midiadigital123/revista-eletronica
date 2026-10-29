"""Rotas do bloqueio, chamadas pelo static/nucleo/bloqueio.js da página do admin.

POST com CSRF (middleware padrão). Sem login responde 403 em vez de
redirecionar: o fetch seguiria o redirect e leria a tela de login como 200.
"""

from django.http import HttpResponse, JsonResponse
from django.urls import path
from django.views.decorators.http import require_POST

from nucleo.servicos import bloqueio


def _pedido(request):
    """(alvo, sessao) a partir do POST, ou None se inválido."""
    modelo = bloqueio.MODELOS.get(request.POST.get("alvo"))
    pk = request.POST.get("id", "")
    sessao = request.POST.get("sessao", "")
    # isascii: isdigit aceita "²" e dígitos de outras escritas; < 19 cabe no bigint.
    if modelo is None or not (pk.isascii() and pk.isdigit() and len(pk) < 19):
        return None
    if not 0 < len(sessao) <= 100:
        return None
    return modelo(pk=int(pk)), sessao


def _rota(acao):
    @require_POST
    def view(request):
        if not request.user.is_authenticated:
            return JsonResponse({"erro": "login necessário"}, status=403)
        pedido = _pedido(request)
        if pedido is None:
            return JsonResponse({"erro": "pedido inválido"}, status=400)
        return acao(request, *pedido)

    return view


def renovar(request, alvo, sessao):
    """200 se esta sessão ainda tem o bloqueio (renovado); 409 se perdeu."""
    ok = bloqueio.renovar(alvo, request.user, sessao)
    return JsonResponse({"bloqueio": ok}, status=200 if ok else 409)


def liberar(request, alvo, sessao):
    """Chamado no pagehide (sendBeacon). Idempotente."""
    bloqueio.liberar(alvo, request.user, sessao)
    return HttpResponse(status=204)


urlpatterns = [
    path("renovar", _rota(renovar), name="bloqueio_renovar"),
    path("liberar", _rota(liberar), name="bloqueio_liberar"),
]
