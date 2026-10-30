"""Impresso B (T26/T27: o que mudou, Revista Impressa Atualizada, planilhas): /ui/impresso/<ano>/, rota ui_impresso.
Convenções: docs/telas/design-system.md. Ficha: docs/telas/fichas/impresso.md.

Lista + detalhe: à esquerda as revistas ativas do ano com a situação do impresso; à direita o que
mudou na revista escolhida (?revista=pk; o HTMX troca só o detalhe). A regra é a da página antiga
(`nucleo/urls/impresso.py`: `situacao`, `estado`, `gravar`): ver exige `view_revista`; marcar exige
`marcar_impressa` e grava sob o bloqueio do projeto (`lote.escrever_travado`), sem segurá-lo na leitura.
As planilhas saem pela rota da página antiga (`impresso_planilhas`).
"""

from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.cache import patch_vary_headers
from django.views.decorators.http import require_POST

from nucleo.models import Ano, Revista
from nucleo.ui_bloqueio import e_htmx
from nucleo.urls.impresso import estado, gravar, pode_marcar, situacao
from nucleo.urls.painel import revistas_do_ano
from nucleo.urls.preview import protegida


def _detalhe(request, s):
    return estado(s["revista"], s) | {"pode": pode_marcar(request.user, s["revista"])}


@protegida
def impresso(request, ano=None):
    resp = _impresso(request, ano)
    patch_vary_headers(resp, ["HX-Request"])  # mesma URL, dois corpos: o Voltar não reaproveita o fragmento
    return resp


def _impresso(request, ano):
    anos = list(Ano.objects.order_by("-ano"))
    if ano is None:  # /ui/impresso/ → ano mais recente
        return redirect("ui_impresso", anos[0].ano) if anos else redirect("ui_anos")
    ano = get_object_or_404(Ano, ano=ano)
    pedido = request.GET.get("revista", "")
    if e_htmx(request):  # só o detalhe: não recalcula a lista
        revista = get_object_or_404(revistas_do_ano(ano), pk=pedido) if pedido.isdigit() else None
        ctx = {"detalhe": revista and _detalhe(request, situacao(revista)), "ano": ano}
        return TemplateResponse(request, "ui/parciais/impresso_detalhe.html", ctx)
    # ponytail: resolve cada revista do ano, como o painel; cache por hash se a lista ficar lenta.
    itens = [situacao(r) for r in revistas_do_ano(ano)]
    escolhida = (
        next((i for i in itens if str(i["revista"].pk) == pedido), None)
        or next((i for i in itens if i["pendente"] and i["validada"]), None)  # o que o impresso já pode marcar
        or next((i for i in itens if i["pendente"]), None)
        or (itens[0] if itens else None)
    )
    ctx = {
        "secao": "impresso", "ano": ano, "anos": anos, "itens": itens,
        "detalhe": escolhida and _detalhe(request, escolhida),
        "para_marcar": sum(i["pendente"] and i["validada"] for i in itens),
        "aguardando": sum(i["pendente"] and not i["validada"] for i in itens),
    }  # fmt: skip
    return TemplateResponse(request, "ui/impresso/impresso.html", ctx)


@require_POST
@login_required(login_url="admin:login")
@permission_required("nucleo.marcar_impressa", raise_exception=True)
def marcar(request, ano, pk):
    # Arquivada depois que a página abriu: a regra recusa com mensagem (não 404).
    revistas = Revista.objects.select_related("projeto__parceiro_ano__parceiro", "projeto__ano")
    gravar(request, get_object_or_404(revistas, pk=pk, ano__ano=ano))
    return redirect(f"{reverse('ui_impresso', args=[ano])}?revista={pk}")


urlpatterns = [
    path("", impresso, name="ui_impresso"),
    path("<int:ano>/", impresso, name="ui_impresso"),
    path("<int:ano>/<int:pk>/marcar/", marcar, name="ui_impresso_marcar"),
]
