"""Lotes (D-102, D-121): "Escolher matriz" (ParceiroAno) e "Escolher template F1/F2" (Revista).

Páginas próprias (rotas em ProjetoAdmin/RevistaAdmin.get_urls), não actions: os admins com o
BloqueioAdminMixin não podem ter actions de escrita. Cada alvo é gravado com o bloqueio do
projeto (`escrever_travado`); alvo travado é pulado e listado na mensagem.
"""

import logging

from django import forms
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Exists, OuterRef, Prefetch
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path
from django.utils.http import urlencode

from nucleo.models import (
    Ano,
    Componente,
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

log = logging.getLogger(__name__)


def escrever_travado(projeto, usuario, escrever):
    """Roda `escrever()` numa transação, segurando o bloqueio do projeto.

    Devolve None se gravou, ou o motivo do pulo: outra sessão (outro usuário ou outra aba)
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


def escolher_ano(request):
    """(anos, ano escolhido por ?ano=AAAA; padrão: o mais recente)."""
    anos = list(Ano.objects.order_by("-ano"))
    pedido = request.GET.get("ano", "")
    ano = next((a for a in anos if str(a.ano) == pedido), anos[0] if anos else None)
    return anos, ano


def rota(model_admin, caminho, view, nome):
    """path() de uma view extra do admin, com login/permissão e nome "nucleo_<modelo>_<nome>"."""
    return path(caminho, model_admin.admin_site.admin_view(view), name=f"nucleo_{model_admin.opts.model_name}_{nome}")


def filtro(rotulo, opcoes, ativo, chave, extra=None):
    """Linha de links do filtro: [(texto, url, ativo)]."""
    return (
        rotulo,
        [(str(o), "?" + urlencode({**(extra or {}), chave: valor}), o == ativo) for o, valor in opcoes],
    )


def contexto(model_admin, request, titulo, **extra):
    return {
        **model_admin.admin_site.each_context(request),
        "title": titulo,
        "opts": model_admin.model._meta,
        **extra,
    }


# --- Escolher matriz ------------------------------------------------------------


class MatrizLoteForm(forms.Form):
    alvos = forms.ModelMultipleChoiceField(None, label="Parceiros", widget=forms.CheckboxSelectMultiple)
    matriz = forms.ModelChoiceField(queryset=None)

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


def escolher_matriz(model_admin, request):
    if not request.user.has_perm("nucleo.change_parceiroano"):
        raise PermissionDenied
    anos, ano = escolher_ano(request)
    form = None
    if ano is not None:
        form = MatrizLoteForm(request.POST or None, ano=ano)
        if request.method == "POST" and form.is_valid():
            matriz = form.cleaned_data["matriz"]

            def gravar(pa):
                pa.matriz = matriz
                pa.save(update_fields=["matriz"])

            itens = [
                (str(pa.parceiro), pa.ativos[0] if pa.ativos else None, lambda pa=pa: gravar(pa))
                for pa in form.cleaned_data["alvos"]
            ]
            feitos = aplicar(request, itens)
            messages.success(request, f"Matriz {matriz.nome} escolhida para {feitos} parceiro(s).")
            return HttpResponseRedirect(request.get_full_path())
    ctx = contexto(
        model_admin, request, "Escolher matriz", form=form,
        filtros=[filtro("Ano", [(a, a.ano) for a in anos], ano, "ano")],
        vazio="Nenhum ano cadastrado.",
    )  # fmt: skip
    return TemplateResponse(request, "nucleo/lote.html", ctx)


# --- Escolher template F1/F2 ------------------------------------------------------


class TemplateLoteForm(forms.Form):
    alvos = forms.ModelMultipleChoiceField(None, label="Revistas", widget=forms.CheckboxSelectMultiple)
    template_f1 = forms.ModelChoiceField(queryset=None, required=False, label="Template F1")
    template_f2 = forms.ModelChoiceField(queryset=None, required=False, label="Template F2")

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


def escolher_template(model_admin, request):
    if not request.user.has_perm("nucleo.change_revistafasciculo"):
        raise PermissionDenied
    anos, ano = escolher_ano(request)
    filtros, form, vazio = [], None, "Nenhum ano cadastrado."
    if ano is not None:
        componentes = list(Componente.objects.filter(ano=ano).order_by("codigo"))
        pedido = request.GET.get("componente", "")
        componente = next((c for c in componentes if str(c.pk) == pedido), None)
        filtros = [
            filtro("Ano", [(a, a.ano) for a in anos], ano, "ano"),
            filtro("Componente", [(c, c.pk) for c in componentes], componente, "componente", {"ano": ano.ano}),
        ]
        vazio = "Escolha o componente: o template tem de ser do mesmo componente da revista."
        if componente is not None:
            form = TemplateLoteForm(request.POST or None, ano=ano, componente=componente)
    if form is not None and request.method == "POST" and form.is_valid():
        novos = {f: form.cleaned_data[f"template_{f.lower()}"] for f in Fasciculo.values}
        novos = {f: t for f, t in novos.items() if t is not None}
        copias = RevistaSecao.objects.filter(revista_fasciculo=OuterRef("pk"))

        def gravar(revista):
            # Dentro do bloqueio: ninguém cria cópia de seção enquanto conferimos.
            if not list(Revista.objects.select_for_update().filter(pk=revista.pk, arquivada_em__isnull=True).values_list("pk")):
                return "revista arquivada"
            com_copias = []
            for rf in RevistaFasciculo.objects.filter(revista=revista, fasciculo__in=novos).annotate(
                tem_copias=Exists(copias)
            ):
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

        itens = [(str(r), r.projeto, lambda r=r: gravar(r)) for r in form.cleaned_data["alvos"]]
        feitos = aplicar(request, itens)
        messages.success(request, f"Template escolhido em {feitos} revista(s).")
        return HttpResponseRedirect(request.get_full_path())
    ctx = contexto(model_admin, request, "Escolher template F1/F2", form=form, filtros=filtros, vazio=vazio)
    return TemplateResponse(request, "nucleo/lote.html", ctx)
