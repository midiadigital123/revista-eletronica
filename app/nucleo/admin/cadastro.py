"""Admin dos cadastros (S11a): Ano, Parceiro, Etapa, Componente e CorPadrao.

Ano só nasce pela ação "Abrir ano" (D-079, D-136): sem incluir, alterar nem excluir.
Etapa, Componente e CorPadrao são por ano (D-086); o ano não muda depois de criado
(as FKs compostas de ano recusariam).
"""

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Max
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path

from nucleo.models import Ano, Componente, CorPadrao, Etapa, Parceiro
from nucleo.servicos.abrir_ano import AnoRecusado, abrir_ano


class SoLeitura:
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class AbrirAnoForm(forms.Form):
    # Sem valor inicial: abrir ano não tem desfazer, o usuário digita o ano.
    ano = forms.IntegerField(label="Ano novo")


@admin.register(Ano)
class AnoAdmin(SoLeitura, admin.ModelAdmin):
    list_display = ("ano",)

    def get_urls(self):
        abrir = path("abrir/", self.admin_site.admin_view(self.abrir_view), name="nucleo_ano_abrir")
        return [abrir, *super().get_urls()]

    def changelist_view(self, request, extra_context=None):
        pode = request.user.has_perm("nucleo.abrir_ano")
        return super().changelist_view(request, {**(extra_context or {}), "pode_abrir_ano": pode})

    def abrir_view(self, request):
        if not request.user.has_perm("nucleo.abrir_ano"):
            raise PermissionDenied
        maior = Ano.objects.aggregate(m=Max("ano"))["m"]
        form = AbrirAnoForm(request.POST or None)
        form.fields["ano"].help_text = f"Digite o ano. O próximo que pode ser aberto é {(maior or 0) + 1}."
        if request.method == "POST" and form.is_valid():
            try:
                novo, origem = abrir_ano(form.cleaned_data["ano"], request.user)
            except AnoRecusado as e:
                form.add_error("ano", str(e))
            else:
                messages.success(request, f"Ano {novo} aberto a partir de {origem}.")
                return redirect("admin:nucleo_ano_changelist")
        contexto = {
            **self.admin_site.each_context(request),
            "opts": self.opts, "title": "Abrir ano", "form": form, "botao": "Abrir ano",
            "aviso": "Copia etapas, componentes, cores, matrizes e templates do último ano. "
            "Não copia parceiros, cortes nem projetos. Não há desfazer.",
        }  # fmt: skip
        return TemplateResponse(request, "nucleo/admin_form.html", contexto)


@admin.register(Parceiro)
class ParceiroAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ("nome",)


class PorAnoAdmin(admin.ModelAdmin):
    """Na edição, o ano e a chave do UNIQUE com o ano ficam readonly (o Django pula a
    checagem de unicidade quando um dos campos não está no form: viraria 500)."""

    list_filter = ("ano",)
    list_select_related = ("ano",)
    chave = "codigo"

    def get_readonly_fields(self, request, obj=None):
        return ("ano", self.chave) if obj else ()


@admin.register(Etapa)
class EtapaAdmin(PorAnoAdmin):
    list_display = ("codigo", "ano", "escala_max", "ordem")
    ordering = ("-ano__ano", "ordem")

    def get_readonly_fields(self, request, obj=None):
        campos = super().get_readonly_fields(request, obj)
        # Escala com corte ou matriz gravados: mudar a escala invalidaria esses dados.
        if obj and (obj.corte_set.exists() or obj.matrizetapacc_set.exists()):
            campos += ("escala_max",)
        return campos


@admin.register(Componente)
class ComponenteAdmin(PorAnoAdmin):
    list_display = ("codigo", "nome", "ano")
    ordering = ("-ano__ano", "codigo")


@admin.register(CorPadrao)
class CorPadraoAdmin(PorAnoAdmin):
    formfield_overrides = {models.TextField: {"widget": forms.TextInput(attrs={"size": 20})}}
    list_display = ("padrao", "nome", "cor", "ano")
    ordering = ("-ano__ano", "padrao")
    chave = "padrao"
