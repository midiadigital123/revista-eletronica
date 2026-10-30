"""Tela do impresso (S13, D-072, D-077, D-094): o que mudou desde a última foto `impresso`.

Só leitura para todos com `view_revista`; o botão "Revista Impressa Atualizada" exige
`marcar_impressa` e a revista "Validado" na versão exibida. O clique leva o hash visto e grava
com o bloqueio do projeto (`lote.escrever_travado`): a tela não segura o bloqueio enquanto o
impresso lê, então a pedagógica continua editando. Revista readicionada compara com a foto
herdada (a cascata copia a foto para a revista nova, D-094). Sem foto: tudo aparece como novo.

O diff é por item (seção, escala da etapa, descritor, cores), em texto puro, na ordem da página.
"""

import difflib

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.safestring import mark_safe
from django.views.decorators.http import require_POST

from nucleo import texto
from nucleo.admin import lote
from nucleo.models import Revista
from nucleo.servicos import resolver, validacao
from nucleo.servicos.planilhas import descritores, zip_planilhas
from nucleo.urls.painel import contexto, impresso_pendente, ultima_impressa
from nucleo.urls.preview import protegida


def _secao(s):
    return f"{texto.html_para_texto(s['titulo'])}\n\n{texto.html_para_texto(s['corpo'])}"


def _escala(dados):
    """Rótulo e faixa de cada padrão (cortes e nomes `pdNN`, D-175)."""
    faixa, n = dados["scaleRange"], len(dados["padroes"])
    limites = [faixa["min"], *(dados["cortes"].get(f"padrao-{i}") for i in range(1, n)), faixa["max"]]
    return "\n".join(f"{p['rotulo']}: {limites[i]} a {limites[i + 1]}" for i, p in enumerate(dados["padroes"]))


def _descritor(codigo, d):
    bncc = d["bncc"]
    linhas = [f"{codigo}: {d['description']}", *(f"Pré-requisito: {p}" for p in d["prerequisites"])]
    linhas += [f"BNCC: {bncc['practices']} / {bncc['knowledge']}", *(f"Habilidade: {s}" for s in bncc["skills"])]
    for chave in sorted(d["scale"], key=lambda c: int(c.split("-")[1])):  # jsonb não guarda a ordem
        linhas.append(f"Padrão {chave.split('-')[1]}:")
        linhas += [f"  {x['level']}: {x['content']}" for x in d["scale"][chave]]
    return "\n".join(linhas)


def textos(conteudo):
    """{(fascículo, grupo, item): texto puro} de `impresso_de(...)`, na ordem das páginas:
    introdução, cores, etapas (escala e descritores), demais seções do F1; seções do F2."""
    f1, saida = conteudo["f1"], {}
    secoes = f1["secoes"] or []
    for s in secoes:
        if s["id"] == "introducao":
            saida["F1", s["id"], s["id"]] = _secao(s)
    if f1["cores"]:
        ordem = sorted(f1["cores"], key=lambda c: int(c.split("-")[1]))
        saida["F1", "Cores", "Cores"] = "\n".join(f"Padrão {c.split('-')[1]}: {f1['cores'][c]}" for c in ordem)
    for etapa in f1["etapas"]:
        dados = f1["dados"][etapa]
        saida["F1", etapa.upper(), "Escala"] = _escala(dados)
        for codigo, d in descritores(dados):
            saida["F1", etapa.upper(), codigo] = _descritor(codigo, d)
    for s in secoes:
        if s["id"] != "introducao":
            saida["F1", s["id"], s["id"]] = _secao(s)
    for s in conteudo["f2"]["secoes"] or []:
        saida["F2", s["id"], s["id"]] = _secao(s)
    return saida


def mudancas(antes, depois):
    """{fascículo: {grupo: [item]}} só com o que mudou. `antes` None (sem foto): tudo é novo."""
    a, d = textos(antes) if antes else {}, textos(depois)
    saida = {}
    for chave in [*d, *(k for k in a if k not in d)]:  # removidos no fim
        velho, novo = a.get(chave), d.get(chave)
        if velho == novo:
            continue
        fasciculo, grupo, item = chave
        tabela = None
        if velho is not None and novo is not None:
            tabela = mark_safe(  # o HtmlDiff escapa &, < e >
                difflib.HtmlDiff(wrapcolumn=70).make_table(velho.splitlines(), novo.splitlines(), "Antes", "Depois", context=True, numlines=2)
            )
        saida.setdefault(fasciculo, {}).setdefault(grupo, []).append(
            {"item": item, "antes": velho, "depois": novo, "tabela": tabela}
        )
    return saida


def _revista(pk):
    try:
        return resolver.carregar(pk)
    except Revista.DoesNotExist:
        raise Http404


@protegida
def impresso(request, pk):
    revista = _revista(pk)
    resolvido = resolver.resolver(revista)
    atual = resolver.hash_validado(revista, resolvido)
    foto = ultima_impressa(revista)
    validada = validacao.validada(revista, atual)
    pendente = impresso_pendente(foto, resolvido)
    ctx = contexto(
        request, f"Impresso: {revista}", revista=revista, foto=foto, hash=atual, validada=validada, pendente=pendente,
        mudancas=mudancas(foto and resolver.impresso_de(foto.conteudo), resolver.impresso_de(resolvido)),
        pode=request.user.has_perm("nucleo.marcar_impressa") and revista.arquivada_em is None,
        url_painel=reverse("painel", args=[revista.projeto.ano.ano]),
    )  # fmt: skip
    return TemplateResponse(request, "nucleo/impresso.html", ctx)


@require_POST
@login_required(login_url="admin:login")
@permission_required("nucleo.marcar_impressa", raise_exception=True)
def marcar(request, pk):
    revista = _revista(pk)
    hash_visto = request.POST.get("hash_visto", "")
    motivo = lote.escrever_travado(
        revista.projeto, request.user, lambda: validacao.marcar_impressa(revista.pk, hash_visto, request.user)
    )
    if motivo:
        messages.error(request, f"Impresso não atualizado: {motivo.rstrip('.')}.")
    else:
        messages.success(request, "Revista Impressa Atualizada: os avisos desta revista foram zerados.")
    return HttpResponseRedirect(reverse("impresso", args=[pk]))


@protegida
def planilhas(request, pk):
    nome, dados = zip_planilhas(_revista(pk))
    resposta = HttpResponse(dados, content_type="application/zip")
    resposta["Content-Disposition"] = f'attachment; filename="{nome}"'
    return resposta


urlpatterns = [
    path("<int:pk>/", impresso, name="impresso"),
    path("<int:pk>/marcar/", marcar, name="impresso_marcar"),
    path("<int:pk>/planilhas/", planilhas, name="impresso_planilhas"),
]
