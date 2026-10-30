"""Forms do projeto (T16; D-053, D-060, D-091, D-166, D-167, D-175): nome, variáveis, passo e cor.

Regra comum às duas telas do projeto: o change form do admin (`admin/projeto.py`) e a página
própria (`urls/ui_projeto.py`, opção B). Passo e cor são sobrescritas do projeto: a linha
existir = sobrescrevi; excluir a linha = voltar ao passo da matriz / à cor da paleta do ano.
"""

from django import forms
from django.forms import BaseInlineFormSet, inlineformset_factory

from nucleo.admin.variaveis import EDITAVEIS, limitar, mostrar_nome_do_ano
from nucleo.models import Componente, Etapa, Projeto, ProjetoCor, ProjetoPasso
from nucleo.variaveis import TAMANHO_MAX

MAX_CORES = 5  # um por padrão (1 a 5)


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
