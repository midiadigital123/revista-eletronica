"""Lotes (D-102, D-121) no admin: "Escolher matriz" (ParceiroAno) e "Escolher template F1/F2" (Revista).

Páginas próprias (rotas em ProjetoAdmin/RevistaAdmin.get_urls), não actions: os admins com o
BloqueioAdminMixin não podem ter actions de escrita. A regra (forms, gravação com bloqueio,
pulados) fica em `nucleo/lotes.py`, comum à página B (`urls/ui_lotes.py`).
"""

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.http import urlencode

from nucleo import lotes as lote
from nucleo.lotes import (  # noqa: F401  (variaveis, painel e impresso usam lote.escrever_travado & cia.)
    MatrizLoteForm,
    TemplateLoteForm,
    aplicar,
    avisar_pulados,
    escrever_travado,
    quem_edita,
)
from nucleo.models import Ano, Componente


def escolher_ano(request):
    """(anos, ano escolhido por ?ano=AAAA; padrão: o mais recente)."""
    anos = list(Ano.objects.order_by("-ano"))
    pedido = request.GET.get("ano", "")
    ano = next((a for a in anos if str(a.ano) == pedido), anos[0] if anos else None)
    return anos, ano


def rota(model_admin, caminho, view, nome):
    """path() de uma view extra do admin, com login/permissão e nome "nucleo_<modelo>_<nome>"."""
    return path(caminho, model_admin.admin_site.admin_view(view), name=f"nucleo_{model_admin.opts.model_name}_{nome}")


def filtro(rotulo, opcoes, ativo, chave, extra=None):
    """Linha de links do filtro: [(texto, url, ativo)]."""
    return (
        rotulo,
        [(str(o), "?" + urlencode({**(extra or {}), chave: valor}), o == ativo) for o, valor in opcoes],
    )


def contexto(model_admin, request, titulo, **extra):
    return {
        **model_admin.admin_site.each_context(request),
        "title": titulo,
        "opts": model_admin.model._meta,
        **extra,
    }


# --- Escolher matriz ------------------------------------------------------------


def escolher_matriz(model_admin, request):
    if not request.user.has_perm("nucleo.change_parceiroano"):
        raise PermissionDenied
    anos, ano = escolher_ano(request)
    form = None
    if ano is not None:
        form = MatrizLoteForm(request.POST or None, ano=ano)
        if request.method == "POST" and form.is_valid():
            lote.gravar_matriz(request, form)
            return HttpResponseRedirect(request.get_full_path())
    ctx = contexto(
        model_admin, request, "Escolher matriz", form=form,
        filtros=[filtro("Ano", [(a, a.ano) for a in anos], ano, "ano")],
        vazio="Nenhum ano cadastrado.",
    )  # fmt: skip
    return TemplateResponse(request, "nucleo/lote.html", ctx)


# --- Escolher template F1/F2 ------------------------------------------------------


def escolher_template(model_admin, request):
    if not request.user.has_perm("nucleo.change_revistafasciculo"):
        raise PermissionDenied
    anos, ano = escolher_ano(request)
    filtros, form, vazio = [], None, "Nenhum ano cadastrado."
    if ano is not None:
        componentes = list(Componente.objects.filter(ano=ano).order_by("codigo"))
        pedido = request.GET.get("componente", "")
        componente = next((c for c in componentes if str(c.pk) == pedido), None)
        filtros = [
            filtro("Ano", [(a, a.ano) for a in anos], ano, "ano"),
            filtro("Componente", [(c, c.pk) for c in componentes], componente, "componente", {"ano": ano.ano}),
        ]
        vazio = "Escolha o componente: o template tem de ser do mesmo componente da revista."
        if componente is not None:
            form = TemplateLoteForm(request.POST or None, ano=ano, componente=componente)
    if form is not None and request.method == "POST" and form.is_valid():
        lote.gravar_template(request, form)
        return HttpResponseRedirect(request.get_full_path())
    ctx = contexto(model_admin, request, "Escolher template F1/F2", form=form, filtros=filtros, vazio=vazio)
    return TemplateResponse(request, "nucleo/lote.html", ctx)
