"""Anos (tela B, S3 e S4 de D-190).

`/ui/anos/`: lista e "Abrir ano", mesma regra do admin (`AnoAdmin.abrir_view`). Ver exige `view_ano`;
abrir exige `abrir_ano` (403 no POST, formulário escondido no GET).
`/ui/anos/<ano>/`: etapas e componentes do ano, mesmas regras de `EtapaAdmin`/`ComponenteAdmin`
(código só leitura na edição; escala só leitura com corte ou matriz), e a paleta (S5), com a
confirmação de impacto de `CorPadraoAdmin` (`nucleo/paleta.py`). Sem excluir e sem bloqueio,
como no admin.
"""

import re

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_http_methods, require_POST

from nucleo.models import Ano, Componente, CorPadrao, Corte, Etapa, MatrizEtapaCC, Revista
from nucleo.models.cadastro import COR_HEX
from nucleo.paleta import PadraoImpactoForm, revistas_afetadas_padrao
from nucleo.servicos.abrir_ano import AnoRecusado, abrir_ano
from nucleo.servicos.impacto import avisar_perdidos
from nucleo.ui_autosave import form_de_um_campo, proxima_ordem, responder_campo


class AbrirAnoForm(forms.Form):  # cópia do form do admin: importá-lo daria import circular (admin → urls)
    ano = forms.IntegerField(label="Ano novo")


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@permission_required("nucleo.view_ano", raise_exception=True)
def anos(request):
    if request.method == "POST" and not request.user.has_perm("nucleo.abrir_ano"):
        raise PermissionDenied
    anos = list(Ano.objects.order_by("-ano"))
    form = AbrirAnoForm(request.POST or None)  # sem valor inicial: não há desfazer, o usuário digita
    if request.method == "POST" and form.is_valid():
        try:
            novo, origem = abrir_ano(form.cleaned_data["ano"], request.user)
        except AnoRecusado as e:
            form.add_error("ano", str(e))
        else:
            messages.success(request, f"Ano {novo} aberto a partir de {origem}.")
            return redirect("ui_anos")
    contexto = {
        "anos": anos, "ano": anos[0] if anos else None, "proximo": anos[0].ano + 1 if anos else None,
        "form": form, "secao": "anos",
    }  # fmt: skip
    return TemplateResponse(request, "ui/anos/anos.html", contexto)


