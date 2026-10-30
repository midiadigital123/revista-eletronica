"""Admin de Projeto (S11c): nome, variáveis, passo e cores por projeto (D-053, D-060, D-091).

Projeto nasce e é arquivado pela cascata (S06): aqui não se inclui nem exclui. Arquivado é só
leitura (D-093). Rotas próprias (fora do mixin): aba Variáveis e lote "Escolher matriz".
"""

from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse

from nucleo.admin import lote, variaveis
from nucleo.admin.bloqueio import BloqueioAdminMixin
from nucleo.models import Projeto, ProjetoCor, ProjetoPasso
from nucleo.projeto import MAX_CORES, CorForm, PassoForm, PassoFormSet, ProjetoForm
from nucleo.variaveis import VARIAVEIS


class PassoInline(admin.TabularInline):
    model = ProjetoPasso
    form = PassoForm
    formset = PassoFormSet
    extra = 0
    verbose_name = "passo sobrescrito"
    verbose_name_plural = (
        "Passo por etapa × componente (sobrescreve o da matriz; a linha existir = sobrescrevi;"
        " excluir a linha = voltar ao passo da matriz)"
    )


class CorInline(admin.TabularInline):
    model = ProjetoCor
    form = CorForm
    extra = 0
    max_num = MAX_CORES
    verbose_name_plural = "Cores do projeto (sobrescrevem a paleta do ano, D-060; excluir = voltar à paleta)"


@admin.register(Projeto)
class ProjetoAdmin(BloqueioAdminMixin, admin.ModelAdmin):
    form = ProjetoForm
    change_list_template = "nucleo/change_list_lotes.html"
    list_display = ("nome", "parceiro", "ano", "arquivado_em")
    list_select_related = ("parceiro_ano__parceiro", "ano")
    list_filter = ("ano", ("arquivado_em", admin.EmptyFieldListFilter))
    search_fields = ("nome", "parceiro_ano__parceiro__nome")
    readonly_fields = ("parceiro_ano", "ano", "arquivado_em")
    fieldsets = (
        (None, {"fields": ("nome", "parceiro_ano", "ano", "arquivado_em"),
                "description": "As variáveis também são editáveis na aba Variáveis."}),
    ) + tuple(
        # Um fieldset por grupo de variáveis, na ordem de VARIAVEIS (25 campos num bloco só cansam).
        (f"Variáveis: {g}", {"fields": [v.nome for v in VARIAVEIS if v.grupo == g and not v.automatica]})
        for g in dict.fromkeys(v.grupo for v in VARIAVEIS if not v.automatica)
    )
    formfield_overrides = {models.TextField: {"widget": forms.TextInput(attrs={"size": 60})}}
    inlines = [PassoInline, CorInline]
    actions = None  # mixin: nada de actions de escrita (inclusive delete_selected)

    @admin.display(description="Parceiro", ordering="parceiro_ano__parceiro__nome")
    def parceiro(self, obj):
        return obj.parceiro_ano.parceiro

    def has_add_permission(self, request):
        return False  # nasce pela cascata (S06)

    def has_delete_permission(self, request, obj=None):
        return False  # arquiva pela cascata

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj.arquivado_em is not None:
            return False
        return super().has_change_permission(request, obj)

    def get_urls(self):
        return [
            lote.rota(self, "variaveis/", lambda r: variaveis.variaveis(self, r), "variaveis"),
            lote.rota(self, "escolher-matriz/", lambda r: lote.escolher_matriz(self, r), "escolher_matriz"),
        ] + super().get_urls()

    def changelist_view(self, request, extra_context=None):
        links = [("Variáveis", reverse("admin:nucleo_projeto_variaveis"))]
        if request.user.has_perm("nucleo.change_parceiroano"):
            links.append(("Escolher matriz", reverse("admin:nucleo_projeto_escolher_matriz")))
        if request.user.has_perm("nucleo.change_revistafasciculo"):
            links.append(("Escolher template F1/F2", reverse("admin:nucleo_revista_escolher_template")))
        return super().changelist_view(request, {**(extra_context or {}), "lotes": links})
