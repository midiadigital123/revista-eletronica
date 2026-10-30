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
from django.urls import path, reverse
from django.utils.functional import cached_property
from django.utils.html import format_html, format_html_join

from nucleo.admin.matriz import ImpactoForm
from nucleo.models import Ano, Componente, CorPadrao, Etapa, Parceiro, ProjetoCor, Revista
from nucleo.servicos import resolver, validacao
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


# --- Padrões do ano: impacto de nome/cor (T07, D-076, D-175) ------------------------------

CAMPOS_DO_HASH = {"nome", "cor"}
MAX_NOMES = 20


def revistas_afetadas_padrao(cor_padrao, campos):
    """(afetadas, perdem o "Validado") ao mudar `campos` ⊆ {"nome", "cor"} do padrão do ano.

    Afetada: revista ativa do ano que tem o padrão N em alguma etapa e que não sobrescreve no
    projeto o que muda (`pdNN` para o nome, `ProjetoCor` N para a cor). Arquivada lê a foto.
    """
    n, pd = cor_padrao.padrao, f"pd{cor_padrao.padrao:02d}"
    com_cor = set(ProjetoCor.objects.filter(padrao=n, projeto__ano_id=cor_padrao.ano_id).values_list("projeto_id", flat=True))
    afetadas, perdem = [], []
    revistas = Revista.objects.filter(ano_id=cor_padrao.ano_id, arquivada_em__isnull=True).select_related(
        "projeto__parceiro_ano__parceiro", "projeto__ano", "componente"
    ).order_by("projeto__parceiro_ano__parceiro__nome", "componente__codigo")
    for r in revistas:
        if not (("nome" in campos and not getattr(r.projeto, pd).strip())
                or ("cor" in campos and r.projeto_id not in com_cor)):
            continue  # fmt: skip
        # ponytail: resolve cada candidata no GET e no POST; guardar na sessão se ficar lento.
        resolvido = resolver.resolver(r)
        if not any(len(d["padroes"]) >= n for d in resolvido["f1"]["dados"].values()):
            continue
        afetadas.append(r)
        if validacao.validada(r, resolver.hash_validado(r, resolvido)):
            perdem.append(r)
    return afetadas, perdem


def nomes(revistas):
    resto = len(revistas) - MAX_NOMES
    lista = format_html_join(", ", "{}", ((r,) for r in revistas[:MAX_NOMES]))
    return format_html("{} e mais {}", lista, resto) if resto > 0 else lista


class PadraoImpactoForm(ImpactoForm):
    """Confirmação só quando nome/cor mudam (no GET, o pior caso: os dois). `impacto` vem do admin."""

    impacto = None  # função(campos) -> (afetadas, perdem); None na inclusão

    @cached_property
    def resultado(self):
        campos = CAMPOS_DO_HASH & set(self.changed_data) if self.is_bound else CAMPOS_DO_HASH
        return self.impacto(campos) if self.impacto and campos else ([], [])

    @property
    def afetadas(self):
        return len(self.resultado[0])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        afetadas, perdem = self.resultado
        if afetadas and perdem:
            campo = self.fields["confirmar_impacto"]
            campo.label += f"; {len(perdem)} perdem o “Validado”"
            campo.help_text = format_html(
                "Perdem o “Validado”: {}.{}", nomes(perdem),
                " As demais afetadas ainda não estavam validadas." if len(afetadas) > len(perdem) else "",
            )  # fmt: skip
        # changed_data criou os BoundFields com o rótulo antigo (o BoundField copia label e help_text).
        self._bound_fields_cache.clear()

    def clean(self):
        dados = super(ImpactoForm, self).clean()
        if self.afetadas and not dados.get("confirmar_impacto"):
            p, ano = self.instance.padrao, self.instance.ano.ano
            raise forms.ValidationError(
                f"Não salvo: mudar o nome ou a cor do Padrão {p} de {ano} afeta {self.afetadas} revista(s) "
                f"ativa(s) (as que não sobrescrevem pd{p:02d} ou a cor no projeto). "
                "Confira a lista, marque a confirmação e salve de novo."
            )
        return dados


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
