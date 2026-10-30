"""Admin de Revista: upload de SVG e capa, template por fascículo, "Baixar zip" (S15, S11c).

Edita com o bloqueio do projeto (D-140, D-143). `hash_validado`, `validado_*` e `arquivada_em`
são só leitura: só os serviços os escrevem (D-142). Nunca inclui nem exclui (D-117).
Textos (S11b2, D-104, D-115): um fieldset por fascículo, um campo por seção (o título vem do
template e não se edita). Salvar uma seção mudada cria a cópia (`RevistaSecao`) com a versão do
template mostrada na página (hidden `versao__F1`), então uma versão nova entre abrir e salvar
ainda aparece como aviso. Seção desatualizada mostra o diff "seu texto | template novo"; mexer
no texto ou marcar "Manter meu texto" salva a cópia com a versão nova (o aviso some); "Descartar
cópia" apaga a cópia (volta ao vivo). Tudo grava dentro da transação do mixin (bloqueio).
Trocar o template de um fascículo com cópias exige digitar "descartar N cópia(s)" no inline;
apaga as cópias e troca o template na mesma transação (D-093, D-104).

"Validado" (S12, D-074, D-089): um form separado do change form (não reenvia uploads nem textos
não salvos) leva o hash da revista exibida e a sessão do bloqueio da aba para `validar/`.

Forms, textos, arquivos e estado do "Validado" moram em `nucleo/revista.py` (a página própria usa
o mesmo, D-183); aqui ficam o ModelAdmin, o inline e o widget com preview.

Upload com ids faltando GRAVA e avisa (decisão do S11c): o template pode ganhar ou perder
seções depois, e a pendência `ids_svg` do resolver já bloqueia o "Validado".
"""

import csv
import io
import logging

from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from nucleo.admin import lote
from nucleo.admin.bloqueio import CAMPO_SESSAO, BloqueioAdminMixin
from nucleo.admin.templates import EditorTexto
from nucleo.models import Ano, Revista, RevistaFasciculo
from nucleo.revista import (  # regra comum ao admin e à página própria (D-183)
    FasciculoForm,
    RevistaForm,
    avisar_descartes,
    aviso_ids,
    blocos_de_texto,
    estado_validacao,
    faixas_sem_template,
    form_de_textos,
    gravar_arquivos,
    gravar_textos,
    ids_do_f2,
    nome,
)
from nucleo.servicos import arquivos, bloqueio, resolver, validacao
from nucleo.servicos.empacotar import Pendente, zip_revista

UPLOADS = ("arquivo_svg", "arquivo_capa")
log = logging.getLogger(__name__)


class FasciculoInline(admin.TabularInline):
    model = RevistaFasciculo
    form = FasciculoForm
    fields = ("fasciculo", "template", "confirmacao")
    readonly_fields = ("fasciculo",)
    extra = 0
    can_delete = False

    def get_formset(self, request, obj=None, **kwargs):
        # A troca que apaga cópias roda sob as permissões de editar textos (D-170, D-171).
        pode = request.user.has_perms(["nucleo.add_revistasecao", "nucleo.change_revistasecao"])
        kwargs["form"] = type("FasciculoForm", (self.form,), {"pode_descartar": pode})
        return super().get_formset(request, obj, **kwargs)

    def get_fields(self, request, obj=None):
        if not self.has_change_permission(request, obj):
            return ("fasciculo", "template")  # só leitura: sem o campo de confirmação
        return self.fields

    def has_add_permission(self, request, obj=None):
        return False  # nascem com a revista (S06)


# --- Textos por seção (S11b2) ---------------------------------------------------


class EditorSecao(EditorTexto):
    """EditorTexto de um corpo só: o preview recebe `## id` + título + corpo, sem validar o documento."""

    cabecalho = ""

    def get_context(self, name, value, attrs):
        contexto = super().get_context(name, value, attrs)
        contexto["widget"]["cabecalho"] = self.cabecalho
        return contexto


def editor_secao(s):
    widget = EditorSecao(attrs={"rows": 6, "spellcheck": "true"})
    widget.cabecalho = f"## {s.id}\n{s.titulo}\n\n"
    return widget


