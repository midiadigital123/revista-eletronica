"""Admin de Revista (S15): só leitura, com a ação "Baixar zip".

S11c estende (upload de SVG/capa, lote de templates) liberando `has_change_permission`;
`hash_validado`, `validado_*` e `arquivada_em` continuam só leitura (D-142). Nunca exclui (D-117).
"""

from django.contrib import admin, messages
from django.http import HttpResponse

from nucleo.models import Revista
from nucleo.servicos import resolver
from nucleo.servicos.empacotar import Pendente, zip_revista


@admin.register(Revista)
class RevistaAdmin(admin.ModelAdmin):
    list_display = ("projeto", "componente", "arquivada_em")
    list_select_related = ("projeto", "componente")
    list_filter = ("ano", "componente")
    readonly_fields = ("hash_validado", "validado_em", "validado_por", "arquivada_em")
    actions = ["baixar_zip"]

    def has_add_permission(self, request):
        return False  # revista nasce pela cascata (S06)

    def has_change_permission(self, request, obj=None):
        return False  # S11c libera

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Baixar zip", permissions=["view"])
    def baixar_zip(self, request, queryset):
        # Uma por vez: zip de zips só empacotaria os mesmos bytes; o lote é o S11c/S12.
        pks = list(queryset.values_list("pk", flat=True)[:2])
        if len(pks) != 1:
            self.message_user(request, "Escolha uma revista por vez para baixar o zip.", messages.ERROR)
            return None
        revista = resolver.carregar(pks[0])
        try:
            nome, dados = zip_revista(revista)
        except Pendente as e:
            self.message_user(request, f"Zip recusado. Pendências: {e}", messages.ERROR)
            return None
        resposta = HttpResponse(dados, content_type="application/zip")
        resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
        return resposta
