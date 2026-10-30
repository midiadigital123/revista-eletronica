"""Regra comum da matriz às duas telas: o admin (`admin/matriz.py`) e a página própria
(`urls/ui_matriz.py`, opção B). Reimportar (D-071, D-141, D-146) e arquivo do item (D-180).
Formulários e o que antes era corpo de view do admin; o admin importa daqui.
"""

import tempfile
from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError

from nucleo.models import Ano, Descritor, Matriz, MatrizEtapaCC, Tarefa
from nucleo.servicos.arquivos import ITEM_MAX, receber_item, remover_item
from nucleo.servicos.importar_matriz import (
    MANTER,
    ImportacaoRecusada,
    gravar_matriz,
    ler,
)
from nucleo.servicos.matriz import revistas_afetadas


def ler_upload(arquivo):
    """O leitor de PDF chama `pdftotext` num caminho: grava o upload num arquivo temporário."""
    with tempfile.NamedTemporaryFile(suffix=Path(arquivo.name).suffix.lower()) as tmp:
        for parte in arquivo.chunks():
            tmp.write(parte)
        tmp.flush()
        try:
            return ler(tmp.name)
        except ImportacaoRecusada as e:  # mensagem com o nome que o usuário enviou
            raise ImportacaoRecusada(str(e).replace(Path(tmp.name).name, arquivo.name)) from e


def reimportar(matriz, form):
    """Grava o arquivo de um `ReimportarForm` válido. Devolve a mensagem de sucesso ou None
    (com o erro já posto no form: arquivo ilegível, confirmação que não confere, recusa)."""
    arquivo, d = form.cleaned_data["arquivo"], form.cleaned_data
    try:
        dados = ler_upload(arquivo)
    except ValueError as e:  # inclui ImportacaoRecusada
        form.add_error("arquivo", str(e))
        return None
    mecs = list(MatrizEtapaCC.objects.filter(matriz=matriz).select_related("etapa", "componente"))
    existentes = sorted({(m.componente.codigo, m.etapa.codigo) for m in mecs} & set(dados))
    if existentes and d["confirmacao"] != matriz.nome:
        lista = ", ".join(" ".join(k) for k in existentes)
        n = revistas_afetadas(*[m for m in mecs if (m.componente.codigo, m.etapa.codigo) in set(existentes)])
        form.add_error(
            "confirmacao",
            f"Vai substituir descritores e tarefas de {lista} (afeta {n} revista(s) ativa(s)). "
            f"Digite {matriz.nome} para confirmar (e escolha o arquivo de novo).",
        )
        return None
    passo = MANTER if d["passo"] is None else d["passo"]
    try:
        resumo = gravar_matriz(matriz, dados, bool(existentes), passo, origem=arquivo.name)
    except ImportacaoRecusada as e:
        form.add_error(None, str(e))
        return None
    partes = ", ".join(f"{cc} {e}: {n} descritores" for (cc, e), n in sorted(resumo.items()))
    return f"Importado em {matriz}: {partes}."


def gravar_item(tarefa, form, remover):
    """Arquivo do item de um `ItemForm` (envia, troca, remove ou só o texto alternativo).
    Devolve (sucesso, None) ou (None, motivo da recusa com a correção)."""
    if not form.is_valid():
        return None, " ".join(e for erros in form.errors.values() for e in erros)
    arquivo, alt = form.cleaned_data["arquivo"], form.cleaned_data["texto_alternativo"]
    try:
        if remover:
            remover_item(tarefa)
            return f"Arquivo do item removido da tarefa {tarefa.codigo}.", None
        if arquivo:
            receber_item(tarefa, arquivo, alt)
            return f"Arquivo do item enviado para a tarefa {tarefa.codigo}.", None
        if tarefa.arquivo:
            tarefa.save(update_fields=["texto_alternativo"])
            return f"Texto alternativo da tarefa {tarefa.codigo} salvo.", None
        return None, "nenhum arquivo escolhido. Escolha um PDF, PNG ou JPG e envie de novo."
    except ValidationError as e:
        return None, " ".join(e.messages) + " Escolha outro arquivo e envie de novo."


# --- Formulários (antes em admin/matriz.py) ----------------------------------------------


class DuplicarForm(forms.Form):
    ano = forms.ModelChoiceField(Ano.objects.order_by("-ano"), label="Ano da cópia", empty_label=None)
    nome = forms.CharField(max_length=200)


LIMITE_UPLOAD = 20 * 2**20  # os PDFs do SAEGO têm 10–12 MB


class ReimportarForm(forms.Form):
    arquivo = forms.FileField(help_text="PDF do SAEGO ou planilha .xlsx.")
    passo = forms.IntegerField(
        label="Intervalo mínimo", required=False, min_value=1,
        help_text="Vazio: mantém o das etapa × CC que já existem (as novas ficam sem linhas vazias).",
    )  # fmt: skip
    confirmacao = forms.CharField(
        label="Confirmação", required=False,
        help_text="Para substituir etapa × CC que já existem, digite o nome da matriz.",
    )  # fmt: skip

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if arquivo.size > LIMITE_UPLOAD:
            raise ValidationError(f"Arquivo maior que {LIMITE_UPLOAD // 2**20} MB.")
        inicio = arquivo.read(5)
        arquivo.seek(0)
        if not inicio.startswith((b"%PDF-", b"PK\x03\x04")):
            raise ValidationError("O arquivo não é um PDF nem uma planilha .xlsx.")
        return arquivo


