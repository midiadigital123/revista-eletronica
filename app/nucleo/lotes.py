"""Lotes (D-102, D-121): "Escolher matriz" (ParceiroAno) e "Escolher template F1/F2" (Revista).

Regra comum às duas telas de cada lote: a do admin (`admin/lote.py`) e a página própria
(`urls/ui_lotes.py`, opção B). Cada alvo é gravado com o bloqueio do projeto
(`escrever_travado`); alvo travado ou arquivado é pulado e listado na mensagem.
"""

import logging

from django import forms
from django.contrib import messages
from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch
from django.db.models.functions import Now

from nucleo.models import (
    Bloqueio,
    Fasciculo,
    Matriz,
    ParceiroAno,
    Projeto,
    Revista,
    RevistaFasciculo,
    RevistaSecao,
    Template,
)
from nucleo.servicos import bloqueio
from nucleo.servicos.impacto import perdem_validado

log = logging.getLogger(__name__)
FORA_DA_LISTA = "Escolha uma opção da lista; a lista mudou desde que a página abriu."


def erros(obrigatorio):
    return {"required": obrigatorio, "invalid_choice": FORA_DA_LISTA, "invalid_pk_value": FORA_DA_LISTA}


def escrever_travado(projeto, usuario, escrever):
    """Roda `escrever()` numa transação, segurando o bloqueio do projeto.

    Devolve None se gravou, ou o motivo do pulo: outro usuário
    edita o projeto, ou ele foi arquivado. `escrever()` também pode devolver um motivo.
    Adquirir (em vez de só olhar `quem_bloqueia`) fecha a corrida: quem abrir o projeto
    enquanto a escrita roda espera o commit e já carrega o valor novo. Exceção: o rollback
    desfaz também o bloqueio adquirido aqui.
    """
    sessao = bloqueio.nova_sessao()
    with transaction.atomic():
        if not bloqueio.adquirir(projeto, usuario, sessao):
            return f"projeto em edição por {quem_edita(projeto)}"
        # A cascata arquiva sem o bloqueio: o FOR UPDATE espera por ela e relê arquivado_em.
        ativo = Projeto.objects.select_for_update().filter(pk=projeto.pk, arquivado_em__isnull=True)
        motivo = escrever() if list(ativo.values_list("pk", flat=True)) else "projeto arquivado"
        bloqueio.liberar(projeto, usuario, sessao)
    return motivo


def aplicar(request, itens):
    """itens: [(rótulo, projeto ou None, escrever)]. Grava um a um; avisa os pulados e devolve
    quantos foram feitos. Erro num alvo não derruba os outros."""
    feitos, pulados = 0, []
    for rotulo, projeto, escrever in itens:
        try:
            if projeto is None:  # sem projeto ativo, ninguém edita nada dele
                with transaction.atomic():
                    motivo = escrever()
            else:
                motivo = escrever_travado(projeto, request.user, escrever)
        except Exception as e:
            log.exception("Falha no lote: %s", rotulo)
            motivo = f"erro ao gravar: {type(e).__name__}"
        if motivo:
            pulados.append(f"{rotulo} ({motivo})")
        else:
            feitos += 1
    avisar_pulados(request, pulados)
    return feitos


def quem_edita(projeto):
    atual = bloqueio.quem_bloqueia(projeto)
    if atual is None:
        return "outra sessão"
    return atual.usuario.get_full_name() or atual.usuario.get_username()


def avisar_pulados(request, pulados):
    if pulados:
        messages.warning(request, "Pulados: " + "; ".join(pulados) + ".")


def em_edicao(projetos):
    """{pk do projeto: quem edita} dos projetos com bloqueio válido: o lote vai pulá-los.
    Uma consulta para a lista toda (`quem_bloqueia` faz uma por projeto)."""
    travas = Bloqueio.objects.filter(projeto__in=projetos, expira_em__gte=Now()).select_related("usuario")
    return {b.projeto_id: b.usuario.get_full_name() or b.usuario.get_username() for b in travas}


# --- Escolher matriz ------------------------------------------------------------


