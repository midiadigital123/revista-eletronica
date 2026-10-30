"""Forms do projeto (T16; D-053, D-060, D-091, D-166, D-167, D-175): nome, variáveis, passo e cor.

Regra comum às duas telas do projeto: o change form do admin (`admin/projeto.py`) e a página
própria (`urls/ui_projeto.py`, opção B). Passo e cor são sobrescritas do projeto: a linha
existir = sobrescrevi; excluir a linha = voltar ao passo da matriz / à cor da paleta do ano.
"""

from django import forms
from django.core.validators import MaxLengthValidator
from django.forms import BaseInlineFormSet, inlineformset_factory

from nucleo.models import Componente, CorPadrao, Etapa, Projeto, ProjetoCor, ProjetoPasso
from nucleo.variaveis import EDITAVEIS, TAMANHO_MAX

MAX_CORES = 5  # um por padrão (1 a 5)


def limitar(form, limites):
    """Tamanho máximo no form (validador + maxlength): sem isso o CHECK do banco vira 500."""
    for nome, limite in limites.items():
        campo = form.fields.get(nome)  # ausente quando só leitura
        if campo is not None:
            campo.validators.append(MaxLengthValidator(limite))
            campo.widget.attrs["maxlength"] = limite


def mostrar_nome_do_ano(form, ano_id):
    """Placeholder dos `pdNN`: o nome do padrão no ano, que vale quando o campo fica vazio (D-175)."""
    for k, nome in CorPadrao.objects.filter(ano_id=ano_id).exclude(nome="").values_list("padrao", "nome"):
        campo = form.fields.get(f"pd{k:02d}")  # ausente quando só leitura
        if campo is not None:
            campo.widget.attrs["placeholder"] = f"padrão do ano: {nome}"


class ProjetoForm(forms.ModelForm):
    class Meta:
        model = Projeto
        fields = ["nome", *EDITAVEIS]
        widgets = dict.fromkeys(fields, forms.TextInput(attrs={"size": 60}))  # TextField viraria textarea

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        limitar(self, {"nome": 200, **dict.fromkeys(EDITAVEIS, TAMANHO_MAX)})  # CHECKs do banco
        mostrar_nome_do_ano(self, self.instance.ano_id)


class PassoForm(forms.ModelForm):
    passo = forms.IntegerField(
        required=False, min_value=1, help_text="Vazio = sem linhas vazias, de propósito (D-091)."
    )

    class Meta:
        model = ProjetoPasso
        fields = ["etapa", "componente", "passo"]

    def __init__(self, *args, ano_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        # D-053: só etapa e componente do ano do projeto (a FK composta recusa os outros no banco).
        self.fields["etapa"].queryset = Etapa.objects.filter(ano_id=ano_id).order_by("ordem")
        self.fields["componente"].queryset = Componente.objects.filter(ano_id=ano_id).order_by("codigo")
        for nome in ("etapa", "componente"):  # o __str__ repete o ano, que aqui é sempre o do projeto
            self.fields[nome].label_from_instance = lambda o: o.codigo

    def clean(self):
        self.instance.ano_id = self.instance.projeto.ano_id  # o ano que a FK composta precisa
        return super().clean()


class PassoFormSet(BaseInlineFormSet):
    """Passa o ano do projeto a cada form (inclusive o `empty_form` da linha nova)."""

    def get_form_kwargs(self, index):
        return {**super().get_form_kwargs(index), "ano_id": self.instance.ano_id}


class CorForm(forms.ModelForm):
    class Meta:
        model = ProjetoCor
        fields = ["padrao", "cor"]
        widgets = {"cor": forms.TextInput(attrs={"type": "color"})}


def formsets(projeto, data=None):
    """Passos e cores do projeto como inline formsets (prefixos `passos` e `cores`)."""
    Passos = inlineformset_factory(Projeto, ProjetoPasso, form=PassoForm, formset=PassoFormSet, extra=0)
    Cores = inlineformset_factory(Projeto, ProjetoCor, form=CorForm, extra=0, max_num=MAX_CORES)
    return Passos(data, instance=projeto, prefix="passos"), Cores(data, instance=projeto, prefix="cores")
