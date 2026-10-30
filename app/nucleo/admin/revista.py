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

Upload com ids faltando GRAVA e avisa (decisão do S11c): o template pode ganhar ou perder
seções depois, e a pendência `ids_svg` do resolver já bloqueia o "Validado".
"""

import csv
import difflib
import io
import logging
from typing import NamedTuple

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.utils import unquote
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from nucleo import texto
from nucleo.admin import lote
from nucleo.admin.bloqueio import CAMPO_SESSAO, BloqueioAdminMixin
from nucleo.admin.templates import EditorTexto
from nucleo.models import Ano, Revista, RevistaFasciculo, RevistaSecao, Template
from nucleo.servicos import arquivos, bloqueio, resolver, validacao
from nucleo.servicos.empacotar import Pendente, zip_revista

UPLOADS = ("arquivo_svg", "arquivo_capa")
log = logging.getLogger(__name__)


class RevistaForm(forms.ModelForm):
    # Validam no clean (erro no campo); gravam no save_model, depois do form todo válido.
    arquivo_svg = forms.FileField(
        required=False, label="Trocar SVG do F2", help_text="Substitui o SVG anterior. Até 3 MB. Ids pela convenção: passoN, btn-action-xx."
    )
    arquivo_capa = forms.FileField(
        required=False, label="Trocar capa", help_text="Substitui a capa anterior. PNG, JPG ou WebP até 5 MB."
    )

    blocos = ()  # get_form põe os da revista

    class Meta:
        model = Revista
        fields = []

    def clean(self):
        dados = super().clean()
        for b in self.blocos:
            f = b.rf.fasciculo
            versao = dados.get(nome("versao", f))
            if versao is not None and versao != b.versao.pk and not b.rf.template.templateversao_set.filter(pk=versao).exists():
                raise ValidationError(f"O template do {f} foi trocado depois que a página abriu: recarregue a página.")
            for s in b.secoes:
                campo = nome("secao", f, s.id)
                if campo not in self.changed_data or campo not in dados:
                    continue
                if dados.get(nome("descartar", f, s.id)):
                    self.add_error(campo, "Editou e marcou “Descartar cópia”: escolha um dos dois.")
                    continue
                try:
                    texto.validar_corpo(dados[campo])
                except ValidationError as e:
                    self.add_error(campo, e)
        return dados

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

    confirmacao = forms.CharField(
        required=False, label="Confirmação", help_text="Só para trocar o template de um fascículo com textos editados."
    )

    pode_descartar = False  # FasciculoInline.get_formset põe pelas permissões de texto

    def clean(self):
        dados = super().clean()
        rf, self.descartar = self.instance, 0
        if rf.pk and "template" in dados and dados["template"] != rf.template:
            # Trava o fascículo antes de contar (D-171): outra aba que crie cópia espera o fim
            # desta transação (gravar_textos trava o mesmo fascículo), então a contagem
            # confirmada é a que o save apaga. Roda na transação do admin.
            RevistaFasciculo.objects.select_for_update().filter(pk=rf.pk).first()
            secoes = sorted(rf.revistasecao_set.values_list("secao", flat=True))
            if secoes:
                if not self.pode_descartar:
                    raise ValidationError(
                        "Este fascículo tem textos editados: trocar o template apaga as cópias "
                        "e exige permissão de editar textos."
                    )
                frase = frase_descarte(len(secoes))
                confirmacao = " ".join(dados.get("confirmacao", "").split()).lower()
                if confirmacao != frase:
                    raise ValidationError(
                        ("A confirmação não confere com as cópias de agora. " if confirmacao else "")
                        + f"Este fascículo tem textos editados (cópias de seção: {', '.join(secoes)}). "
                        f"Trocar o template apaga essas cópias: para confirmar, digite “{frase}” em Confirmação."
                    )
                self.descartar = len(secoes)
        return dados

    def save(self, commit=True):
        if self.descartar:  # mesma transação do admin; antes do UPDATE (FK composta NO ACTION)
            RevistaSecao.objects.filter(revista_fasciculo=self.instance).delete()
        return super().save(commit)


def frase_descarte(n):
    return f"descartar {n} cópia" + ("s" if n > 1 else "")


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


class Secao(NamedTuple):
    id: str
    titulo: str
    corpo: str  # efetivo: a cópia, ou o do template
    copia: RevistaSecao | None
    desatualizada: bool
    do_template: str | None  # corpo na versão atual; None se a seção saiu do template


class Bloco(NamedTuple):
    rf: RevistaFasciculo
    versao: object  # TemplateVersao atual
    secoes: list


def blocos_de_texto(revista):
    """Um Bloco por fascículo com template (F1, F2), na ordem."""
    desatualizadas = {(c.revista_fasciculo_id, c.secao) for c in resolver.secoes_desatualizadas(revista)}
    blocos = []
    for rf in RevistaFasciculo.objects.filter(revista=revista, template__isnull=False).order_by("fasciculo"):
        versao = resolver.versao_atual(rf.template_id)
        efetivas = resolver.secoes_efetivas(rf)
        if versao is None or efetivas is None:
            continue
        do_template = texto.secoes(versao.texto)
        copias = {c.secao: c for c in rf.revistasecao_set.all()}
        secoes = [
            Secao(id_, titulo, corpo, copias.get(id_), (rf.pk, id_) in desatualizadas, do_template.get(id_, (None, None))[1])
            for id_, titulo, corpo in efetivas
        ]
        blocos.append(Bloco(rf, versao, secoes))
    return blocos


def faixas_sem_template(revista):
    """Faixa vermelha do resolver para cada fascículo sem template (D-116)."""
    sem = RevistaFasciculo.objects.filter(revista=revista, template__isnull=True).order_by("fasciculo")
    return mark_safe("".join(resolver.FAIXA_SEM_TEMPLATE.format(f) for f in sem.values_list("fasciculo", flat=True)))


def nome(tipo, fasciculo, secao=""):
    return f"{tipo}__{fasciculo}__{secao}" if secao else f"{tipo}__{fasciculo}"


class EditorSecao(EditorTexto):
    """EditorTexto de um corpo só: o preview recebe `## id` + título + corpo, sem validar o documento."""

    cabecalho = ""

    def get_context(self, name, value, attrs):
        contexto = super().get_context(name, value, attrs)
        contexto["widget"]["cabecalho"] = self.cabecalho
        return contexto


class CorpoField(forms.CharField):
    """Corpo da seção como `texto.secoes` o devolve: `\n` e sem espaço nas pontas.
    Assim o has_changed (contra o hidden do valor inicial) não vê `\r\n` do navegador como edição."""

    def to_python(self, value):
        return super().to_python(value).replace("\r\n", "\n").replace("\r", "\n")


def diff(seu, novo):
    """Tabela lado a lado do difflib (escapa &, < e >)."""
    tabela = difflib.HtmlDiff(wrapcolumn=70).make_table(seu.splitlines(), (novo or "").splitlines(), "Seu texto", "Template novo")
    return mark_safe(tabela)


def campos_de_texto(blocos):
    """Campos declarados do form (o modelform_factory recusa campo que não seja declarado)."""
    campos = {}
    for b in blocos:
        f = b.rf.fasciculo
        campos[nome("versao", f)] = forms.IntegerField(required=False, widget=forms.HiddenInput, initial=b.versao.pk)
        for s in b.secoes:
            widget = EditorSecao(attrs={"rows": 6, "spellcheck": "true"})
            widget.cabecalho = f"## {s.id}\n{s.titulo}\n\n"
            if s.desatualizada:
                ajuda = format_html(
                    '<strong class="impacto-alerta">O template mudou nesta seção depois da sua cópia.</strong> '
                    "Edite o texto ou marque “Manter meu texto” para salvar a cópia sobre a versão nova; "
                    "ou descarte a cópia.{}",
                    diff(s.corpo, s.do_template),
                )
            elif s.copia is not None:
                ajuda = "Texto editado nesta revista (cópia). Descarte para voltar ao texto do template."
            else:
                ajuda = "Texto do template. Salvar com o texto mudado cria uma cópia só desta seção."
            campos[nome("secao", f, s.id)] = CorpoField(
                label=f"{s.id} · {s.titulo}", required=False, max_length=texto.TEXTO_MAX,
                initial=s.corpo, show_hidden_initial=True, widget=widget, help_text=ajuda,
            )  # fmt: skip
            if s.desatualizada:
                campos[nome("manter", f, s.id)] = forms.BooleanField(required=False, label="Manter meu texto (o aviso some)")
            if s.copia is not None:
                campos[nome("descartar", f, s.id)] = forms.BooleanField(
                    required=False, label="Descartar cópia (volta ao texto do template)"
                )
    return campos


def gravar_textos(request, form):
    """Cria, atualiza ou descarta as cópias de seção (D-104, D-115). Roda na transação do mixin."""
    dados = form.cleaned_data
    # Trava a revista: a cascata arquiva com UPDATE na mesma linha (D-117); arquivada é foto congelada.
    # Projeto só arquiva com todas as revistas arquivadas: basta a linha da revista.
    if Revista.objects.select_for_update().get(pk=form.instance.pk).arquivada_em is not None:
        if any(n.startswith(("secao__", "manter__", "descartar__")) for n in form.changed_data):
            messages.error(request, "Textos não salvos: a revista foi arquivada (só leitura).")
        return
    # Trava os fascículos: duplo envio da mesma aba passa junto pelo FOR SHARE do bloqueio.
    rfs = {rf.pk: rf for rf in RevistaFasciculo.objects.select_for_update().filter(pk__in=[b.rf.pk for b in form.blocos])}
    for b in form.blocos:
        f, rf = b.rf.fasciculo, rfs[b.rf.pk]
        mexeu = [s.id for s in b.secoes if any(n in form.changed_data for n in (nome(t, f, s.id) for t in ("secao", "manter", "descartar")))]
        if rf.template_id != b.rf.template_id:
            if mexeu:
                messages.warning(request, f"Textos do {f} não salvos: o template do {f} foi trocado.")
            continue
        versao_id = dados.get(nome("versao", f)) or b.versao.pk  # a versão que a pessoa viu
        copias = {c.secao: c for c in RevistaSecao.objects.filter(revista_fasciculo=rf)}
        for s in b.secoes:
            copia, corpo = copias.get(s.id), dados.get(nome("secao", f, s.id))
            if dados.get(nome("descartar", f, s.id)):
                if copia is not None:
                    copia.delete()
            elif nome("secao", f, s.id) in form.changed_data:
                if copia is None and corpo == s.do_template:
                    continue  # igual ao template ao vivo: não congela a seção
                RevistaSecao.objects.update_or_create(
                    revista_fasciculo=rf, secao=s.id,
                    defaults={"texto": corpo, "template_id": rf.template_id, "template_versao_id": versao_id},
                )  # fmt: skip
            elif copia is not None and dados.get(nome("manter", f, s.id)):
                copia.template_versao_id = versao_id
                copia.save(update_fields=["template_versao"])
        if mexeu:
            messages.info(request, f"Textos do {f} salvos: {', '.join(mexeu)}.")


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
    change_form_template = "nucleo/revista_change_form.html"
    change_list_template = "nucleo/change_list_lotes.html"
    list_display = ("projeto", "componente", "arquivada_em")
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
    actions = ["baixar_zip"]  # só leitura: o mixin proíbe actions de escrita

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
            kwargs["form"] = type("RevistaForm", (self.form,), {**campos_de_texto(blocos), "blocos": blocos})
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
        if form.cleaned_data.get("arquivo_svg"):
            arquivos.receber_svg(obj, form.cleaned_data["arquivo_svg"])
            ids = ids_do_f2(obj)
            if ids and ids[1]:
                messages.warning(request, aviso_ids(obj, ids[1], ids[0]))
        if form.cleaned_data.get("arquivo_capa"):
            arquivos.receber_capa(obj, form.cleaned_data["arquivo_capa"])

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)  # inline antes: troca de template
        for f in (f for fs in formsets for f in fs.forms if getattr(f, "descartar", 0)):
            n = f.descartar
            messages.warning(
                request, f"Template do {f.instance.fasciculo} trocado: {n} cópia{'s' if n > 1 else ''} de seção descartada{'s' if n > 1 else ''}."
            )
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
            revista = resolver.carregar(obj.pk)
            resolvido = resolver.resolver(revista)
            atual = resolver.hash_validado(revista, resolvido)
            extra_context = {
                **(extra_context or {}),
                "validacao": {
                    "hash": atual,
                    "validada": validacao.validada(revista, atual),
                    "pendencias": resolver.pendencias(revista, resolvido),
                    # D-087: só avisa.
                    "desatualizadas": [
                        f"{c.revista_fasciculo.fasciculo} {c.secao}" for c in resolver.secoes_desatualizadas(revista)
                    ],
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