class MatrizLoteForm(forms.Form):
    alvos = forms.ModelMultipleChoiceField(
        None, label="Parceiros", widget=forms.CheckboxSelectMultiple, error_messages=erros("Marque ao menos um parceiro.")
    )
    matriz = forms.ModelChoiceField(queryset=None, error_messages=erros("Escolha a matriz."))

    def __init__(self, *args, ano, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["alvos"].queryset = (
            ParceiroAno.objects.filter(ano=ano)
            .select_related("parceiro", "matriz")
            .prefetch_related(Prefetch("projeto_set", Projeto.objects.filter(arquivado_em__isnull=True), to_attr="ativos"))
            .order_by("parceiro__nome")
        )
        self.fields["alvos"].label_from_instance = lambda pa: f"{pa.parceiro} (atual: {pa.matriz.nome if pa.matriz else '—'})"
        self.fields["matriz"].queryset = Matriz.objects.filter(ano=ano).order_by("nome")


def _escrever_matriz(pa, matriz):
    pa.matriz = matriz
    pa.save(update_fields=["matriz"])


def perdem_matriz(form):
    """Revistas validadas que o lote de matriz do form válido tira do "Validado" (simulado, U2).
    Ponytail: conta também as de projeto em edição, que o lote vai pular."""
    alvos, matriz = form.cleaned_data["alvos"], form.cleaned_data["matriz"]
    revistas = Revista.objects.filter(projeto__parceiro_ano__in=alvos, arquivada_em__isnull=True).select_related(
        "projeto__parceiro_ano__parceiro", "projeto__ano", "componente"
    )
    return perdem_validado(lambda: [_escrever_matriz(pa, matriz) for pa in alvos], revistas)


def gravar_matriz(request, form):
    """Grava a matriz escolhida nos parceiros do form válido; avisa feitos e pulados."""
    matriz = form.cleaned_data["matriz"]
    itens = [
        (str(pa.parceiro), pa.ativos[0] if pa.ativos else None, lambda pa=pa: _escrever_matriz(pa, matriz))
        for pa in form.cleaned_data["alvos"]
    ]
    feitos = aplicar(request, itens)
    messages.success(request, f"Matriz {matriz.nome} escolhida para {feitos} parceiro(s).")
    return feitos


# --- Escolher template F1/F2 ------------------------------------------------------


class TemplateLoteForm(forms.Form):
    alvos = forms.ModelMultipleChoiceField(
        None, label="Revistas", widget=forms.CheckboxSelectMultiple, error_messages=erros("Marque ao menos uma revista.")
    )
    template_f1 = forms.ModelChoiceField(queryset=None, required=False, label="Template F1", error_messages=erros(""))
    template_f2 = forms.ModelChoiceField(queryset=None, required=False, label="Template F2", error_messages=erros(""))

    def __init__(self, *args, ano, componente, **kwargs):
        super().__init__(*args, **kwargs)
        # Só ativas: revista ou projeto arquivado é só leitura (D-093, D-117).
        self.fields["alvos"].queryset = (
            Revista.objects.filter(ano=ano, componente=componente, arquivada_em__isnull=True,
                                   projeto__arquivado_em__isnull=True)
            .select_related("projeto", "componente")
            .order_by("projeto__nome")
        )  # fmt: skip
        # Template de outro componente não é oferecido (e o banco recusa: FK composta, D-098).
        for fasc in Fasciculo.values:
            self.fields[f"template_{fasc.lower()}"].queryset = Template.objects.filter(
                ano=ano, componente=componente, fasciculo=fasc
            ).order_by("nome")

    def clean(self):
        dados = super().clean()
        if not (dados.get("template_f1") or dados.get("template_f2")):
            raise forms.ValidationError("Escolha o template do F1, do F2 ou dos dois.")
        return dados


def _templates(form):
    novos = {f: form.cleaned_data[f"template_{f.lower()}"] for f in Fasciculo.values}
    return {f: t for f, t in novos.items() if t is not None}


def perdem_template(form):
    """Revistas validadas que o lote de template do form válido tira do "Validado" (simulado, U2)."""
    novos, alvos = _templates(form), form.cleaned_data["alvos"]
    return perdem_validado(lambda: [_escrever_template(r, novos) for r in alvos], alvos)


def _escrever_template(revista, novos):
    """Troca os templates da revista; devolve o motivo do pulo ou None."""
    # Dentro do bloqueio: ninguém cria cópia de seção enquanto conferimos.
    if not list(Revista.objects.select_for_update().filter(pk=revista.pk, arquivada_em__isnull=True).values_list("pk")):
        return "revista arquivada"
    copias = RevistaSecao.objects.filter(revista_fasciculo=OuterRef("pk"))
    com_copias = []
    for rf in RevistaFasciculo.objects.filter(revista=revista, fasciculo__in=novos).annotate(tem_copias=Exists(copias)):
        novo = novos[rf.fasciculo]
        if rf.template_id == novo.pk:
            continue
        if rf.tem_copias:  # a FK composta recusaria (D-104)
            com_copias.append(rf.fasciculo)
            continue
        rf.template = novo
        rf.save(update_fields=["template"])
    if com_copias:
        return f"{'/'.join(com_copias)} tem cópias de seção; troque o template pela revista"
    return None


def gravar_template(request, form):
    """Grava os templates escolhidos nas revistas do form válido; avisa feitos e pulados."""
    novos = _templates(form)
    itens = [(str(r), r.projeto, lambda r=r: _escrever_template(r, novos)) for r in form.cleaned_data["alvos"]]
    feitos = aplicar(request, itens)
    messages.success(request, f"Template escolhido em {feitos} revista(s).")
    return feitos
