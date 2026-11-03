"""Grade de cortes fora do admin (protótipo da opção B): mesma regra de `nucleo/cortes.py`.

Login (redireciona ao login do admin); ver exige `view_corte` ou `change_corte` (403);
gravar exige `add_corte` + `change_corte`, sem elas a grade é só leitura. Autosave por célula
(U3, `celula`): sem bloqueio, o conflito entre duas abas é otimista pelo `original` da célula.
"""

import re

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_GET, require_POST

from nucleo import cortes as regra
from nucleo.cortes import grade, pode_ver
from nucleo.models import Ano, Componente, Etapa, Parceiro, Revista
from nucleo.servicos import impacto
from nucleo.servicos.cascata import validar_linhas
from nucleo.ui_autosave import Conflito, conflito, erros, responder_campo


@require_GET
@login_required(login_url="admin:login")
def cortes(request, ano=None):
    """A grade (só GET): cada célula grava sozinha pela rota `cortes_celula` (U3)."""
    if not pode_ver(request.user):
        raise PermissionDenied
    anos = list(Ano.objects.order_by("-ano"))
    if ano is None:  # /cortes/ → ano mais recente
        return redirect("cortes", anos[0].ano) if anos else TemplateResponse(request, "ui/cortes.html", {"anos": anos})
    ano = get_object_or_404(Ano, ano=ano)
    contexto, _ = grade(request, ano, ler_post=False)
    return TemplateResponse(request, "ui/cortes.html", {**contexto, "ano": ano, "anos": anos, "secao": "cortes"})


@require_POST
@login_required(login_url="admin:login")
@permission_required("nucleo.add_parceiro", raise_exception=True)
def novo_parceiro(request, ano):
    """Nova linha da grade: o parceiro nasce sem cortes; o projeto nasce quando os cortes forem salvos."""
    form = modelform_factory(Parceiro, fields=["nome"])(request.POST)
    if form.is_valid():
        messages.success(request, f"Parceiro {form.save()} criado. Preencha os cortes da linha e salve.")
    else:
        messages.error(request, "Parceiro não criado: " + " ".join(m for erros in form.errors.values() for m in erros))
    return redirect("cortes", ano)


def perdem_validado(parceiro, nome):
    """Revistas ativas do parceiro (todos os anos) validadas cujo hash muda com o nome novo."""
    revistas = Revista.objects.filter(projeto__parceiro_ano__parceiro=parceiro, arquivada_em__isnull=True)
    return impacto.perdem_validado(lambda: Parceiro.objects.filter(pk=parceiro.pk).update(nome=nome), revistas)


@require_POST
@login_required(login_url="admin:login")
@permission_required("nucleo.change_parceiro", raise_exception=True)
def renomear_parceiro(request, ano, pk):
    """Item 6 (D-190). O nome vale para todos os anos e entra no hash (`nome_parceiro`): revista
    validada que mudaria só é afetada depois do modal de impacto (U2)."""
    parceiro = get_object_or_404(Parceiro, pk=pk)
    form = modelform_factory(Parceiro, fields=["nome"])(request.POST, instance=parceiro)
    if not form.is_valid():
        messages.error(request, "Parceiro não renomeado: " + " ".join(m for erros in form.errors.values() for m in erros))
        return redirect("cortes", ano)
    perdem = perdem_validado(parceiro, form.cleaned_data["nome"])
    if perdem and not request.POST.get("confirmar_impacto"):
        ano = get_object_or_404(Ano, ano=ano)
        contexto, _ = grade(request, ano, ler_post=False)
        renomear = {"pk": parceiro.pk, "nome": form.cleaned_data["nome"], "perdem": perdem, "form_id": f"renomear-{parceiro.pk}"}
        return TemplateResponse(request, "ui/cortes.html", {
            **contexto, "ano": ano, "anos": list(Ano.objects.order_by("-ano")), "secao": "cortes", "renomear": renomear,
        })  # fmt: skip
    form.save()
    messages.success(request, f"Parceiro renomeado para {parceiro.nome}." + (f" {len(perdem)} revista(s) perderam o “Validado”." if perdem else ""))
    return redirect("cortes", ano)


CELULA = re.compile(r"^c-(\d{1,9})-(\d{1,9})-(\d{1,9})$")


