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
from nucleo.admin.variaveis import limitar
from nucleo.models import Componente, Etapa, Projeto, ProjetoCor, ProjetoPasso
from nucleo.variaveis import TAMANHO_MAX, VARIAVEIS


class PassoForm(forms.ModelForm):
    passo = forms.IntegerField(
        required=False, min_value=1, help_text="Vazio = sem linhas vazias, de propósito (D-091)."
    )

    class Meta:
        model = ProjetoPasso
        fields = ["etapa", "componente", "passo"]

    def clean(self):
        dados = super().clean()
        # D-053: etapa e componente do ano do projeto (as FKs compostas também recusam).
        ano_id = Projeto.objects.values_list("ano_id", flat=True).get(pk=self.instance.projeto_id)
        for nome in ("etapa", "componente"):
            if dados.get(nome) is not None and dados[nome].ano_id != ano_id:
                self.add_error(nome, "Precisa ser do ano do projeto.")
        self.instance.ano_id = ano_id
        return dados


class PassoInline(admin.TabularInline):
    model = ProjetoPasso
    form = PassoForm
    extra = 0
    verbose_name = "passo sobrescrito"
    verbose_name_plural = (
        "Passo por etapa × componente (sobrescreve o da matriz; a linha existir = sobrescrevi;"
        " excluir a linha = voltar ao passo da matriz)"
    )

    def get_formset(self, request, obj=None, **kwargs):
        self._ano_id = obj.ano_id if obj else None  # instância por requisição
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "etapa":
            kwargs["queryset"] = Etapa.objects.filter(ano_id=getattr(self, "_ano_id", None)).order_by("ordem")
        elif db_field.name == "componente":
            kwargs["queryset"] = Componente.objects.filter(ano_id=getattr(self, "_ano_id", None)).order_by("codigo")
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CorInline(admin.TabularInline):
    model = ProjetoCor
    formfield_overrides = {models.TextField: {"widget": forms.TextInput(attrs={"type": "color"})}}
    extra = 0
    max_num = 5
    verbose_name_plural = "Cores do projeto (sobrescrevem a paleta do ano, D-060; excluir = voltar à paleta)"


class ProjetoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        limitar(self, {"nome": 200, **dict.fromkeys(variaveis.EDITAVEIS, TAMANHO_MAX)})  # CHECKs do banco
        variaveis.mostrar_nome_do_ano(self, self.instance.ano_id)


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
