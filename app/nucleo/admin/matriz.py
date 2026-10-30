"""Admin da matriz (S11a): Matriz, MatrizEtapaCC (MEC), Descritor e Tarefa.

- Matriz: "Duplicar" (de qualquer ano, D-101, D-124), "Diferenças da origem" (só consulta,
  D-113) e "Reimportar" com confirmação forte (D-071, D-141, D-146).
- MEC e Descritor usam o BloqueioAdminMixin com alvo = MEC (D-081): a tarefa é inline
  do descritor, o descritor é inline da MEC. Sem actions nem list_editable (o mixin proíbe).
- Antes de salvar, o formulário pede confirmação quando a edição afeta revistas ativas (D-076).
- MEC nasce pela importação ou pela duplicação; ninguém exclui (D-136).
- Arquivo do item (D-180): botão "Arquivo do item" em cada tarefa abre um <dialog> que posta
  em `item_view`, com a sessão do bloqueio da página e a confirmação de impacto.
- Tarefa e descritor se excluem só pela tela de confirmação forte (D-181): revistas afetadas,
  as que perdem o "Validado" e o código digitado. Os inlines não têm "Excluir?".
"""

from pathlib import PurePosixPath

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied
from django.core.files.storage import default_storage
from django.db import router, transaction
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.html import format_html, format_html_join

from nucleo.admin.bloqueio import CAMPO_SESSAO, BloqueioAdminMixin, aviso
from nucleo.admin.lote import rota
from nucleo.matriz import (  # formulários comuns ao admin e à página própria (urls/ui_matriz.py)
    DescritorForm,
    DuplicarForm,
    ExcluirForm,
    ImpactoForm,
    ItemForm,
    LinhasField,
    MatrizForm,
    ReimportarForm,
    gravar_item,
    reimportar,
)  # fmt: skip
from nucleo.models import Descritor, Matriz, MatrizEtapaCC, Tarefa
from nucleo.servicos import bloqueio
from nucleo.servicos.matriz import (
    DuplicacaoRecusada,
    diferencas,
    duplicar_matriz,
    impacto,
    revistas_afetadas,
)
from nucleo.urls.preview import TIPOS_ITEM, servir

# --- Matriz -------------------------------------------------------------------------------


class MecInline(admin.TabularInline):
    model = MatrizEtapaCC
    fields = ("etapa", "componente", "passo")
    readonly_fields = fields
    show_change_link = True
    extra = max_num = 0
    can_delete = False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("etapa", "componente")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Matriz)
class MatrizAdmin(admin.ModelAdmin):
    form = MatrizForm
    list_display = ("nome", "ano", "duplicada_de")
    list_filter = ("ano",)
    list_select_related = ("ano", "duplicada_de__ano")
    search_fields = ("nome",)
    inlines = [MecInline]

    def get_fields(self, request, obj=None):
        return ("nome", "ano", "duplicada_de") if obj else ("nome", "ano")

    def get_readonly_fields(self, request, obj=None):
        return ("ano", "duplicada_de") if obj else ()

    def get_urls(self):
        return [
            rota(self, "<int:pk>/duplicar/", self.duplicar_view, "duplicar"),
            rota(self, "<int:pk>/reimportar/", self.reimportar_view, "reimportar"),
            rota(self, "<int:pk>/diferencas/", self.diferencas_view, "diferencas"),
            *super().get_urls(),
        ]

    def _pagina(self, request, matriz, template, **contexto):
        contexto = {**self.admin_site.each_context(request), "opts": self.opts, "original": matriz, **contexto}
        return TemplateResponse(request, template, contexto)

    def _matriz(self, request, pk, permissao):
        matriz = get_object_or_404(Matriz.objects.select_related("ano", "duplicada_de__ano"), pk=pk)
        if not self.has_view_permission(request, matriz) or not permissao(request, matriz):
            raise PermissionDenied
        return matriz

    def duplicar_view(self, request, pk):
        origem = self._matriz(request, pk, lambda r, m: self.has_add_permission(r))
        form = DuplicarForm(request.POST or None, initial={"nome": f"{origem.nome} (cópia)"})
        if request.method == "POST" and form.is_valid():
            try:
                nova = duplicar_matriz(origem, form.cleaned_data["ano"], form.cleaned_data["nome"], request.user)
            except DuplicacaoRecusada as e:
                form.add_error(None, str(e))
            else:
                messages.success(request, f"Matriz {nova} criada como cópia de {origem}.")
                return redirect("admin:nucleo_matriz_change", nova.pk)
        return self._pagina(
            request, origem, "nucleo/admin_form.html", form=form, title=f"Duplicar {origem}",
            botao="Duplicar", aviso="Copia etapas × CC, descritores e tarefas. A cópia só guarda de onde veio.",
        )  # fmt: skip

    def reimportar_view(self, request, pk):
        matriz = self._matriz(request, pk, self.has_change_permission)
        form = ReimportarForm(request.POST or None, request.FILES or None)
        if request.method == "POST" and form.is_valid():
            if self._reimportar(request, matriz, form):
                return redirect("admin:nucleo_matriz_change", matriz.pk)
        return self._pagina(
            request, matriz, "nucleo/admin_form.html", form=form, title=f"Reimportar {matriz}",
            botao="Importar",
            aviso="Só as etapa × CC do arquivo são tocadas. Nelas, descritores e tarefas são "
            "apagados e recriados a partir do arquivo; edições feitas no sistema se perdem.",
        )  # fmt: skip

    def _reimportar(self, request, matriz, form):
        sucesso = reimportar(matriz, form)
        if sucesso:
            messages.success(request, sucesso)
        return bool(sucesso)

    def diferencas_view(self, request, pk):
        matriz = self._matriz(request, pk, lambda r, m: True)
        return self._pagina(
            request, matriz, "nucleo/matriz_diferencas.html",
            title=f"Diferenças de {matriz} para {matriz.duplicada_de or 'a origem'}",
            linhas=diferencas(matriz),
        )  # fmt: skip