class _DoAno(forms.ModelForm):
    """Linha da tabela do ano. Cópia das regras do admin (importá-lo daria import circular).
    O `ano` fica fora do form, então o Django pula o UNIQUE (ano, código): `clean_codigo` o faz."""

    def __init__(self, *args, ano, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.ano = ano
        if self.instance.pk:
            self.fields["codigo"].disabled = True
            self.fields["codigo"].widget.attrs["title"] = "O código não muda depois de criado."
        for nome, campo in self.fields.items():
            onde = self.instance.codigo if self.instance.pk else "linha nova"
            campo.widget.attrs.update({"class": "input", "aria-label": f"{campo.label} ({onde})"})

    codigo = forms.CharField(label="Código", max_length=20)  # TextField no modelo; o limite vem do CHECK

    def clean_codigo(self):
        if self.instance.pk:
            return self.instance.codigo  # só leitura: nem consulta o banco
        codigo = self.cleaned_data["codigo"].strip()
        modelo = type(self.instance)
        if modelo.objects.filter(ano=self.instance.ano, codigo=codigo).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(f"Já existe {self.artigo} {codigo} em {self.instance.ano.ano}.")
        return codigo


class EtapaForm(_DoAno):
    artigo = "a etapa"

    class Meta:
        model = Etapa
        fields = ["codigo", "escala_max"]  # U4: a ordem vem do código (ordem_escolar), não se digita
        labels = {"escala_max": "Escala máxima"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Escala com corte ou matriz gravados: mudar a escala invalidaria esses dados (EtapaAdmin).
        if getattr(self.instance, "travada", False):
            self.fields["escala_max"].disabled = True
            self.fields["escala_max"].widget.attrs["title"] = "Travada: a etapa já tem corte ou matriz."

    def save(self, commit=True):
        if not self.instance.pk:  # provisória: `renumerar_etapas` acerta a ordem do ano inteiro
            self.instance.ordem = proxima_ordem(Etapa.objects.filter(ano=self.instance.ano))
        return super().save(commit)


ETAPA = re.compile(r"^\s*(\d+)\s*(EF|EM)\s*$", re.IGNORECASE)


def ordem_escolar(codigo):
    """Lógica escolar (pedido do usuário, 03/11): todo o fundamental (EF) antes do médio (EM) e, no
    mesmo ensino, pela série (2EF, 5EF, 9EF, 1EM, 3EM). Código fora do padrão vai para o fim."""
    m = ETAPA.match(codigo)
    return (("EF", "EM").index(m[2].upper()), int(m[1]), "") if m else (2, 0, codigo)


def renumerar_etapas(ano):
    """Ordem 1…N das etapas do ano pela `ordem_escolar`. `save` (não `update`): o histórico registra."""
    for n, etapa in enumerate(sorted(Etapa.objects.filter(ano=ano), key=lambda e: ordem_escolar(e.codigo)), 1):
        if etapa.ordem != n:
            etapa.ordem = n
            etapa.save(update_fields=["ordem"])


class ComponenteForm(_DoAno):
    artigo = "o componente"
    nome = forms.CharField(label="Nome", max_length=200)

    class Meta:
        model = Componente
        fields = ["codigo", "nome"]


class _SemRepetir(forms.BaseModelFormSet):
    """Duas linhas novas com o mesmo código: `clean_codigo` não vê (nenhuma existe ainda)."""

    def clean(self):
        super().clean()
        vistos = set()
        for f in self.forms:
            codigo = getattr(f, "cleaned_data", {}).get("codigo")
            if codigo and codigo in vistos:
                f.add_error("codigo", "Código repetido nesta tabela.")
            vistos.add(codigo)


# U4: sem linha vazia no fim; o "+ Adicionar" põe a linha (molde do empty_form, componente linhaNova).
EtapaFormSet = forms.modelformset_factory(Etapa, form=EtapaForm, formset=_SemRepetir, extra=0)
ComponenteFormSet = forms.modelformset_factory(Componente, form=ComponenteForm, formset=_SemRepetir, extra=0)
SALVO = {"etapas": "Etapas de {} salvas.", "componentes": "Componentes de {} salvos."}


def _etapas(ano):
    """Etapas do ano com `travada` (tem corte ou matriz: a escala fica só leitura)."""
    travada = Exists(Corte.objects.filter(etapa=OuterRef("pk"))) | Exists(MatrizEtapaCC.objects.filter(etapa=OuterRef("pk")))
    return Etapa.objects.filter(ano=ano).annotate(travada=travada)


def _tabelas(ano, data=None, tabela=None):
    """Os dois formsets do ano; só `tabela` recebe o POST (a outra volta como estava)."""
    etapas = _etapas(ano).order_by("ordem", "codigo")
    componentes = Componente.objects.filter(ano=ano).order_by("codigo")
    return {
        "etapas": EtapaFormSet(data if tabela == "etapas" else None, queryset=etapas, prefix="etapas", form_kwargs={"ano": ano}),
        "componentes": ComponenteFormSet(
            data if tabela == "componentes" else None, queryset=componentes, prefix="componentes", form_kwargs={"ano": ano}
        ),
    }


COR = forms.TextInput(attrs={"type": "color", "class": "input-cor"})


class CorField(forms.CharField):
    """O <input type=color> sempre manda minúsculas; a carga gravou maiúsculas. Mesma cor em outra
    caixa não é mudança: senão pede confirmação à toa e o save troca a caixa (muda o hash)."""

    def has_changed(self, initial, data):
        return (initial or "").lower() != (data or "").lower()


class PadraoForm(PadraoImpactoForm):
    modal = True  # confirmação no modal de impacto (U2)
    cor = CorField(label="Cor", widget=COR, validators=COR_HEX)

    def clean_cor(self):
        cor = self.cleaned_data["cor"]
        return self.instance.cor if cor.lower() == (self.instance.cor or "").lower() else cor


def _form_padrao(cp, data=None):
    """Um form por padrão: a confirmação de impacto é de cada um. Só o enviado calcula o impacto
    (resolver por revista); no GET as 5 linhas sairiam caras e sem caixa de confirmação útil."""
    Form = forms.modelform_factory(CorPadrao, form=PadraoForm, fields=["nome", "cor"])
    if data is not None:  # classe nova por chamada: o atributo não vaza (como em CorPadraoAdmin.get_form)
        Form.impacto = staticmethod(lambda campos: revistas_afetadas_padrao(cp, campos))
    return Form(data, instance=cp, prefix=f"p{cp.padrao}")


class NovoPadraoForm(forms.ModelForm):
    """Padrão que falta no ano (admin deixa incluir). Sem impacto: o admin também não calcula."""

    class Meta:
        model = CorPadrao
        fields = ["padrao", "nome", "cor"]
        widgets = {"nome": forms.TextInput(attrs={"class": "input", "maxlength": 200}), "cor": COR}

    def __init__(self, *args, ano, livres, **kwargs):
        super().__init__(*args, prefix="novo", initial={"cor": "#808080"}, **kwargs)  # cinza, não preto: sinaliza "escolha a cor"
        self.instance.ano = ano
        self.fields["padrao"] = forms.TypedChoiceField(
            label="Padrão", choices=[(n, f"Padrão {n}") for n in livres], coerce=int, widget=forms.Select(attrs={"class": "select"})
        )


def _pode(user):
    return {
        "etapas": user.has_perms(["nucleo.add_etapa", "nucleo.change_etapa"]),
        "componentes": user.has_perms(["nucleo.add_componente", "nucleo.change_componente"]),
        "padroes": user.has_perm("nucleo.change_corpadrao"),
        "novo_padrao": user.has_perm("nucleo.add_corpadrao"),
    }


def _gravar_padrao(request, ano, cps, novo, enviado):
    """POST de um padrão (`padroes`) ou do padrão novo (`novo_padrao`). Devolve o redirect ou None."""
    if request.POST["tabela"] == "novo_padrao":
        if novo.is_valid():
            try:
                with transaction.atomic():
                    novo.save()
            except IntegrityError:  # outra pessoa criou o mesmo padrão entre o GET e o POST
                messages.error(request, "Nada foi salvo: esse padrão acabou de ser criado por outra pessoa.")
                return redirect("ui_ano", ano.ano)
            messages.success(request, f"Padrão {novo.instance.padrao} de {ano.ano} criado.")
            return redirect("ui_ano", ano.ano)
        return None
    cp = next(c for c in cps if c.pk == enviado)
    form = cps[cp]
    if not form.is_valid() or form.pedir_confirmacao(form.resultado[1]):
        return None  # erro ou modal de impacto: a página volta com os valores enviados
    form.save()
    if form.perdem:  # mesmo aviso de CorPadraoAdmin.save_model
        avisar_perdidos(request, form.perdem, ano.ano)
    else:
        messages.success(request, f"Padrão {cp.padrao} de {ano.ano} salvo.")
    return redirect("ui_ano", ano.ano)


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@permission_required("nucleo.view_etapa", raise_exception=True)
def ano(request, ano):
    ano = get_object_or_404(Ano, ano=ano)
    pode = _pode(request.user)
    tabela = request.POST.get("tabela") if request.method == "POST" else None
    if request.method == "POST" and not pode.get(tabela):
        raise PermissionDenied
    enviado = None
    if tabela == "padroes":
        pk = request.POST.get("padrao", "")
        if not (pk.isascii() and pk.isdigit()):
            raise Http404
        enviado = get_object_or_404(CorPadrao, pk=int(pk), ano=ano).pk
    cps = {cp: _form_padrao(cp, request.POST if cp.pk == enviado else None) for cp in CorPadrao.objects.filter(ano=ano).order_by("padrao")}
    livres = sorted({1, 2, 3, 4, 5} - {cp.padrao for cp in cps})
    novo = NovoPadraoForm(request.POST if tabela == "novo_padrao" else None, ano=ano, livres=livres) if livres else None
    if tabela in ("padroes", "novo_padrao"):
        if tabela == "novo_padrao" and novo is None:
            raise PermissionDenied  # já há os 5
        if resposta := _gravar_padrao(request, ano, cps, novo, enviado):
            return resposta
    tabelas = _tabelas(ano, request.POST, tabela)
    if tabela in ("etapas", "componentes") and tabelas[tabela].is_valid():
        try:
            with transaction.atomic():  # tudo ou nada
                tabelas[tabela].save()
                if tabela == "etapas":
                    renumerar_etapas(ano)
        except IntegrityError:  # outra pessoa gravou o mesmo código entre a checagem e o save
            messages.error(request, "Nada foi salvo: um dos códigos acabou de ser criado por outra pessoa. Confira e salve de novo.")
        else:
            messages.success(request, SALVO[tabela].format(ano.ano))
            return redirect("ui_ano", ano.ano)
    contexto = {**tabelas, "padroes": list(cps.values()), "novo": novo, "ano": ano, "pode": pode, "secao": "anos"}
    return TemplateResponse(request, "ui/anos/ano.html", contexto)


@require_POST
@login_required(login_url="admin:login")
@permission_required("nucleo.view_etapa", raise_exception=True)
def campo(request, ano, tabela, pk):
    """Autosave (U3) de um campo de etapa (escala máxima sem corte nem matriz) ou de componente
    (nome) já gravados. A linha nova grava pelo botão "Incluir" da linha (U4)."""
    if tabela not in SALVO:
        raise Http404
    if not _pode(request.user)[tabela]:
        raise PermissionDenied
    ano = get_object_or_404(Ano, ano=ano)
    Form, qs = (EtapaForm, _etapas(ano)) if tabela == "etapas" else (ComponenteForm, Componente.objects.filter(ano=ano))
    obj = get_object_or_404(qs, pk=pk)
    nome = request.POST.get("campo", "")
    form = form_de_um_campo(Form, nome, request.POST.get("valor", ""), instance=obj, ano=ano)

    def gravar(dados):
        atual = type(obj).objects.get(pk=obj.pk)
        setattr(atual, nome, dados[nome])
        atual.save(update_fields=[nome])

    revistas = lambda: Revista.objects.filter(projeto__ano=ano, arquivada_em__isnull=True)  # noqa: E731
    titulo = f"Salvar “{form.fields[nome].label}” de {obj.codigo}" if form else "Salvar"
    return responder_campo(request, form=form, gravar=gravar, revistas=revistas, titulo=titulo)


urlpatterns = [
    path("", anos, name="ui_anos"),
    path("<int:ano>/", ano, name="ui_ano"),
    path("<int:ano>/<str:tabela>/<int:pk>/campo/", campo, name="ui_ano_campo"),
]