class MatrizForm(forms.ModelForm):
    def clean(self):
        dados = super().clean()
        # Na edição o ano é readonly e o Django pula o UNIQUE (ano, nome): confere aqui.
        ano_id = self.instance.ano_id if self.instance.pk else getattr(dados.get("ano"), "pk", None)
        nome = dados.get("nome")
        if ano_id and nome and Matriz.objects.filter(ano_id=ano_id, nome=nome).exclude(pk=self.instance.pk).exists():
            self.add_error("nome", "Já existe uma matriz com este nome neste ano.")
        return dados


class ImpactoForm(forms.ModelForm):
    """Pede confirmação quando a edição afeta revistas ativas. `afetadas` vem do admin."""

    confirmar_impacto = forms.BooleanField(required=False)
    afetadas = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        campo = self.fields["confirmar_impacto"]
        if self.afetadas:
            campo.label = f"Confirmo: afeta {self.afetadas} revista(s) ativa(s)"
        else:
            campo.widget = forms.HiddenInput()

    def clean(self):
        dados = super().clean()
        if self.afetadas and not dados.get("confirmar_impacto"):
            raise ValidationError(
                f"Esta edição afeta {self.afetadas} revista(s) ativa(s) (parceiros com corte nesta "
                "etapa × CC que usam esta matriz). Marque a confirmação e salve de novo."
            )
        return dados


class LinhasField(forms.CharField):
    """Lista de textos, um por linha (vírgula pode aparecer dentro do pré-requisito)."""

    widget = forms.Textarea(attrs={"rows": 3})

    def prepare_value(self, value):
        return "\n".join(value) if isinstance(value, list) else value

    def to_python(self, value):
        return [linha.strip() for linha in (value or "").splitlines() if linha.strip()]


class DescritorForm(ImpactoForm):
    def clean_codigo(self):
        codigo = self.cleaned_data["codigo"]
        # A MEC é readonly aqui: o Django pula o UNIQUE (mec, código).
        if Descritor.objects.filter(matriz_etapa_cc_id=self.instance.matriz_etapa_cc_id, codigo=codigo).exclude(
            pk=self.instance.pk
        ).exists():
            raise ValidationError("Já existe um descritor com este código nesta etapa × CC.")
        return codigo


class ItemForm(ImpactoForm):
    arquivo = forms.FileField(
        label="Arquivo", required=False, help_text="PDF, PNG ou JPG, até 5 MB.",
        widget=forms.FileInput(attrs={"accept": "application/pdf,image/png,image/jpeg,.pdf,.png,.jpg,.jpeg"}),
    )  # fmt: skip
    field_order = ("arquivo", "texto_alternativo", "confirmar_impacto")

    def clean_arquivo(self):
        arquivo = self.cleaned_data["arquivo"]
        if arquivo and arquivo.size > ITEM_MAX:
            raise ValidationError(f"Arquivo do item acima de {ITEM_MAX // 2**20} MB. Reduza o arquivo e envie de novo.")
        return arquivo

    class Meta:
        model = Tarefa
        fields = ("texto_alternativo",)
        labels = {"texto_alternativo": "Texto alternativo (opcional)"}
        help_texts = {"texto_alternativo": "O que o item mostra, para quem usa leitor de tela. Até 1000 caracteres."}
        widgets = {"texto_alternativo": forms.Textarea(attrs={"rows": 3, "cols": 50, "maxlength": 1000})}


class ExcluirForm(forms.Form):
    confirmacao = forms.CharField(label="Confirmação")

    def __init__(self, *args, codigo, **kwargs):
        super().__init__(*args, **kwargs)
        self.codigo = codigo
        self.fields["confirmacao"].help_text = f"Digite {codigo} para confirmar."

    def clean_confirmacao(self):
        if self.cleaned_data["confirmacao"].strip() != self.codigo:
            raise ValidationError(f"Nada foi excluído: o código não confere. Digite {self.codigo} exatamente.")
        return self.cleaned_data["confirmacao"]


def com_afetadas(classe, n):
    """Form de impacto (`ImpactoForm`) com a contagem de revistas afetadas desta MEC."""
    return type(classe.__name__, (classe,), {"afetadas": n})


def excluir(obj, rotulo):
    """Exclui o descritor ou a tarefa (D-181) e devolve a mensagem de sucesso. Quem chama já
    validou o `ExcluirForm` e cuida do bloqueio da MEC."""
    codigo = obj.codigo
    obj.delete()
    return f"{rotulo.capitalize()} {codigo} {'excluída' if rotulo == 'tarefa' else 'excluído'}."