# --- Impacto (D-076) ----------------------------------------------------------------------


class MatrizEditAdmin(BloqueioAdminMixin, admin.ModelAdmin):
    """Base de MEC e Descritor: bloqueio por MEC + confirmação de impacto."""

    form = ImpactoForm
    actions = None

    def mec(self, obj):
        raise NotImplementedError

    def alvo_do_bloqueio(self, obj):
        return self.mec(obj)

    def get_form(self, request, obj=None, change=False, **kwargs):
        form = super().get_form(request, obj, change=change, **kwargs)
        # get_form devolve uma classe nova por chamada: o atributo não vaza entre pedidos.
        form.afetadas = self.afetadas(request, obj) if obj is not None else 0
        return form

    def afetadas(self, request, obj):
        """Uma contagem por pedido: o admin chama get_form mais de uma vez."""
        cache = request.__dict__.setdefault("_revistas_afetadas", {})
        mec = self.mec(obj)
        if mec.pk not in cache:
            cache[mec.pk] = revistas_afetadas(mec)
        return cache[mec.pk]

    def has_add_permission(self, request):
        return False  # MEC nasce na importação/duplicação; descritor, no inline da MEC


class DescritorInline(admin.TabularInline):
    model = Descritor
    fields = ("codigo", "descricao", "ordem")
    show_change_link = True
    extra = 0
    can_delete = False  # só pela confirmação forte do DescritorAdmin (D-181)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "descricao":
            kwargs["widget"] = forms.Textarea(attrs={"rows": 2, "cols": 60})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(MatrizEtapaCC)
