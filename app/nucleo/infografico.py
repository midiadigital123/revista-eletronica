"""Regra de gravação do infográfico do F2 (D-230 a D-235): um campo por envio do autosave.

A view do passo "Infográficos" (`urls/ui_revista.py`) só traduz o POST e chama `form_do_campo`;
a validação e a gravação ficam aqui, como em `nucleo/revista.py`. `<pk>` é o do `RevistaInfografico`:

- `inf-<pk>-<habilidade|texto_descritor|texto_habilidades|texto_progressao>` → `RevistaInfografico`;
- `inf-<pk>-passo-<habilidades|progressao|tarefas>`, valor `on` (ligado) ou vazio → `passos_desligados`;
- `inf-<pk>-etapa-<1EF…3EM>-<marca|codigo|texto>` → `RevistaInfograficoEtapa`;
- `inf-<pk>-item-<1..4>-<etapa|descritor|texto_alternativo|analise>` → `RevistaInfograficoItem`;
- `inf-<pk>-item-<1..4>-imagem`, o arquivo em `arquivo` → `arquivos.receber_imagem_item`.

A linha de etapa ou item que falta é criada na 1ª gravação, com o `ano` do infográfico.
"""

import hashlib
import re

from django import forms
from django.core.exceptions import ValidationError

from nucleo.models import RevistaInfografico, RevistaInfograficoEtapa, RevistaInfograficoItem
from nucleo.models.revista import PASSOS_DESLIGAVEIS, EtapaReferencial
from nucleo.servicos import arquivos
from nucleo.ui_autosave import form_de_um_campo

# Os campos texto são TextField no modelo; o limite vem do CHECK (max_len) e aqui vira erro de form.


class InfograficoForm(forms.ModelForm):
    habilidade = forms.CharField(max_length=500, required=False)

    class Meta:
        model = RevistaInfografico
        fields = ["habilidade", "texto_descritor", "texto_habilidades", "texto_progressao"]


class EtapaForm(forms.ModelForm):
    codigo = forms.CharField(label="Código", max_length=50, required=False)

    class Meta:
        model = RevistaInfograficoEtapa
        fields = ["marca", "codigo", "texto"]


class ItemForm(forms.ModelForm):
    descritor = forms.CharField(max_length=20, required=False)
    texto_alternativo = forms.CharField(label="Texto alternativo", max_length=1000, required=False)

    class Meta:
        model = RevistaInfograficoItem
        fields = ["etapa", "descritor", "texto_alternativo", "analise"]


class PassoForm(forms.Form):
    ligado = forms.BooleanField(required=False)


class ImagemForm(forms.Form):
    arquivo = forms.FileField(label="")  # "Imagem maior que 5 MB: …" já diz qual

    def clean_arquivo(self):
        dados = arquivos._ler(self.cleaned_data["arquivo"], arquivos.ITEM_MAX, "Imagem")
        if arquivos.tipo_imagem(dados) is None:
            raise ValidationError("A imagem precisa ser PNG, JPG ou WebP.")
        return dados


CAMPO = re.compile(
    r"inf-(?P<pk>\d+)-(?:"
    r"(?P<inf>habilidade|texto_descritor|texto_habilidades|texto_progressao)"
    rf"|passo-(?P<passo>{'|'.join(PASSOS_DESLIGAVEIS)})"
    rf"|etapa-(?P<etapa>{'|'.join(EtapaReferencial.values)})-(?P<etapa_campo>marca|codigo|texto)"
    r"|item-(?P<posicao>[1-4])-(?P<item_campo>etapa|descritor|texto_alternativo|analise|imagem))"
)


def familia(campo):
    """`etapa`, `item` ou `infografico` (habilidade, textos, passo): de que modelo é a permissão. None: campo desconhecido."""
    m = CAMPO.fullmatch(campo)
    return m and ("etapa" if m["etapa"] else "item" if m["posicao"] else "infografico")


def form_do_campo(revista, campo, valor, arquivo=None):
    """`(form, gravar, simular)` do `campo` (nomes na docstring do módulo), ou None se o campo é
    desconhecido ou o infográfico não é da `revista` ou está arquivado (a view responde 422).

    Serve direto a `ui_autosave.responder_campo(request, form=form, gravar=gravar, simular=simular,
    revistas=lambda: [revista])`: `form` é um form de um campo só, ligado; `gravar(cleaned_data)` grava
    com `.save()` (o histórico registra), dentro da transação de quem chama. `simular` é None (a
    simulação roda o próprio `gravar`), menos na imagem: lá ela grava só `imagem` + `imagem_sha256`
    (juntos, por causa do CHECK), sem arquivo no storage."""
    m = CAMPO.fullmatch(campo)
    inf = m and RevistaInfografico.objects.filter(pk=m["pk"], revista=revista, arquivado_em__isnull=True).first()
    if not inf:
        return None
    linha = {"infografico": inf, "ano_id": inf.ano_id}  # etapa ou item: a linha nova sai com o ano do infográfico

    if m["passo"]:
        inf_pk = inf.pk

        def gravar(dados):
            inf = RevistaInfografico.objects.get(pk=inf_pk)  # relê: a simulação desfeita mexeu na instância
            fora = set(inf.passos_desligados) - {m["passo"]}
            if not dados["ligado"]:
                fora.add(m["passo"])
            inf.passos_desligados = [p for p in PASSOS_DESLIGAVEIS if p in fora]
            inf.save(update_fields=["passos_desligados"])

        return PassoForm({"ligado": valor}), gravar, None

    if m["item_campo"] == "imagem":
        chave = {**linha, "posicao": m["posicao"]}

        def gravar(dados):
            item = RevistaInfograficoItem.objects.filter(**chave).first() or RevistaInfograficoItem(**chave)
            arquivos.receber_imagem_item(item, dados["arquivo"])

        def simular(dados):
            sha = hashlib.sha256(dados["arquivo"]).hexdigest()
            RevistaInfograficoItem.objects.update_or_create(**chave, defaults={"imagem": "simulada", "imagem_sha256": sha})

        return ImagemForm({}, {"arquivo": arquivo}), gravar, simular

    if m["inf"]:
        Model, chave, nome, Form = RevistaInfografico, {"pk": inf.pk}, m["inf"], InfograficoForm
    elif m["etapa"]:
        Model, chave, nome, Form = RevistaInfograficoEtapa, {**linha, "etapa": m["etapa"]}, m["etapa_campo"], EtapaForm
    else:
        Model, chave, nome, Form = RevistaInfograficoItem, {**linha, "posicao": m["posicao"]}, m["item_campo"], ItemForm
    instancia = Model.objects.filter(**chave).first() or Model(**chave)

    def gravar(dados):
        # update_or_create, não a instância do form: a simulação (savepoint desfeito) não deixa pk velho nela.
        Model.objects.update_or_create(**chave, defaults={nome: dados[nome]})

    return form_de_um_campo(Form, nome, valor, instance=instancia), gravar, None
