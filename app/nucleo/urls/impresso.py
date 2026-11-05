"""Tela do impresso (S13, D-072, D-077, D-094): o que mudou desde a última foto `impresso`.

Só leitura para todos com `view_revista`; o botão "Revista Impressa Atualizada" exige
`marcar_impressa` e a revista "Validado" na versão exibida. O clique leva o hash visto e grava
com o bloqueio do projeto (`lote.escrever_travado`): a tela não segura o bloqueio enquanto o
impresso lê, então a pedagógica continua editando. Revista readicionada compara com a foto
herdada (a cascata copia a foto para a revista nova, D-094). Sem foto: tudo aparece como novo.

O diff é por item (seção, escala da etapa, descritor, cores), em texto puro, na ordem da página:
por palavra (`diff_texto`), só os parágrafos ou linhas que mudaram, com 1 de contexto.
"""

import difflib
import re
from itertools import zip_longest

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
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
        linhas += [_linha(chave.split("-")[1], x) for x in d["scale"][chave]]
    return "\n".join(linhas)


def _linha(n, x):
    """"Padrão 2: 556–640: texto [item: id.tipo]": cada linha se explica sozinha no diff; fim e arquivo
    da tarefa também vão para o InDesign."""
    faixa = f"{x['level']}–{x['fim']}" if "fim" in x else str(x["level"])
    item = f" [item: {x['item']['id']}.{x['item']['tipo']}]" if "item" in x else ""
    return f"Padrão {n}: {faixa}: {x['content']}{item}"


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


def _partes(velho, novo):
    """[(igual|del|ins, texto)] por palavra; cada palavra leva o espaço que a segue."""
    a, b = re.findall(r"\S+\s*", velho), re.findall(r"\S+\s*", novo)
    partes = []
    for op, i0, i1, j0, j1 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "equal":
            partes.append(("igual", "".join(a[i0:i1])))
            continue
        if i1 > i0:
            partes.append(("del", "".join(a[i0:i1])))
        if j1 > j0:
            partes.append(("ins", "".join(b[j0:j1])))
    return partes


def diff_texto(velho, novo, prosa):
    """(blocos, trecho) do que mudou entre dois textos puros, para o InDesign.

    Unidade: parágrafo (`prosa`, seções) ou linha (escala, descritor, cores). Só as unidades que mudaram,
    com 1 de contexto antes e depois; o resto vira um bloco "pulo" ("… 3 parágrafos sem mudança").
    Blocos: contexto {texto}; pulo {rotulo}; inline {partes} (prosa: del e ins no mesmo parágrafo);
    par {antes, depois} (linhas: a velha e a nova, cada uma None se não existe).
    `trecho`: só as unidades novas que mudaram, no texto novo (o que se cola no InDesign)."""
    sep = "\n\n" if prosa else "\n"
    a, b = ([u.strip() for u in t.split(sep) if u.strip()] for t in (velho, novo))
    nome = "parágrafo" if prosa else "linha"
    blocos, trecho, fim = [], [], 0

    def pulo(n):
        return {"tipo": "pulo", "rotulo": f"{n} {nome}{'s' if n > 1 else ''} sem mudança"}

    for grupo in difflib.SequenceMatcher(None, a, b, autojunk=False).get_grouped_opcodes(1):
        if grupo[0][1] > fim:
            blocos.append(pulo(grupo[0][1] - fim))
        for op, i0, i1, j0, j1 in grupo:
            if op == "equal":
                blocos += [{"tipo": "contexto", "texto": x} for x in a[i0:i1]]
                continue
            trecho += b[j0:j1]
            # ponytail: pareia na ordem; um parágrafo inserido no meio de uma troca sai como del + ins inteiros.
            for v, n in zip_longest(a[i0:i1], b[j0:j1]):
                partes = _partes(v or "", n or "")
                if prosa:
                    blocos.append({"tipo": "inline", "partes": partes})
                else:
                    antes = v and [p for p in partes if p[0] != "ins"]
                    depois = n and [p for p in partes if p[0] != "del"]
                    blocos.append({"tipo": "par", "antes": antes, "depois": depois})
        fim = grupo[-1][2]
    if blocos and fim < len(a):
        blocos.append(pulo(len(a) - fim))
    return blocos, sep.join(trecho)