class MatrizEtapaCCAdmin(MatrizEditAdmin):
    list_display = ("matriz", "etapa", "componente", "passo")
    list_filter = ("ano", "matriz", "componente")
    list_select_related = ("matriz__ano", "etapa__ano", "componente__ano")
    fields = ("matriz", "etapa", "componente", "passo", "confirmar_impacto")
    readonly_fields = ("matriz", "etapa", "componente")
    inlines = [DescritorInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("matriz__ano", "etapa", "componente")

    def mec(self, obj):
        return obj

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "passo":  # D-155: intervalo mínimo; vazio = sem linhas vazias
            return forms.IntegerField(
                label="Intervalo mínimo", required=False, min_value=1,
                help_text="Vazio = sem linhas vazias. Os projetos podem sobrescrever.",
            )  # fmt: skip
        return super().formfield_for_dbfield(db_field, request, **kwargs)


class TarefaInline(admin.TabularInline):
    model = Tarefa
    fields = ("inicio", "fim", "texto", "ordem", "acoes")
    readonly_fields = ("acoes",)
    extra = 0
    can_delete = False  # só pela confirmação forte (D-181)
    editavel = pode_excluir = False  # o DescritorAdmin preenche por pedido (instância nova a cada um)

    @admin.display(description="Item e exclusão")
    def acoes(self, obj):
        if obj.pk is None:
            return ""
        partes = []
        if obj.arquivo:
            partes.append(format_html("{} ", PurePosixPath(obj.arquivo).suffix.lstrip(".").upper()))
        if self.editavel:
            partes.append(format_html(
                '<button type="button" class="button" data-dialogo="item-{}" '
                'aria-label="Arquivo do item da tarefa {}">Arquivo do item</button> ', obj.pk, obj.codigo,
            ))  # fmt: skip
        if self.pode_excluir:
            url = reverse("admin:nucleo_descritor_excluir_tarefa", args=[obj.descritor_id, obj.pk])
            partes.append(format_html('<a href="{}" class="deletelink">Excluir tarefa {}</a>', url, obj.codigo))
        return format_html_join("", "{}", ((p,) for p in partes))

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "texto":
            kwargs["widget"] = forms.Textarea(attrs={"rows": 2, "cols": 60})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(Descritor)
class DescritorAdmin(MatrizEditAdmin):
    list_display = ("codigo", "matriz_etapa_cc_rotulo", "ordem")
    list_filter = ("matriz_etapa_cc__matriz", "matriz_etapa_cc__etapa__codigo", "matriz_etapa_cc__componente__codigo")
    list_select_related = ("matriz_etapa_cc__matriz", "matriz_etapa_cc__etapa", "matriz_etapa_cc__componente")
    search_fields = ("codigo", "descricao")
    fields = (
        "matriz_etapa_cc", "codigo", "descricao", "prerequisitos", "praticas", "conhecimento",
        "habilidades_relacionadas", "habilidade_correspondente", "ordem", "confirmar_impacto",
    )  # fmt: skip
    readonly_fields = ("matriz_etapa_cc",)
    inlines = [TarefaInline]
    form = DescritorForm

    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            "matriz_etapa_cc__matriz__ano", "matriz_etapa_cc__etapa", "matriz_etapa_cc__componente"
        )

    def mec(self, obj):
        return obj.matriz_etapa_cc

    @admin.display(description="Etapa × CC")
    def matriz_etapa_cc_rotulo(self, obj):
        m = obj.matriz_etapa_cc
        return f"{m.matriz.nome} · {m.etapa.codigo} {m.componente.codigo}"

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == "prerequisitos":
            return LinhasField(label="Pré-requisitos", required=False, help_text="Um por linha.")
        return super().formfield_for_dbfield(db_field, request, **kwargs)

    change_form_template = "nucleo/descritor_change_form.html"

    def get_urls(self):
        def rota(sufixo, view, nome):
            return path(
                f"<int:pk>/tarefa/<int:tarefa_pk>/{sufixo}/", self.admin_site.admin_view(view),
                name=f"nucleo_descritor_{nome}",
            )  # fmt: skip

        return [
            rota("item", self.item_view, "item"),
            rota("excluir", self.excluir_tarefa_view, "excluir_tarefa"),
            *super().get_urls(),
        ]

    def get_inline_instances(self, request, obj=None):
        inlines = super().get_inline_instances(request, obj)
        editavel = obj is not None and self._edita_tarefa(request, obj)
        pode_excluir = obj is not None and self._exclui_tarefa(request, obj)
        for inline in inlines:
            inline.editavel, inline.pode_excluir = editavel, pode_excluir
        return inlines

    def _edita_tarefa(self, request, descritor):
        return self.has_change_permission(request, descritor) and request.user.has_perm("nucleo.change_tarefa")

    def _exclui_tarefa(self, request, descritor):
        return request.user.has_perm("nucleo.delete_tarefa") and not _de_outro(request, descritor.matriz_etapa_cc)

    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):
        # Os <dialog> do item ficam fora do form do admin (form não aninha); só com o bloqueio.
        if obj is not None and context.get("bloqueio") and self._edita_tarefa(request, obj):
            tarefas = list(obj.tarefa_set.order_by("ordem", "pk"))
            revistas = impacto(obj.matriz_etapa_cc) if tarefas else []
            form = _item_form(len(revistas))
            context["itens"] = [
                (t, form(instance=t, auto_id=f"item{t.pk}_%s"), PurePosixPath(t.arquivo or "")) for t in tarefas
            ]
            context["item_impacto"] = (len(revistas), sum(v for _, v in revistas))
        return super().render_change_form(request, context, add, change, form_url, obj)

    def _descritor_e_tarefa(self, request, pk, tarefa_pk):
        descritor = self.get_object(request, str(pk))
        if descritor is None:
            raise Http404
        return descritor, get_object_or_404(Tarefa, pk=tarefa_pk, descritor=descritor)

    def item_view(self, request, pk, tarefa_pk):
        """GET: o arquivo do item (link do modal). POST: envia, troca ou remove (D-180)."""
        descritor, tarefa = self._descritor_e_tarefa(request, pk, tarefa_pk)
        if request.method != "POST":
            tipo = TIPOS_ITEM.get(PurePosixPath(tarefa.arquivo or "").suffix)
            if not self.has_view_permission(request, descritor) or tipo is None:
                raise Http404
            try:
                return servir(default_storage.open(tarefa.arquivo), tipo, as_attachment=True)
            except FileNotFoundError:
                raise Http404 from None
        if not self._edita_tarefa(request, descritor):
            raise PermissionDenied
        mec, sessao = descritor.matriz_etapa_cc, request.POST.get(CAMPO_SESSAO, "")
        voltar = redirect("admin:nucleo_descritor_change", descritor.pk)
        form = _item_form(revistas_afetadas(mec))(request.POST, request.FILES, instance=tarefa)
        with transaction.atomic(using=router.db_for_write(Tarefa)):
            if not bloqueio.conferir_na_transacao(mec, request.user, sessao):
                messages.error(
                    request, "Arquivo do item não salvo: você perdeu o bloqueio de edição. Recarregue e tente de novo."
                )
                return voltar
            erro = self._gravar_item(request, tarefa, form)
        bloqueio.liberar(mec, request.user, sessao)  # a próxima página readquire com sessão nova
        if erro:
            messages.error(request, f"Arquivo do item da tarefa {tarefa.codigo} não salvo: {erro}")
        return voltar

    def _gravar_item(self, request, tarefa, form):
        """Grava e devolve None, ou devolve o motivo da recusa (causa + correção)."""
        sucesso, erro = gravar_item(tarefa, form, "_remover" in request.POST)
        if sucesso:
            messages.success(request, sucesso)
        return erro

    # --- Exclusão com confirmação forte (D-181) --------------------------------------

    def delete_view(self, request, object_id, extra_context=None):
        descritor = self.get_object(request, unquote(object_id))
        if descritor is None:
            raise Http404
        if not self.has_delete_permission(request, descritor):
            raise PermissionDenied
        mec = descritor.matriz_etapa_cc
        voltar = reverse("admin:nucleo_matrizetapacc_change", args=[mec.pk])
        return _excluir(self, request, descritor, "descritor", mec, voltar)

    def excluir_tarefa_view(self, request, pk, tarefa_pk):
        descritor, tarefa = self._descritor_e_tarefa(request, pk, tarefa_pk)
        if not self._exclui_tarefa(request, descritor):
            raise PermissionDenied
        voltar = reverse("admin:nucleo_descritor_change", args=[descritor.pk])
        return _excluir(self, request, tarefa, "tarefa", descritor.matriz_etapa_cc, voltar)


