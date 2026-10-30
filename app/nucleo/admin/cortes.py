"""Tela de cortes no admin e planilha de grupos (S11a; D-049, D-055, D-056, D-135).

A regra da grade mora em `nucleo/cortes.py`, comum a esta tela e à página própria (`/cortes/<ano>/`).
"""

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.http import Http404, HttpResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse

from nucleo.admin.lote import escolher_ano, rota
from nucleo.cortes import grade, numerar_grupos, planilha  # noqa: F401 (numerar_grupos: testes)
from nucleo.models import Corte


@admin.register(Corte)
class CorteAdmin(admin.ModelAdmin):
    def get_urls(self):
        # Só a grade e a exportação: corte não se edita um a um (a linha do parceiro é inteira).
        return [rota(self, "", self.changelist_view, "changelist"), rota(self, "exportar/", self.exportar_view, "exportar")]

    def has_add_permission(self, request):
        return False  # some o "incluir" do índice; a grade confere add + change por conta própria

    def _ano(self, request):
        if not self.has_view_permission(request):
            raise PermissionDenied
        return escolher_ano(request)

    def exportar_view(self, request):
        _, ano = self._ano(request)
        if ano is None:
            raise Http404("Nenhum ano aberto.")
        resposta = HttpResponse(planilha(ano), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        resposta["Content-Disposition"] = f'attachment; filename="cortes-{ano.ano}.xlsx"'
        return resposta

    def changelist_view(self, request, extra_context=None):
        anos, ano = self._ano(request)
        contexto = {
            **self.admin_site.each_context(request), "opts": self.opts, "title": "Cortes",
            "ano": ano, "anos": anos,
        }  # fmt: skip
        if ano is not None:
            extra, gravou = grade(request, ano)
            if gravou:
                return redirect(f"{reverse('admin:nucleo_corte_changelist')}?ano={ano.ano}")
            contexto.update(extra)
        return TemplateResponse(request, "nucleo/cortes.html", contexto)
