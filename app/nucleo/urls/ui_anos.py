"""Anos (tela B, S3 e S4 de D-190).

`/ui/anos/`: lista e "Abrir ano", mesma regra do admin (`AnoAdmin.abrir_view`). Ver exige `view_ano`;
abrir exige `abrir_ano` (403 no POST, formulário escondido no GET).
`/ui/anos/<ano>/`: etapas e componentes do ano, mesmas regras de `EtapaAdmin`/`ComponenteAdmin`
(código só leitura na edição; escala só leitura com corte ou matriz). Sem excluir e sem bloqueio,
como no admin.
"""

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_http_methods

from nucleo.models import Ano, Componente, Corte, Etapa, MatrizEtapaCC
from nucleo.servicos.abrir_ano import AnoRecusado, abrir_ano


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
        fields = ["codigo", "escala_max", "ordem"]
        labels = {"escala_max": "Escala máxima", "ordem": "Ordem"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Escala com corte ou matriz gravados: mudar a escala invalidaria esses dados (EtapaAdmin).
        if getattr(self.instance, "travada", False):
            self.fields["escala_max"].disabled = True


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


EtapaFormSet = forms.modelformset_factory(Etapa, form=EtapaForm, formset=_SemRepetir, extra=1)
ComponenteFormSet = forms.modelformset_factory(Componente, form=ComponenteForm, formset=_SemRepetir, extra=1)
SALVO = {"etapas": "Etapas de {} salvas.", "componentes": "Componentes de {} salvos."}


def _tabelas(ano, data=None, tabela=None):
    """Os dois formsets do ano; só `tabela` recebe o POST (a outra volta como estava)."""
    travada = Exists(Corte.objects.filter(etapa=OuterRef("pk"))) | Exists(MatrizEtapaCC.objects.filter(etapa=OuterRef("pk")))
    etapas = Etapa.objects.filter(ano=ano).annotate(travada=travada).order_by("ordem", "codigo")
    componentes = Componente.objects.filter(ano=ano).order_by("codigo")
    return {
        "etapas": EtapaFormSet(data if tabela == "etapas" else None, queryset=etapas, prefix="etapas", form_kwargs={"ano": ano}),
        "componentes": ComponenteFormSet(
            data if tabela == "componentes" else None, queryset=componentes, prefix="componentes", form_kwargs={"ano": ano}
        ),
    }


def _pode(user):
    return {
        "etapas": user.has_perms(["nucleo.add_etapa", "nucleo.change_etapa"]),
        "componentes": user.has_perms(["nucleo.add_componente", "nucleo.change_componente"]),
    }


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@permission_required("nucleo.view_etapa", raise_exception=True)
def ano(request, ano):
    ano = get_object_or_404(Ano, ano=ano)
    pode = _pode(request.user)
    tabela = request.POST.get("tabela") if request.method == "POST" else None
    if request.method == "POST" and not pode.get(tabela):
        raise PermissionDenied
    tabelas = _tabelas(ano, request.POST, tabela)
    if tabela and tabelas[tabela].is_valid():
        try:
            with transaction.atomic():  # tudo ou nada
                tabelas[tabela].save()
        except IntegrityError:  # outra pessoa gravou o mesmo código entre a checagem e o save
            messages.error(request, "Nada foi salvo: um dos códigos acabou de ser criado por outra pessoa. Confira e salve de novo.")
        else:
            messages.success(request, SALVO[tabela].format(ano.ano))
            return redirect("ui_ano", ano.ano)
    contexto = {**tabelas, "ano": ano, "pode": pode, "secao": "anos"}
    return TemplateResponse(request, "ui/anos/ano.html", contexto)


urlpatterns = [path("", anos, name="ui_anos"), path("<int:ano>/", ano, name="ui_ano")]
