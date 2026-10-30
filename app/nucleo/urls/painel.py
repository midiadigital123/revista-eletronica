"""Regra do painel da temporada e validação em lote (S12, D-078, D-120). A tela do painel é
`urls/ui_painel.py` (rota `painel`); aqui ficam as linhas, os filtros e o validar em lote do admin.

Uma linha por revista ativa do ano: ✓ ou "falta" por coluna, com link para a correção.
O resolvido é montado uma vez por linha e serve ao hash e às pendências.
Validação em lote: mostra o diff de cada revista e envia pares (revista, hash visto); cada par
é gravado ou recusado sozinho, com o bloqueio do projeto (`lote.escrever_travado`, D-121).
O diff é contra a última foto do impresso: o "Validado" guarda só o hash, não o conteúdo.
"""

import difflib
import json

from django.contrib import admin, messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.http import urlencode
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_http_methods

from nucleo.admin import lote
from nucleo.models import Ano, FotoRevista, Parceiro, Revista, Template
from nucleo.models.revista import Motivo
from nucleo.servicos import bloqueio, resolver, validacao

# Coluna → códigos de `pendencias` que ela mostra (ordem das colunas da tela).
COLUNAS = {
    "matriz": ("Matriz", ("matriz", "corte_sem_matriz", "corte_invalido")),
    "template_f1": ("Template F1", ("template_f1",)),
    "template_f2": ("Template F2", ("template_f2",)),
    "variaveis": ("Variáveis", ("variaveis", "nome_projeto")),
    "svg": ("SVG", ("svg", "ids_svg")),
    "capa": ("Capa", ("capa",)),
    "validado": ("Validado", ()),
    "impresso": ("Impresso", ()),
}


def link(codigo, revista):
    """Onde corrigir cada pendência (o `Pendencia.link` fica nulo: o painel monta pelo código)."""
    ano = {"ano": revista.projeto.ano.ano}
    if codigo in ("matriz", "corte_sem_matriz"):
        return reverse("admin:nucleo_projeto_escolher_matriz") + "?" + urlencode(ano)
    if codigo == "corte_invalido":
        return reverse("admin:nucleo_corte_changelist") + "?" + urlencode(ano)
    if codigo in ("variaveis", "nome_projeto"):
        return reverse("admin:nucleo_projeto_change", args=[revista.projeto_id])
    if codigo == "impresso":
        return reverse("impresso", args=[revista.pk])  # tela do impresso (S13)
    return reverse("admin:nucleo_revista_change", args=[revista.pk])  # templates, SVG, capa, Validado


def ultima_impressa(revista):
    # ponytail: carrega o JSON inteiro da foto; comparar por hash pede uma coluna hash_impresso
    # (o `hash` da foto inclui SVG e capa, D-118) = migração. Fazer se o painel ficar lento.
    return FotoRevista.objects.filter(revista=revista, motivo=Motivo.IMPRESSO).order_by("-criada_em", "-pk").first()


def impresso_pendente(foto, resolvido):
    """O impresso confere só textos e escalas (D-118): trocar SVG ou capa não o derruba."""
    return foto is None or resolver.impresso_de(foto.conteudo) != resolver.impresso_de(resolvido)


def linha(revista):
    resolvido = resolver.resolver(revista)
    atual = resolver.hash_validado(revista, resolvido)
    pendentes = resolver.pendencias(revista, resolvido)
    foto = ultima_impressa(revista)
    celulas = {}
    for chave, (_, codigos) in COLUNAS.items():
        faltas = [p for p in pendentes if p.codigo in codigos]
        celulas[chave] = {
            "ok": not faltas,
            "dica": " ".join(p.mensagem for p in faltas),
            "link": link(faltas[0].codigo, revista) if faltas else None,
        }
    if not validacao.validada(revista, atual):
        celulas["validado"] = {"ok": False, "dica": "Sem “Validado” nesta versão.", "link": link("validado", revista)}
    if impresso_pendente(foto, resolvido):
        celulas["impresso"] = {"ok": False, "dica": "Impresso não atualizado nesta versão.", "link": None}
    celulas["impresso"]["link"] = link("impresso", revista)  # com ✓ também: a tela mostra a última foto
    return {"revista": revista, "celulas": [celulas[c] | {"coluna": c} for c in COLUNAS], "faltas": celulas}


def revistas_do_ano(ano):
    return (
        Revista.objects.filter(ano=ano, arquivada_em__isnull=True)
        .select_related("projeto__parceiro_ano__parceiro", "projeto__ano", "componente")
        .order_by("projeto__parceiro_ano__parceiro__nome", "componente__codigo")
    )