def celula(valor):
    """Célula de CSV que o Excel não executa como fórmula (=, +, -, @, tab, CR no início)."""
    return "'" + valor if valor[:1] in ("=", "+", "-", "@", "\t", "\r") else valor


@admin.register(Revista)
class RevistaAdmin(BloqueioAdminMixin, admin.ModelAdmin):
    form = RevistaForm
    change_form_template = "nucleo/revista_change_form.html"
    change_list_template = "nucleo/change_list_lotes.html"
    list_display = ("projeto", "componente", "arquivada_em", "preview")
    list_select_related = ("projeto", "componente")
    list_filter = ("ano", "componente")
    readonly_fields = (
        "projeto", "componente", "ano", "svg_f2", "svg_sha256", "conferencia_ids", "capa", "capa_sha256",
        "hash_validado", "validado_em", "validado_por", "arquivada_em", "textos",
    )  # fmt: skip
    fieldsets = (
        (None, {"fields": ("projeto", "componente", "ano")}),
        ("SVG do F2", {"fields": ("arquivo_svg", "svg_f2", "svg_sha256", "conferencia_ids")}),
        ("Capa", {"fields": ("arquivo_capa", "capa", "capa_sha256")}),
        ("Validação", {"fields": ("hash_validado", "validado_em", "validado_por", "arquivada_em")}),
    )
    inlines = [FasciculoInline]
    actions = ["baixar_zip", "baixar_planilhas"]  # só leitura: o mixin proíbe actions de escrita

    def alvo_do_bloqueio(self, obj):
        return obj.projeto  # revista trava o projeto dela (D-140)

    def pode_editar_textos(self, request, obj):
        return self.has_change_permission(request, obj) and request.user.has_perms(
            ["nucleo.add_revistasecao", "nucleo.change_revistasecao"]
        )

    def _blocos(self, request, obj):
        """Blocos de texto da revista, lidos uma vez por requisição (fieldsets e form usam)."""
        if getattr(request, "_blocos_revista", (None,))[0] != obj.pk:
            request._blocos_revista = (obj.pk, blocos_de_texto(obj))
        return request._blocos_revista[1]

    def get_fieldsets(self, request, obj=None):
        if obj is not None and not self.has_change_permission(request, obj):
            # Sem os campos de upload: o admin os mostraria como "-" na tela só leitura.
            return [
                (titulo, {**op, "fields": [f for f in op["fields"] if f not in UPLOADS]}) for titulo, op in self.fieldsets
            ] + [("Textos", {"fields": ["textos"]})]
        if obj is None:
            return self.fieldsets
        if not self.pode_editar_textos(request, obj):
            return [*self.fieldsets, ("Textos", {"fields": ["textos"]})]
        textos = []
        for b in self._blocos(request, obj):
            f, campos = b.rf.fasciculo, [nome("versao", b.rf.fasciculo)]
            for s in b.secoes:
                campos.append(nome("secao", f, s.id))
                campos += [nome(t, f, s.id) for t, sim in (("manter", s.desatualizada), ("descartar", s.copia)) if sim]
            velhas = [s.id for s in b.secoes if s.desatualizada]
            descricao = (
                format_html('<strong class="impacto-alerta">Seções desatualizadas: {}.</strong>', ", ".join(velhas))
                if velhas
                else ""
            )
            textos.append((f"Textos do {f} ({b.rf.template.nome}, versão {b.versao.numero})", {"fields": campos, "description": descricao}))
        if faixas := faixas_sem_template(obj):
            textos.append(("Textos sem template", {"fields": [], "description": faixas}))
        return [*self.fieldsets, *textos]

    def get_form(self, request, obj=None, **kwargs):
        if obj is not None and self.pode_editar_textos(request, obj):
            blocos = self._blocos(request, obj)
            kwargs["form"] = form_de_textos(blocos, editor_secao)
        return super().get_form(request, obj, **kwargs)

    @admin.display(description="Textos")
    def textos(self, obj):
        if obj.arquivada_em is not None:
            # Arquivada: as seções da foto de arquivamento (D-117), já renderizadas e escapadas.
            r = resolver.resolver(resolver.carregar(obj.pk))
            return mark_safe("".join(
                r[f]["faixa"] if r[f]["secoes"] is None else format_html_join(
                    "", '<h4>{} {} · {}</h4><div class="texto-template">{}</div>',
                    ((f.upper(), s["id"], mark_safe(s["titulo"]), mark_safe(s["corpo"])) for s in r[f]["secoes"]),
                )
                for f in ("f1", "f2")
            ))  # fmt: skip
        return format_html_join(
            "",
            '<h4>{} {} · {}</h4><pre class="texto-template">{}</pre>',
            ((b.rf.fasciculo, s.id, s.titulo, s.corpo) for b in blocos_de_texto(obj) for s in b.secoes),
        ) + faixas_sem_template(obj)

    @admin.display(description="Preview")
    def preview(self, obj):
        rotulo = "versão arquivada ↗" if obj.arquivada_em else "preview ↗"  # arquivada: a foto (D-117)
        return format_html('<a href="{}" target="_blank" rel="noopener">{}</a>', reverse("preview", args=[obj.pk]), rotulo)

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
        # Nenhum campo do modelo é editável aqui (todos readonly): só uploads e textos.
        gravar_arquivos(request, obj, form.cleaned_data)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)  # inline antes: troca de template
        avisar_descartes(request, [f for fs in formsets for f in fs.forms])
        gravar_textos(request, form)

    def get_urls(self):
        return [
            lote.rota(self, "escolher-template/", lambda r: lote.escolher_template(self, r), "escolher_template"),
            lote.rota(self, "<int:pk>/gabarito-ids/", self.gabarito_ids, "gabarito_ids"),
            lote.rota(self, "<int:pk>/validar/", require_POST(self.validar_view), "validar"),
        ] + super().get_urls()

    def change_view(self, request, object_id, form_url="", extra_context=None):
        obj = self.get_object(request, unquote(object_id)) if request.method == "GET" else None
        # Só no GET (no POST o resultado se perderia) e depois da permissão de ver.
        if obj is not None and self.has_view_or_change_permission(request, obj):
            extra_context = {
                **(extra_context or {}),
                "validacao": {
                    **estado_validacao(obj.pk),
                    "pode": request.user.has_perm("nucleo.validar_revista"),
                    "url": reverse("admin:nucleo_revista_validar", args=[obj.pk]),
                },
            }
        return super().change_view(request, object_id, form_url, extra_context)

    def validar_view(self, request, pk):
        """POST do botão "Validado": confere o bloqueio da aba e o hash visto (D-089)."""
        if not request.user.has_perm("nucleo.validar_revista"):
            raise PermissionDenied
        alvo = self.alvo_do_bloqueio(get_object_or_404(Revista.objects.select_related("projeto"), pk=pk))
        sessao = request.POST.get(CAMPO_SESSAO, "")
        with transaction.atomic():
            if bloqueio.conferir_na_transacao(alvo, request.user, sessao):
                motivo = validacao.validar(pk, request.POST.get("hash_visto", ""), request.user)
            else:
                motivo = "você não tem o bloqueio de edição desta revista; recarregue a página"
        # Libera para a próxima carga readquirir (o beacon do pagehide pode chegar depois).
        try:
            bloqueio.liberar(alvo, request.user, sessao)
        except Exception:  # o clique já gravou; o bloqueio expira sozinho em 30 s
            log.exception("Falha ao liberar o bloqueio depois de validar")
        if motivo:
            messages.error(request, f"Não validada: {motivo.rstrip('.')}.")
        else:
            messages.success(request, "Revista validada.")
        return HttpResponseRedirect(reverse("admin:nucleo_revista_change", args=[pk]))

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
        if ano := Ano.objects.order_by("-ano").first():
            links.append((f"Painel {ano.ano}", reverse("painel", args=[ano.ano])))
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

    @admin.action(description="Baixar planilhas", permissions=["view"])
    def baixar_planilhas(self, request, queryset):
        """Zip com as planilhas F1 e F2 (S13); a tela do impresso tem o mesmo link por revista."""
        pks = list(queryset.values_list("pk", flat=True)[:2])
        if len(pks) != 1:
            self.message_user(request, "Escolha uma revista por vez para baixar as planilhas.", messages.ERROR)
            return None
        return HttpResponseRedirect(reverse("impresso_planilhas", args=pks))
