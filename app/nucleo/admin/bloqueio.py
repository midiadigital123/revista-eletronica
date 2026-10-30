"""BloqueioAdminMixin: um editor por alvo no change form (D-080, D-081, D-121).

Uso (S11a, S11b1, S11c): `class XAdmin(BloqueioAdminMixin, admin.ModelAdmin)`.
Se o alvo do bloqueio não for o próprio objeto (ex.: revista trava o projeto),
sobrescreva `alvo_do_bloqueio`. Um `change_form_template` próprio deve
estender "nucleo/bloqueio_change_form.html".

- GET: tenta adquirir com uma sessão nova (uma por carga da página = uma aba).
  Sem bloqueio: somente leitura, com aviso de quem está editando.
- POST: confere o bloqueio dentro da transação da escrita (FOR SHARE) e recusa
  se outra sessão o tiver. Salvou (redirect): libera, para que "Salvar e
  continuar" readquira com a sessão nova da próxima página.
- Somente leitura vale também para os inlines (sem mudar, incluir ou excluir).
- Excluir é negado enquanto outro usuário tiver o bloqueio. O mesmo usuário
  pode: a página de exclusão não tem sessão, e o bloqueio da própria aba só é
  liberado pelo pagehide, em corrida com o GET da exclusão.

Proibido nos admins com o mixin (S11 respeita): `list_editable` e actions de
escrita (inclusive `delete_selected`), porque passam por fora do change form e
não conferem o bloqueio. Lotes usam `quem_bloqueia` e pulam os travados (D-121).
"""

import logging

from django.contrib import messages
from django.contrib.admin.utils import unquote
from django.db import router, transaction
from django.http import HttpResponseRedirect
from django.utils import timezone

from nucleo.servicos import bloqueio

CAMPO_SESSAO = "_bloqueio_sessao"
log = logging.getLogger(__name__)


def _nega(*args, **kwargs):
    return False


def aviso(request, alvo):
    """Aviso de somente leitura: quem segura o bloqueio e até quando (admin e páginas B)."""
    atual = bloqueio.quem_bloqueia(alvo)
    if atual is None:
        return "Somente leitura: outra sessão está editando. Recarregue para tentar editar."
    if atual.usuario_id == request.user.pk:
        return (
            "Somente leitura: sua outra aba ou a carga anterior desta página ainda segura "
            "a edição; recarregue em alguns segundos."
        )
    quem = atual.usuario.get_full_name() or atual.usuario.get_username()
    return (
        f"Somente leitura: {quem} está editando "
        f"(bloqueio até {timezone.localtime(atual.expira_em):%H:%M:%S}, renovado enquanto "
        "a página estiver aberta). Recarregue para tentar editar."
    )


class BloqueioAdminMixin:
    change_form_template = "nucleo/bloqueio_change_form.html"

    def alvo_do_bloqueio(self, obj):
        return obj

    def has_change_permission(self, request, obj=None):
        if obj is not None and getattr(request, "_bloqueio_somente_leitura", False):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None:
            atual = bloqueio.quem_bloqueia(self.alvo_do_bloqueio(obj))
            if atual is not None and atual.usuario_id != request.user.pk:
                return False
        return super().has_delete_permission(request, obj)

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        # Também quando o admin já diz "só leitura" (ex.: arquivado): o POST daria 403.
        if getattr(request, "_bloqueio_somente_leitura", False) or (
            obj is not None and not self.has_change_permission(request, obj)
        ):
            for inline in inlines:  # instâncias desta requisição: pode trocar o método
                inline.has_change_permission = inline.has_add_permission = _nega
                inline.has_delete_permission = _nega
                inline.max_num = 0
        return inlines

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        obj = self.get_object(request, unquote(object_id)) if object_id else None
        # self (não super): o admin que já diz "só leitura" (ex.: arquivado) não trava o alvo.
        if obj is None or not self.has_change_permission(request, obj):
            # Inclusão, objeto inexistente ou sem permissão: fluxo normal do admin.
            return super().changeform_view(request, object_id, form_url, extra_context)

        alvo = self.alvo_do_bloqueio(obj)
        if request.method == "POST":
            return self._salvar(request, alvo, object_id, form_url, extra_context)

        sessao = bloqueio.nova_sessao()
        if bloqueio.adquirir(alvo, request.user, sessao):
            extra_context = self._contexto(extra_context, alvo, sessao)
        else:
            request._bloqueio_somente_leitura = True
            messages.warning(request, aviso(request, alvo))
        return super().changeform_view(request, object_id, form_url, extra_context)

    def _salvar(self, request, alvo, object_id, form_url, extra_context):
        sessao = request.POST.get(CAMPO_SESSAO, "")
        with transaction.atomic(using=router.db_for_write(self.model)):
            if not bloqueio.conferir_na_transacao(alvo, request.user, sessao):
                messages.error(request, "Não salvo: você perdeu o bloqueio de edição.")
                return HttpResponseRedirect(request.get_full_path())
            resposta = super().changeform_view(
                request, object_id, form_url, self._contexto(extra_context, alvo, sessao)
            )
        if resposta.status_code == 302:
            try:
                bloqueio.liberar(alvo, request.user, sessao)
            except Exception:  # já salvou; o bloqueio expira sozinho em 30 s
                log.exception("Falha ao liberar o bloqueio depois de salvar")
        return resposta

    @staticmethod
    def _contexto(extra_context, alvo, sessao):
        return {
            **(extra_context or {}),
            "bloqueio": {"alvo": bloqueio.campo(alvo), "id": alvo.pk, "sessao": sessao},
            "bloqueio_campo_sessao": CAMPO_SESSAO,
        }