def contexto(request, titulo, **extra):
    return {**admin.site.each_context(request), "title": titulo, **extra}


def filtrar(ano, params):
    """Linhas do painel com os filtros falta/parceiro/template (inválidos são ignorados).
    `todas` = linhas antes do filtro de falta (serve às contagens por coluna da tela B)."""
    revistas = revistas_do_ano(ano)
    parceiros = list(Parceiro.objects.filter(parceiroano__ano=ano).order_by("nome"))
    parceiro = next((p for p in parceiros if str(p.pk) == params.get("parceiro")), None)
    falta = params.get("falta") if params.get("falta") in COLUNAS else None
    pedido = params.get("template", "")
    # Inexistente ou de outro ano: ignorado, como o parceiro inválido.
    template = Template.objects.filter(ano=ano, pk=pedido).select_related("componente").first() if pedido.isdigit() else None
    if parceiro is not None:
        revistas = revistas.filter(projeto__parceiro_ano__parceiro=parceiro)
    if template is not None:
        revistas = revistas.filter(revistafasciculo__template=template)  # 1 fascículo por template: sem duplicar
    todas = [linha(r) for r in revistas]
    linhas = [x for x in todas if not x["faltas"][falta]["ok"]] if falta else todas
    return {"linhas": linhas, "todas": todas, "parceiros": parceiros, "parceiro": parceiro, "falta": falta, "template": template}


def diff(revista, resolvido):
    """Tabela do difflib: última foto do impresso | agora (só os trechos que mudaram)."""
    foto = ultima_impressa(revista)
    if foto is None:
        return None
    antes, agora = (json.dumps(c, indent=1, sort_keys=True, ensure_ascii=False).splitlines() for c in (foto.conteudo, resolvido))
    if antes == agora:
        return ""
    tabela = difflib.HtmlDiff(wrapcolumn=70).make_table(antes, agora, "Última impressa", "Agora", context=True, numlines=2)
    return mark_safe(tabela)  # o HtmlDiff escapa &, < e >


def validar_pares(request, ano, pedidos):
    """Grava os pares "pk:hash" (cada um sozinho, sob o bloqueio do projeto: D-121) e avisa
    pelo `messages`. Serve ao admin e à tela B (urls/ui_validar.py). Devolve os pks pedidos."""
    pares = {}
    for par in pedidos:
        pk, _, hash_visto = par.partition(":")
        if pk.isdigit():
            pares[int(pk)] = hash_visto
    revistas = revistas_do_ano(ano).filter(pk__in=pares)
    itens = [(str(r), r.projeto, lambda r=r: validacao.validar(r.pk, pares[r.pk], request.user)) for r in revistas]
    feitos = lote.aplicar(request, itens)  # recusadas: "Pulados: revista (motivo)"
    lote.avisar_pulados(request, [f"revista {pk} (não encontrada ou arquivada)" for pk in set(pares) - {r.pk for r in revistas}])
    if feitos:
        messages.success(request, f"Validadas {feitos} revista(s).")
    return list(pares)


def itens_validar(ano, ids):
    """O que a validação mostra de cada revista ativa do ano em `ids` (admin e tela B)."""
    itens = []
    for revista in revistas_do_ano(ano).filter(pk__in=ids):
        resolvido = resolver.resolver(revista)
        itens.append(
            {
                "revista": revista,
                "hash": (atual := resolver.hash_validado(revista, resolvido)),
                "validada": validacao.validada(revista, atual),
                "pendencias": [p._replace(link=link(p.codigo, revista)) for p in resolver.pendencias(revista, resolvido)],
                "desatualizadas": resolver.secoes_desatualizadas(revista),  # D-087: só avisa
                "diff": diff(revista, resolvido),
                "editando": bloqueio.quem_bloqueia(revista.projeto),  # o lote vai pular (D-121)
            }
        )
    return itens


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@permission_required("nucleo.validar_revista", raise_exception=True)
def validar_lote(request, ano):
    ano = get_object_or_404(Ano, ano=ano)
    if request.method == "POST":
        validar_pares(request, ano, request.POST.getlist("par"))
        return HttpResponseRedirect(reverse("painel", args=[ano.ano]))
    ids = [int(x) for x in request.GET.getlist("revista") if x.isdigit()]
    ctx = contexto(
        request, f"Validar em lote ({ano.ano})", itens=itens_validar(ano, ids), url_painel=reverse("painel", args=[ano.ano])
    )
    return TemplateResponse(request, "nucleo/painel_validar.html", ctx)


urlpatterns = [
    path("<int:ano>/validar/", validar_lote, name="painel_validar"),
]