def _de_outro(request, mec):
    """Outro usuário edita a MEC: excluir fica negado (mesma regra do BloqueioAdminMixin)."""
    atual = bloqueio.quem_bloqueia(mec)
    return atual is not None and atual.usuario_id != request.user.pk


def _item_form(afetadas):
    return type("ItemForm", (ItemForm,), {"afetadas": afetadas})


def _excluir(model_admin, request, obj, rotulo, mec, voltar):
    """Tela intermediária: revistas afetadas, as que perdem o "Validado" e o código digitado."""
    codigo = obj.codigo
    form = ExcluirForm(request.POST or None, codigo=codigo)
    # A página trava a MEC com uma sessão própria (como o change form); o POST a confere com
    # FOR SHARE dentro da transação da exclusão.
    sessao = request.POST.get(CAMPO_SESSAO, "")
    if request.method == "POST" and form.is_valid():
        with transaction.atomic(using=router.db_for_write(type(obj))):
            if not bloqueio.conferir_na_transacao(mec, request.user, sessao):
                messages.error(request, "Nada foi excluído: você perdeu o bloqueio de edição. Recarregue e tente de novo.")
                return redirect(voltar)
            obj.delete()
        bloqueio.liberar(mec, request.user, sessao)
        excluido = "excluída" if rotulo == "tarefa" else "excluído"
        messages.success(request, f"{rotulo.capitalize()} {codigo} {excluido}.")
        return redirect(voltar)
    if request.method != "POST":
        sessao = bloqueio.nova_sessao()
        if not bloqueio.adquirir(mec, request.user, sessao):
            sessao = ""
            messages.warning(request, aviso(request, mec))
    revistas = impacto(mec)
    contexto = {
        **model_admin.admin_site.each_context(request),
        "opts": model_admin.opts, "original": obj, "title": f"Excluir {rotulo} {codigo}",
        "rotulo": rotulo, "form": form, "revistas": revistas, "voltar": voltar, "mec": mec,
        "validadas": sum(v for _, v in revistas), "bloqueio_campo_sessao": CAMPO_SESSAO,
        "bloqueio": {"alvo": bloqueio.campo(mec), "id": mec.pk, "sessao": sessao} if sessao else None,
    }  # fmt: skip
    return TemplateResponse(request, "nucleo/excluir_confirmar.html", contexto)
