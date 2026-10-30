"""Bloqueio de edição nas páginas próprias (opção B): o BloqueioAdminMixin para views de função.

Mesma regra do admin (D-080, D-081, D-121), mesmo serviço (`servicos/bloqueio.py`), mesmo JS
(`static/nucleo/bloqueio.js`) e mesmo campo de sessão (`_bloqueio_sessao`). Uso:

    @login_required(login_url="admin:login")
    @com_bloqueio(lambda request, pk: get_object_or_404(Projeto, pk=pk), pode_gravar)
    def projeto(request, pk): ...

- GET de página: quem `pode_gravar` tenta adquirir com uma sessão nova (uma por aba). Sem
  bloqueio: aviso de quem edita e `request.pode_gravar = False` (somente leitura).
- GET do HTMX (fragmento): não adquire; vale a sessão que o bloqueio.js põe em todo pedido HTMX.
- POST: sem `pode_gravar` é 403. Confere o bloqueio dentro da transação (FOR SHARE) e roda a
  view nela; perdeu o bloqueio: nada roda, mensagem e volta à página. Resposta de redirect
  (302 ou HX-Redirect) libera o bloqueio, como o "Salvar" do admin.

A view lê `request.pode_gravar` (permissão e bloqueio juntos) e o template põe
`{% include "ui/_componentes/bloqueio.html" %}` dentro do <form> que grava.
"""

import logging
from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect

from nucleo.admin.bloqueio import CAMPO_SESSAO, aviso
from nucleo.servicos import bloqueio

log = logging.getLogger(__name__)
PERDEU = "Não salvo: você perdeu o bloqueio de edição (outra pessoa ou aba abriu esta página). Recarregue e refaça a alteração."


def e_htmx(request):
    # Restauração de histórico (falta no cache do htmx) pede a página inteira, não o fragmento.
    return request.headers.get("HX-Request") == "true" and not request.headers.get("HX-History-Restore-Request")


def _dados(alvo, sessao):
    return {"alvo": bloqueio.campo(alvo), "id": alvo.pk, "sessao": sessao, "campo": CAMPO_SESSAO}


def _voltar(request):
    """Recarrega a página inteira: no HTMX o caminho do pedido pode ser o de um fragmento."""
    if e_htmx(request):
        return HttpResponse(headers={"HX-Refresh": "true"})
    return HttpResponseRedirect(request.get_full_path())


def com_bloqueio(obter_alvo, pode_gravar):
    """`obter_alvo(request, *args, **kwargs)` devolve a instância travada (Projeto, Template ou
    MatrizEtapaCC; ex.: a revista trava o projeto) ou None para não travar (ex.: arquivado).
    `pode_gravar(user)` é a permissão de escrita do admin equivalente."""

    def decorador(view):
        @wraps(view)
        def envolta(request, *args, **kwargs):
            alvo = obter_alvo(request, *args, **kwargs)
            pode = pode_gravar(request.user)
            request.bloqueio = None
            if request.method == "POST":
                if not pode:
                    raise PermissionDenied
                if alvo is None:
                    request.pode_gravar = True
                    return view(request, *args, **kwargs)
                return _salvar(request, alvo, view, args, kwargs)
            if pode and alvo is not None:
                if e_htmx(request):
                    sessao = request.GET.get(CAMPO_SESSAO, "")
                    atual = bloqueio.quem_bloqueia(alvo)
                    pode = atual is not None and atual.usuario_id == request.user.pk and atual.sessao_edicao == sessao
                else:
                    sessao = bloqueio.nova_sessao()
                    pode = bloqueio.adquirir(alvo, request.user, sessao)
                    if not pode:
                        messages.warning(request, aviso(request, alvo))
                if pode:
                    request.bloqueio = _dados(alvo, sessao)
            request.pode_gravar = pode
            return view(request, *args, **kwargs)

        return envolta

    return decorador


def _salvar(request, alvo, view, args, kwargs):
    sessao = request.POST.get(CAMPO_SESSAO, "")
    with transaction.atomic():
        if not bloqueio.conferir_na_transacao(alvo, request.user, sessao):
            messages.error(request, PERDEU)
            return _voltar(request)
        request.bloqueio, request.pode_gravar = _dados(alvo, sessao), True
        resposta = view(request, *args, **kwargs)
    if resposta.status_code in (301, 302, 303) or resposta.has_header("HX-Redirect"):
        try:
            bloqueio.liberar(alvo, request.user, sessao)
        except Exception:  # já salvou; o bloqueio expira sozinho em 30 s
            log.exception("Falha ao liberar o bloqueio depois de salvar")
    return resposta
