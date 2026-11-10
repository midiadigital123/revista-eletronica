"""Admin dos cadastros (S11a): Ano, Parceiro, Etapa, Componente e CorPadrao.

Ano só nasce pela ação "Abrir ano" (D-079, D-136): sem incluir nem alterar. Excluir (o ano inteiro) é
só do Admin, pela página `ui_excluir` (D-206).
Etapa, Componente e CorPadrao são por ano (D-086); o ano não muda depois de criado
(as FKs compostas de ano recusariam).
"""

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Max
from django.http import Http404
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from nucleo.models import Ano, Componente, CorPadrao, Etapa, Parceiro
from nucleo.paleta import PadraoImpactoForm, nomes, revistas_afetadas_padrao
from nucleo.servicos.abrir_ano import VAZIO, AnoRecusado, abrir_ano


class ExclusaoAdminMixin:
    """D-205: o "Excluir" do admin leva à página `ui_excluir` (impedimentos, confirmação forte, partes e
    versões do template); o delete do Django passaria por fora do serviço. Sem `delete_selected`."""

    campo_exclusao = "pk"  # o `<pk>` da rota; o do ano é o próprio ano (`REGISTRO` de urls/ui_excluir.py)

    def delete_view(self, request, object_id, extra_context=None):
        if not self.has_delete_permission(request):
            raise PermissionDenied
        obj = self.get_object(request, object_id)
        if obj is None:
            raise Http404
        modelo = self.opts.model_name
        destino = reverse("ui_excluir", args=[modelo, getattr(obj, self.campo_exclusao)])
        return redirect(destino + "?" + urlencode({"voltar": reverse(f"admin:nucleo_{modelo}_changelist")}))

    def get_actions(self, request):
        acoes = super().get_actions(request)
        acoes.pop("delete_selected", None)
        return acoes


class SoLeitura:
    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class AbrirAnoForm(forms.Form):
    # Sem valor inicial: abrir ano não tem desfazer, o usuário digita o ano.
    ano = forms.IntegerField(label="Ano novo")


@admin.register(Ano)
class AnoAdmin(ExclusaoAdminMixin, SoLeitura, admin.ModelAdmin):
    list_display = ("ano",)
    campo_exclusao = "ano"

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
        form.fields["ano"].help_text = "Digite o ano." + (f" O próximo que pode ser aberto é {maior + 1}." if maior else "")
        if request.method == "POST" and form.is_valid():
            try:
                novo, origem = abrir_ano(form.cleaned_data["ano"], request.user)
            except AnoRecusado as e:
                form.add_error("ano", str(e))
            else:
                messages.success(request, f"Ano {novo} aberto a partir de {origem}." if origem else VAZIO.format(novo))
                return redirect("admin:nucleo_ano_changelist")
        contexto = {
            **self.admin_site.each_context(request),
            "opts": self.opts, "title": "Abrir ano", "form": form, "botao": "Abrir ano",
            "aviso": "Copia etapas, componentes, cores, matrizes e templates do último ano. "
            "Não copia parceiros, cortes nem projetos. Não há desfazer.",
        }  # fmt: skip
        return TemplateResponse(request, "nucleo/admin_form.html", contexto)


@admin.register(Parceiro)
class ParceiroAdmin(ExclusaoAdminMixin, admin.ModelAdmin):
    list_display = ("nome", "desativado_em")
    list_filter = ("desativado_em",)
    readonly_fields = ("desativado_em",)  # D-208: desativar/reativar só pela página de excluir (serviço)
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
class EtapaAdmin(ExclusaoAdminMixin, PorAnoAdmin):
    list_display = ("codigo", "ano", "escala_max", "ordem")
    ordering = ("-ano__ano", "ordem")

    def get_readonly_fields(self, request, obj=None):
        campos = super().get_readonly_fields(request, obj)
        # Escala com corte ou matriz gravados: mudar a escala invalidaria esses dados.
        if obj and (obj.corte_set.exists() or obj.matrizetapacc_set.exists()):
            campos += ("escala_max",)
        return campos


@admin.register(Componente)
class ComponenteAdmin(ExclusaoAdminMixin, PorAnoAdmin):
    list_display = ("codigo", "nome", "ano")
    ordering = ("-ano__ano", "codigo")


@admin.register(CorPadrao)
class CorPadraoAdmin(PorAnoAdmin):
    form = PadraoImpactoForm
    formfield_overrides = {models.TextField: {"widget": forms.TextInput(attrs={"size": 20})}}
    list_display = ("padrao", "nome", "cor", "ano")
    ordering = ("-ano__ano", "padrao")
    chave = "padrao"

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        # get_form devolve uma classe nova por chamada: o atributo não vaza entre pedidos.
        form.impacto = staticmethod(lambda campos: revistas_afetadas_padrao(obj, campos)) if obj is not None else None
        return form

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        perdem = form.resultado[1] if change else []
        if perdem:
            messages.warning(request, format_html(
                "{} revista(s) perderam o “Validado”: {}. Revalide no <a href=\"{}\">Painel</a>.",
                len(perdem), nomes(perdem), reverse("painel", args=[obj.ano.ano]) + "?falta=validado",
            ))  # fmt: skip
