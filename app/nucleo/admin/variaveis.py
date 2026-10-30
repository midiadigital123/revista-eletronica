"""Aba Variáveis no admin (D-100, D-107, D-119): projetos do ano × variáveis, como planilha.

Página própria (rota em ProjetoAdmin.get_urls), não `list_editable`: o ProjetoAdmin usa o
BloqueioAdminMixin. A regra está em `nucleo/planilha_variaveis.py` (comum à tela B).
"""

from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from nucleo.admin.lote import contexto, escolher_ano, filtro
from nucleo.planilha_variaveis import EDITAVEIS, limitar, mostrar_nome_do_ano, planilha  # noqa: F401 (admin/projeto.py)


def variaveis(model_admin, request):
    if not model_admin.has_view_permission(request):
        raise PermissionDenied
    anos, ano = escolher_ano(request)
    extra, gravou = planilha(request, ano)
    if gravou:
        return HttpResponseRedirect(request.get_full_path())
    ctx = contexto(
        model_admin, request, "Variáveis dos projetos", **extra,
        filtros=[filtro("Ano", [(a, a.ano) for a in anos], ano, "ano")],
    )  # fmt: skip
    return TemplateResponse(request, "nucleo/variaveis.html", ctx)
