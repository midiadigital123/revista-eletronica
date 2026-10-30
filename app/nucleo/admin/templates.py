"""Admin de templates de texto (S11b1; D-099, D-102, D-109, D-115, D-123, D-125).

Página "Templates": abas Textos F1 e F2 (esta changelist filtrada por fascículo),
Matrizes e Variáveis (links para os admins do S11a e do S11c).

Editar o texto = nova `TemplateVersao` (só INSERT). Fluxo do salvar, todo sob o
`BloqueioAdminMixin` (alvo = o template):
1. POST do change form com o texto mudado: `validar` (no form) e, se passou,
   a tela de impacto. Nada é gravado; o POST inteiro volta em campos hidden.
2. "Confirmar": o mesmo POST com `_confirmar` e a assinatura da tela (hash do
   texto + versão-base) passa pelo mixin (confere o bloqueio na transação),
   revalida e grava a versão nova. Assinatura que não bate (texto editado no
   hidden, versão-base mudou, expirou): reabre a tela de impacto.
3. "Voltar e editar": o mesmo POST com `_voltar` reabre o form com o texto pendente.
Texto igual ao da versão atual (só o nome mudou): salva direto, sem versão nova.
"""

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import ValidationError
from django.db import router, transaction
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode

from nucleo import texto
from nucleo.admin.bloqueio import CAMPO_SESSAO, BloqueioAdminMixin
from nucleo.models import Ano, Template
from nucleo.servicos import bloqueio
from nucleo.servicos.resolver import versao_atual
from nucleo.templates_texto import ASSINATURA, assinar, assinatura, com_uso, criar_versao, impacto, ler_assinatura
from nucleo.variaveis import VARIAVEIS


class EditorTexto(forms.Textarea):
    """Textarea + "Inserir variável" + preview ao vivo (static/nucleo/template_editor.js)."""

    template_name = "nucleo/widgets/editor_texto.html"
    fasciculo = ""  # o form preenche; no "adicionar" o JS lê o select de fascículo

    class Media:
        js = [forms.Script("nucleo/template_editor.js", defer=True)]  # {{ media }} sai no <head>
        css = {"all": ["nucleo/template_editor.css"]}

    def get_context(self, name, value, attrs):
        contexto = super().get_context(name, value, attrs)
        contexto["widget"].update(
            variaveis=VARIAVEIS, fasciculo=self.fasciculo, preview=reverse("template_preview")
        )
        return contexto


