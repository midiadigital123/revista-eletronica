"""Regra da revista (SVG, capa, template por fascículo, textos por seção, "Validado").

Extraída de `admin/revista.py` para o admin e a página própria (`urls/ui_revista.py`) usarem a
mesma regra (D-183). Detalhes das regras na docstring do admin: D-104, D-108, D-115, D-170, D-171.
Tudo que grava roda dentro da transação de quem chama (bloqueio do projeto, D-140).
"""

import difflib
from typing import NamedTuple

from django import forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from nucleo import texto
from nucleo.models import Revista, RevistaFasciculo, RevistaSecao, Template
from nucleo.servicos import arquivos, resolver, validacao


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


class CorpoField(forms.CharField):
    """Corpo da seção como `texto.secoes` o devolve: `\n` e sem espaço nas pontas.
    Assim o has_changed (contra o hidden do valor inicial) não vê `\r\n` do navegador como edição."""

    def to_python(self, value):
        return super().to_python(value).replace("\r\n", "\n").replace("\r", "\n")


def diff(seu, novo):
    """Tabela lado a lado do difflib (escapa &, < e >)."""
    tabela = difflib.HtmlDiff(wrapcolumn=70).make_table(seu.splitlines(), (novo or "").splitlines(), "Seu texto", "Template novo")
    return mark_safe(tabela)


def campos_de_texto(blocos, editor=None):
    """Campos declarados do form (o modelform_factory recusa campo que não seja declarado).
    `editor(secao)` devolve o widget do corpo (o admin usa o EditorSecao com preview)."""
    campos = {}
    for b in blocos:
        f = b.rf.fasciculo
        campos[nome("versao", f)] = forms.IntegerField(required=False, widget=forms.HiddenInput, initial=b.versao.pk)
        for s in b.secoes:
            widget = editor(s) if editor else forms.Textarea(attrs={"rows": 6, "spellcheck": "true"})
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


def form_de_textos(blocos, editor=None):
    """RevistaForm com um campo por seção dos `blocos` (o admin e a página própria usam)."""
    return type("RevistaForm", (RevistaForm,), {**campos_de_texto(blocos, editor), "blocos": blocos})


def gravar_arquivos(request, revista, dados):
    """Grava SVG e capa já validados pelo RevistaForm; ids faltando gravam e avisam (D-108)."""
    if dados.get("arquivo_svg"):
        arquivos.receber_svg(revista, dados["arquivo_svg"])
        ids = ids_do_f2(revista)
        if ids and ids[1]:
            messages.warning(request, aviso_ids(revista, ids[1], ids[0]))
    if dados.get("arquivo_capa"):
        arquivos.receber_capa(revista, dados["arquivo_capa"])


def avisar_descartes(request, forms_):
    """Aviso de cópias apagadas pela troca de template (FasciculoForm.descartar)."""
    for f in (f for f in forms_ if getattr(f, "descartar", 0)):
        n = f.descartar
        messages.warning(
            request, f"Template do {f.instance.fasciculo} trocado: {n} cópia{'s' if n > 1 else ''} de seção descartada{'s' if n > 1 else ''}."
        )


def estado_validacao(pk):
    """Hash exibido, se está validada, pendências e seções desatualizadas (só aviso, D-087)."""
    revista = resolver.carregar(pk)
    resolvido = resolver.resolver(revista)
    atual = resolver.hash_validado(revista, resolvido)
    return {
        "hash": atual,
        "validada": validacao.validada(revista, atual),
        "pendencias": resolver.pendencias(revista, resolvido),
        "desatualizadas": [f"{c.revista_fasciculo.fasciculo} {c.secao}" for c in resolver.secoes_desatualizadas(revista)],
    }
