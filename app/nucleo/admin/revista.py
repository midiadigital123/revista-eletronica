"""Admin de Revista: upload de SVG e capa, template por fascículo, "Baixar zip" (S15, S11c).

Edita com o bloqueio do projeto (D-140, D-143). `hash_validado`, `validado_*` e `arquivada_em`
são só leitura: só os serviços os escrevem (D-142). Nunca inclui nem exclui (D-117).
S11b2: o texto por seção entra como mais um fieldset em `fieldsets`.

Upload com ids faltando GRAVA e avisa (decisão do S11c): o template pode ganhar ou perder
seções depois, e a pendência `ids_svg` do resolver já bloqueia o "Validado".
"""

import csv
import io

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import path, reverse
from django.utils.html import format_html

from nucleo.admin import lote
from nucleo.admin.bloqueio import BloqueioAdminMixin
from nucleo.models import Revista, RevistaFasciculo, Template
from nucleo.servicos import arquivos, resolver
from nucleo.servicos.empacotar import Pendente, zip_revista

UPLOADS = ("arquivo_svg", "arquivo_capa")


class RevistaForm(forms.ModelForm):
    # Validam no clean (erro no campo); gravam no save_model, depois do form todo válido.
    arquivo_svg = forms.FileField(
        required=False, label="Trocar SVG do F2", help_text="Substitui o SVG anterior. Até 3 MB. Ids pela convenção: passoN, btn-action-xx."
    )
    arquivo_capa = forms.FileField(
        required=False, label="Trocar capa", help_text="Substitui a capa anterior. PNG, JPG ou WebP até 5 MB."
    )

    class Meta:
        model = Revista
        fields = []

    def clean_arquivo_svg(self):
        f = self.cleaned_data.get("arquivo_svg")
        if not f:
            return None
        dados = arquivos._ler(f, arquivos.SVG_MAX, "SVG")
        arquivos.sanitizar_svg(dados)  # ponytail: o receber_svg sanitiza de novo (3 MB no pior caso)
        return dados

    def clean_arquivo_capa(self):
        f = self.cleaned_data.get("arquivo_capa")
        if not f:
            return None
        dados = arquivos._ler(f, arquivos.CAPA_MAX, "Capa")
        if arquivos.tipo_imagem(dados) is None:
            raise ValidationError("Capa precisa ser PNG, JPG ou WebP.")
        return dados