class TemplateForm(forms.ModelForm):
    # strip=False: o texto volta igual ao salvo e não gera versão nova à toa.
    texto = forms.CharField(
        strip=False, max_length=texto.TEXTO_MAX, widget=EditorTexto(attrs={"rows": 30, "spellcheck": "true"})
    )

    class Meta:
        model = Template
        fields = ["ano", "componente", "fasciculo", "nome"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.atual = versao_atual(self.instance.pk) if self.instance.pk else None
        if self.atual is not None:
            self.fields["texto"].initial = self.atual.texto
        self.fields["texto"].widget.fasciculo = self.instance.fasciculo or ""

    def clean_texto(self):
        return self.cleaned_data["texto"].replace("\r\n", "\n").replace("\r", "\n")

    def clean(self):
        dados = super().clean()
        if "_voltar" in self.data:
            # ponytail: "voltar" reaproveita o caminho do form inválido (mantém bloqueio e texto).
            raise ValidationError("Voltou da tela de impacto: nada foi salvo. Revise e salve de novo.")
        fasciculo = self.instance.fasciculo if self.instance.pk else dados.get("fasciculo")
        if "texto" in dados and fasciculo:
            try:
                texto.validar(dados["texto"], fasciculo)
            except ValidationError as e:
                self.add_error("texto", e)
        return dados

    @property
    def texto_mudou(self):
        return self.atual is None or self.cleaned_data["texto"] != self.atual.texto


@admin.register(Template)
class TemplateAdmin(BloqueioAdminMixin, admin.ModelAdmin):
    form = TemplateForm
    change_list_template = "nucleo/template_change_list.html"
    list_display = ("nome", "ano", "componente", "fasciculo", "versao", "usado_por")
    list_select_related = ("ano", "componente")
    list_filter = ("fasciculo", "ano", "componente")
    ordering = ("-ano__ano", "componente__codigo", "fasciculo", "nome")
    search_fields = ("nome",)
    actions = None  # o mixin proíbe actions de escrita (delete_selected incluso)

    def get_queryset(self, request):
        return com_uso(super().get_queryset(request))

    @admin.display(description="Versão", ordering="n_versao")
    def versao(self, obj):
        return obj.n_versao

    @admin.display(description="Uso", ordering="n_usado")
    def usado_por(self, obj):
        url = reverse("painel", args=[obj.ano.ano]) + "?" + urlencode({"template": obj.pk})
        return format_html('<a href="{}">usado por {} ({} com cópia)</a>', url, obj.n_usado, obj.n_copia)

    def changelist_view(self, request, extra_context=None):
        variaveis = reverse("admin:nucleo_projeto_variaveis")
        filtrado = request.GET.get("ano__id__exact", "")
        ano = Ano.objects.filter(pk=filtrado).first() if filtrado.isdigit() else None
        if ano:
            variaveis += "?" + urlencode({"ano": ano.ano})  # o ano do filtro da lista
        abas = [
            ("Textos F1", "?fasciculo__exact=F1", request.GET.get("fasciculo__exact") == "F1"),
            ("Textos F2", "?fasciculo__exact=F2", request.GET.get("fasciculo__exact") == "F2"),
            ("Matrizes", reverse("admin:nucleo_matriz_changelist"), False),
            ("Variáveis", variaveis, False),  # planilha T17: variáveis = colunas de Projeto (D-100)
        ]
        return super().changelist_view(request, {**(extra_context or {}), "abas": abas})

    # --- Permissões: salvar o texto cria TemplateVersao, então exige add_templateversao também.

    def has_add_permission(self, request):
        return super().has_add_permission(request) and request.user.has_perm("nucleo.add_templateversao")

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj) and request.user.has_perm(
            "nucleo.add_templateversao"
        )

    def get_readonly_fields(self, request, obj=None):
        # Trocar ano/componente/fascículo quebraria as FKs compostas das revistas (D-098).
        return ("ano", "componente", "fasciculo") if obj else ()

    def get_fields(self, request, obj=None):
        if obj is not None and not self.has_change_permission(request, obj):
            return ["ano", "componente", "fasciculo", "nome", "texto_atual"]  # só leitura
        return ["ano", "componente", "fasciculo", "nome", "texto"]

    @admin.display(description="Texto")
    def texto_atual(self, obj):
        atual = versao_atual(obj.pk)
        return format_html('<pre class="texto-template">{}</pre>', atual.texto if atual else "")

    # --- Salvar -> tela de impacto -> confirmar

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not form.texto_mudou:
            return
        numero = criar_versao(obj, form.cleaned_data["texto"], request.user)
        if numero:
            self.message_user(request, f"Versão {numero} criada.")

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        if request.method == "POST" and object_id and "_voltar" not in request.POST:
            obj = self.get_object(request, unquote(object_id))
            if obj is not None and self.has_change_permission(request, obj):
                resposta = self._tela_impacto(request, obj)
                if resposta is not None:
                    return resposta
        return super().changeform_view(request, object_id, form_url, extra_context)

    def _tela_impacto(self, request, obj):
        """Resposta da tela de impacto, ou None para seguir o fluxo normal do admin
        (form inválido, texto igual, confirmação com assinatura válida ou bloqueio
        perdido: o mixin trata)."""
        form = self.get_form(request, obj, change=True)(request.POST, instance=obj)
        if not form.is_valid() or not form.texto_mudou:
            return None
        esperada = assinatura(form.cleaned_data["texto"], form.atual)
        if "_confirmar" in request.POST and ler_assinatura(request.POST) == esperada:
            return None
        sessao = request.POST.get(CAMPO_SESSAO, "")
        with transaction.atomic(using=router.db_for_write(Template)):
            if not bloqueio.conferir_na_transacao(obj, request.user, sessao):
                return None
        if "_confirmar" in request.POST:
            messages.warning(request, "O texto ou a versão atual mudou desde a tela de impacto: confira de novo.")
        obj.refresh_from_db()  # o form alterou a instância em memória
        dados = [
            (k, v)
            for k, valores in request.POST.lists()
            # _continue etc. seguem para o confirmar; sessão e assinatura saem à parte.
            if k not in ("csrfmiddlewaretoken", CAMPO_SESSAO, ASSINATURA, "_confirmar")
            for v in valores
        ]
        dados.append((ASSINATURA, assinar(esperada)))
        contexto = {
            **self.admin_site.each_context(request),
            "opts": self.opts,
            "original": obj,
            "title": f"Impacto da mudança em {obj}",
            "revistas": self.impacto(obj, form.cleaned_data["texto"]),
            "dados": dados,
            "bloqueio": {"alvo": bloqueio.campo(obj), "id": obj.pk, "sessao": sessao},
            "bloqueio_campo_sessao": CAMPO_SESSAO,
        }
        return TemplateResponse(request, "nucleo/template_impacto.html", contexto)

    impacto = staticmethod(impacto)  # nucleo/templates_texto.py