def _rotulos(*conteudos):
    """{(fascículo, id): título em texto puro} das seções (o rótulo humano de "introducao")."""
    return {
        (f.upper(), s["id"]): texto.html_para_texto(s["titulo"]).strip()
        for c in conteudos if c for f in ("f1", "f2") for s in c[f]["secoes"] or []
    }  # fmt: skip


def mudancas(antes, depois):
    """{fascículo: {grupo: [item]}} só com o que mudou. `antes` None (sem foto): tudo é novo.
    Item: antes/depois (texto inteiro), blocos (só alterado), trecho (o novo que mudou) e rótulos."""
    a, d = textos(antes) if antes else {}, textos(depois)
    titulos = _rotulos(antes, depois)
    saida = {}
    for chave in [*d, *(k for k in a if k not in d)]:  # removidos no fim
        velho, novo = a.get(chave), d.get(chave)
        if velho == novo:
            continue
        fasciculo, grupo, item = chave
        secao = grupo == item != "Cores"
        blocos, trecho = None, novo
        if velho is not None and novo is not None:
            blocos, trecho = diff_texto(velho, novo, prosa=secao)
            if not blocos:  # só espaço em branco: nada a levar ao InDesign
                continue
        rotulo_grupo = titulos.get((fasciculo, grupo)) or grupo if secao else grupo
        saida.setdefault(fasciculo, {}).setdefault(grupo, []).append({
            "item": item, "antes": velho, "depois": novo, "blocos": blocos, "trecho": trecho,
            "rotulo_grupo": rotulo_grupo, "rotulo": rotulo_grupo if secao or item == grupo else f"{grupo} · {item}",
        })  # fmt: skip
    return saida


def _revista(pk):
    try:
        return resolver.carregar(pk)
    except Revista.DoesNotExist:
        raise Http404


def situacao(revista):
    """Foto, hash, "Validado" e pendência do impresso de uma revista (lista da tela B e `estado`)."""
    resolvido = resolver.resolver(revista)
    atual = resolver.hash_validado(revista, resolvido)
    foto = ultima_impressa(revista)
    return {
        "revista": revista, "foto": foto, "hash": atual, "validada": validacao.validada(revista, atual),
        "pendente": impresso_pendente(foto, resolvido), "resolvido": resolvido,
    }  # fmt: skip


def estado(revista, s=None):
    """O que a tela do impresso mostra (página antiga e tela B): `situacao` + o que mudou desde a foto.
    `s`: a `situacao` já calculada (a lista da tela B não resolve a revista duas vezes)."""
    s = s or situacao(revista)
    foto = s["foto"]
    return s | {"mudancas": mudancas(foto and resolver.impresso_de(foto.conteudo), resolver.impresso_de(s["resolvido"]))}


def pode_marcar(user, revista):
    return user.has_perm("nucleo.marcar_impressa") and revista.arquivada_em is None


def gravar(request, revista):
    """"Revista Impressa Atualizada" com o hash visto, sob o bloqueio do projeto; resultado em messages."""
    hash_visto = request.POST.get("hash_visto", "")
    motivo = lote.escrever_travado(
        revista.projeto, request.user, lambda: validacao.marcar_impressa(revista.pk, hash_visto, request.user)
    )
    if motivo:
        messages.error(request, f"Impresso não atualizado: {motivo.rstrip('.')}.")
    else:
        messages.success(request, "Revista Impressa Atualizada: os avisos desta revista foram zerados.")


@protegida
def impresso(request, pk):
    revista = _revista(pk)
    ctx = contexto(
        request, f"Impresso: {revista}", **estado(revista), pode=pode_marcar(request.user, revista),
        url_painel=reverse("painel", args=[revista.projeto.ano.ano]),
    )  # fmt: skip
    return TemplateResponse(request, "nucleo/impresso.html", ctx)


@require_POST
@login_required
@permission_required("nucleo.marcar_impressa", raise_exception=True)
def marcar(request, pk):
    gravar(request, _revista(pk))
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