class FasciculoForm(forms.ModelForm):
    class Meta:
        model = RevistaFasciculo
        fields = ["template"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        rf = self.instance
        # Só templates do mesmo ano, componente e fascículo (a FK composta também recusa, D-098).
        self.fields["template"].queryset = Template.objects.filter(
            ano_id=rf.ano_id, componente_id=rf.componente_id, fasciculo=rf.fasciculo
        ).order_by("nome")

    def clean_template(self):
        novo = self.cleaned_data["template"]
        rf = self.instance
        if novo != rf.template and rf.pk and rf.revistasecao_set.exists():
            raise ValidationError("Este fascículo tem textos editados (cópias de seção): o template não pode mudar.")
        return novo


class FasciculoInline(admin.TabularInline):
    model = RevistaFasciculo
    form = FasciculoForm
    fields = ("fasciculo", "template")
    readonly_fields = ("fasciculo",)
    extra = 0
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False  # nascem com a revista (S06)


def celula(valor):
    """Célula de CSV que o Excel não executa como fórmula (=, +, -, @, tab, CR no início)."""
    return "'" + valor if valor[:1] in ("=", "+", "-", "@", "\t", "\r") else valor


def ids_do_f2(revista):
    """(esperados, faltando) pelas seções efetivas do F2; None sem template do F2."""
    f2 = RevistaFasciculo.objects.filter(revista=revista, fasciculo="F2").first()
    secoes = resolver.secoes_efetivas(f2)
    if secoes is None:
        return None
    nomes = [s[0] for s in secoes]
    return arquivos.ids_esperados(nomes), arquivos.ids_faltando(revista, nomes)


def aviso_ids(revista, faltando, esperados):
    url = reverse("admin:nucleo_revista_gabarito_ids", args=[revista.pk])
    return format_html(
        'Ids que faltam no SVG: <strong>{}</strong>. Esperados: {}. <a class="button" href="{}">Baixar gabarito de ids</a>',
        ", ".join(faltando), ", ".join(esperados), url,
    )  # fmt: skip


@admin.register(Revista)
class RevistaAdmin(BloqueioAdminMixin, admin.ModelAdmin):
    form = RevistaForm
    change_list_template = "nucleo/change_list_lotes.html"
    list_display = ("projeto", "componente", "arquivada_em")
    list_select_related = ("projeto", "componente")
    list_filter = ("ano", "componente")
    readonly_fields = (
        "projeto", "componente", "ano", "svg_f2", "svg_sha256", "conferencia_ids", "capa", "capa_sha256",
        "hash_validado", "validado_em", "validado_por", "arquivada_em",
    )  # fmt: skip
    fieldsets = (
        (None, {"fields": ("projeto", "componente", "ano")}),
        ("SVG do F2", {"fields": ("arquivo_svg", "svg_f2", "svg_sha256", "conferencia_ids")}),
        ("Capa", {"fields": ("arquivo_capa", "capa", "capa_sha256")}),
        ("Validação", {"fields": ("hash_validado", "validado_em", "validado_por", "arquivada_em")}),
    )
    inlines = [FasciculoInline]
    actions = ["baixar_zip"]  # só leitura: o mixin proíbe actions de escrita

    def alvo_do_bloqueio(self, obj):
        return obj.projeto  # revista trava o projeto dela (D-140)

    def get_fieldsets(self, request, obj=None):
        if obj is not None and not self.has_change_permission(request, obj):
            # Sem os campos de upload: o admin os mostraria como "-" na tela só leitura.
            return [(nome, {**op, "fields": [f for f in op["fields"] if f not in UPLOADS]}) for nome, op in self.fieldsets]
        return self.fieldsets

    @admin.display(description="Ids do SVG")
    def conferencia_ids(self, obj):
        if not obj.svg_f2:
            return "Sem SVG."
        ids = ids_do_f2(obj)
        if ids is None:
            return "Sem template do F2: nada a conferir."
        esperados, faltando = ids
        if faltando:
            return aviso_ids(obj, faltando, esperados)
        return format_html("Todos os {} ids esperados estão no SVG.", len(esperados))

    def has_add_permission(self, request):
        return False  # revista nasce pela cascata (S06)

    def has_change_permission(self, request, obj=None):
        if obj is not None and (obj.arquivada_em is not None or obj.projeto.arquivado_em is not None):
            return False  # arquivada: só leitura (D-093, D-117)
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        if any(n not in UPLOADS for n in form.changed_data):  # S11b2: campos do modelo
            super().save_model(request, obj, form, change)
        if form.cleaned_data.get("arquivo_svg"):
            arquivos.receber_svg(obj, form.cleaned_data["arquivo_svg"])
            ids = ids_do_f2(obj)
            if ids and ids[1]:
                messages.warning(request, aviso_ids(obj, ids[1], ids[0]))
        if form.cleaned_data.get("arquivo_capa"):
            arquivos.receber_capa(obj, form.cleaned_data["arquivo_capa"])

    def get_urls(self):
        def rota(caminho, view, nome):
            return path(caminho, self.admin_site.admin_view(view), name=f"nucleo_revista_{nome}")

        return [
            rota("escolher-template/", lambda r: lote.escolher_template(self, r), "escolher_template"),
            rota("<int:pk>/gabarito-ids/", self.gabarito_ids, "gabarito_ids"),
        ] + super().get_urls()

    def gabarito_ids(self, request, pk):
        """CSV com os ids que o design deve pôr no SVG (sem o prefixo f2-, que o upload põe)."""
        revista = get_object_or_404(Revista, pk=pk)
        if not self.has_view_permission(request, revista):
            raise PermissionDenied
        f2 = RevistaFasciculo.objects.filter(revista=revista, fasciculo="F2").first()
        saida = io.StringIO()
        escritor = csv.writer(saida)
        escritor.writerow(["id_no_svg", "secao_do_template"])
        for secao, *_ in resolver.secoes_efetivas(f2) or []:
            for id_ in arquivos.ids_esperados([secao]):
                escritor.writerow([celula(id_), celula(secao)])
        resposta = HttpResponse(saida.getvalue(), content_type="text/csv; charset=utf-8")
        resposta["Content-Disposition"] = f'attachment; filename="gabarito-ids-revista-{revista.pk}.csv"'
        return resposta

    def changelist_view(self, request, extra_context=None):
        links = []
        if request.user.has_perm("nucleo.change_revistafasciculo"):
            links.append(("Escolher template F1/F2", reverse("admin:nucleo_revista_escolher_template")))
        return super().changelist_view(request, {**(extra_context or {}), "lotes": links})

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