class CelulaForm(forms.Form):
    """Uma célula da grade: a linha do parceiro é a gravada agora com esta célula trocada, e passa
    pela mesma validação da grade inteira (`cascata.validar_linhas`, D-055)."""

    valor = forms.CharField(required=False, label="")  # o erro já começa por "ETAPA CC:"

    def __init__(self, *args, linha, indice, colunas, ano, **kwargs):
        super().__init__(*args, **kwargs)
        self.linha, self.indice, self.colunas, self.ano = linha, indice, colunas, ano

    def clean_valor(self):
        e, c = self.colunas[self.indice]
        try:
            lista = regra.interpretar(self.cleaned_data["valor"])
        except ValueError:
            raise forms.ValidationError(f"{e.codigo} {c.codigo}: cortes precisam ser inteiros (ex.: 350, 400, 500).") from None
        textos = [*self.linha[: self.indice], regra.formatar(lista), *self.linha[self.indice + 1 :]]
        self.valores = [(e2, c2, regra.interpretar(t)) for (e2, c2), t in zip(self.colunas, textos) if t]
        try:
            validar_linhas(self.valores, self.ano.pk)
        except forms.ValidationError as ex:
            raise forms.ValidationError([m for m in ex.messages if m.startswith(f"{e.codigo} {c.codigo}:")] or ex.messages) from None
        return regra.formatar(lista)


@require_POST
@login_required(login_url="admin:login")
def celula(request, ano):
    """Autosave de uma célula (U3, protocolo de `ui_autosave`). Cortes não tem bloqueio: o `original`
    (o texto da célula na tela) diferente do gravado é conflito (409, com o `atual`), nunca sobrescrita."""
    if not regra.pode_gravar(request.user):
        raise PermissionDenied
    ano = get_object_or_404(Ano, ano=ano)
    m = CELULA.match(request.POST.get("campo", ""))
    parceiro = m and Parceiro.objects.filter(pk=m[1]).first()
    etapa = m and Etapa.objects.filter(pk=m[2], ano=ano).first()
    componente = m and Componente.objects.filter(pk=m[3], ano=ano).first()
    if not (parceiro and etapa and componente):
        return erros(["Célula não encontrada neste ano. Recarregue a página."])
    colunas = [(e, c) for e in Etapa.objects.filter(ano=ano).order_by("ordem") for c in Componente.objects.filter(ano=ano).order_by("codigo")]
    indice = [(e.pk, c.pk) for e, c in colunas].index((etapa.pk, componente.pk))
    linha = regra.linhas_atuais(ano, colunas, [parceiro.pk]).get(parceiro.pk, [""] * len(colunas))
    if regra.formatar_texto(request.POST.get("original", "").strip()) != linha[indice]:
        e = _excecao(parceiro, linha[indice])
        return conflito(e.texto, e.atual)
    form = CelulaForm({"valor": request.POST.get("valor", "").strip()}, linha=linha, indice=indice, colunas=colunas, ano=ano)

    def gravar(dados):
        try:
            regra.gravar(request.user, ano, colunas, {parceiro.pk: (parceiro, form.valores, regra.SEP.join(linha))})
        except regra.Conflito as ex:
            raise _excecao(parceiro, ex.agora.split(regra.SEP)[indice] if ex.agora else "") from None
        return {"valor": dados["valor"]}

    revistas = lambda: Revista.objects.filter(  # noqa: E731
        projeto__parceiro_ano__ano=ano, projeto__parceiro_ano__parceiro=parceiro, arquivada_em__isnull=True
    ).select_related("projeto__parceiro_ano__parceiro", "projeto__ano", "componente")
    return responder_campo(request, form=form, gravar=gravar, revistas=revistas, titulo="Salvar o corte")


def _excecao(parceiro, atual):
    return Conflito(
        f"{parceiro}: outra pessoa mudou este corte depois que a página abriu (agora: {atual or 'vazio'}). "
        "Seu valor ficou na célula; Tentar de novo grava por cima.",
        atual,
    )


urlpatterns = [
    path("", cortes, name="cortes_inicio"),
    path("<int:ano>/", cortes, name="cortes"),
    path("<int:ano>/parceiro/", novo_parceiro, name="cortes_novo_parceiro"),
    path("<int:ano>/celula/", celula, name="cortes_celula"),
    path("<int:ano>/parceiro/<int:pk>/renomear/", renomear_parceiro, name="cortes_renomear_parceiro"),
]
