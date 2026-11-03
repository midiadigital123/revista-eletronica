"""Templates B (T12-T14: lista com abas, editor, impacto): /ui/templates/<ano>/, rota ui_templates. Convenções: docs/telas/design-system.md.

Mesma regra do admin (`admin/templates.py`): o form `TemplateForm` (validação do texto) e
`nucleo/templates_texto.py` (uso, impacto, assinatura, versão nova, preview). Ver exige
`view_template` ou `change_template` (403); gravar exige `change_template` + `add_templateversao`,
sem elas o editor é só leitura. Bloqueio por template, como o `BloqueioAdminMixin` do admin.

Salvar: texto igual ao da versão atual grava só o nome; texto mudado vai à tela de impacto (mesma
URL, nada gravado); "Confirmar e criar versão" com a assinatura da tela cria a versão N+1;
"Voltar e editar" reabre o editor com o texto pendente.

Editor por seção (U9b): o POST manda `secao-N-id` (hidden, conferido contra o fascículo; fora dele é
422), `secao-N-titulo` e `secao-N-corpo`; a view monta o mesmo markdown `## id` com `form_para_corpo`
e segue o fluxo acima. A tela de impacto e o "Voltar" continuam mandando o `texto` montado.
"""

import re

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.forms import modelform_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from nucleo.contexto import ano_da_sessao
from nucleo.admin.templates import TemplateForm
from nucleo.models import Ano, Template
from nucleo.models.texto import Fasciculo
from nucleo.servicos.resolver import versao_atual
from nucleo.templates_texto import (
    assinar, assinatura, com_uso, criar_versao, form_para_corpo, id_permitido, impacto, ler_assinatura,
    previa_secoes, proximo_passo, rotulo, secoes_para_form, secoes_permitidas,
)  # fmt: skip
from nucleo.texto import TEXTO_MAX
from nucleo.ui_bloqueio import com_bloqueio
from nucleo.variaveis import VARIAVEIS

FormTemplate = modelform_factory(Template, form=TemplateForm, fields=["nome"])  # ano/CC/fascículo não mudam (D-098)
GRUPOS = {}  # "Inserir variável" por grupo, na ordem de VARIAVEIS
for _v in VARIAVEIS:
    GRUPOS.setdefault(_v.grupo or "Automáticas (do cadastro)", []).append(_v)
GRANDE = f"Texto grande demais: o limite é {TEXTO_MAX:,} caracteres.".replace(",", ".") + " Encurte o texto para ver a pré-visualização."


def pode_ver(user):
    return user.has_perm("nucleo.view_template") or user.has_perm("nucleo.change_template")


def pode_gravar(user):
    return user.has_perms(["nucleo.change_template", "nucleo.add_templateversao"])


@require_GET
@login_required(login_url="admin:login")
def lista(request, ano=None):
    if not pode_ver(request.user):
        raise PermissionDenied
    anos = list(Ano.objects.order_by("-ano"))
    if ano is None:  # /ui/templates/ → ano mais recente
        if anos:
            return redirect("ui_templates", ano_da_sessao(request).ano)
        return TemplateResponse(request, "ui/templates/lista.html", {"anos": anos, "secao": "templates"})
    ano = get_object_or_404(Ano, ano=ano)
    aba = request.GET.get("aba") if request.GET.get("aba") in Fasciculo.values else Fasciculo.F1
    contagem = dict(Template.objects.filter(ano=ano).values_list("fasciculo").annotate(n=Count("pk")))
    templates = (
        com_uso(Template.objects.filter(ano=ano, fasciculo=aba))
        .select_related("componente")
        .order_by("componente__codigo", "nome")
    )
    contexto = {
        "ano": ano,
        "anos": anos,
        "secao": "templates",
        "aba": aba,
        "abas": [(f, contagem.get(f, 0)) for f in Fasciculo.values],
        "templates": templates,
        "pode_criar": request.user.has_perms(["nucleo.add_template", "nucleo.add_templateversao"]),
    }
    return TemplateResponse(request, "ui/templates/lista.html", contexto)


CAMPO_ID = re.compile(r"secao-(\d+)-id")


class IdInvalido(Exception):
    pass


def secoes_do_post(post, fasciculo):
    """[{id, titulo, corpo}] do editor por seção, na ordem de N; None se o POST não é por seção
    (tela de impacto e "Voltar" mandam o `texto` montado). Id fora do fascículo: IdInvalido (422)."""
    ns = sorted(int(m[1]) for k in post if (m := CAMPO_ID.fullmatch(k)))
    if not ns:
        return None
    secoes = []
    for n in ns:
        id_ = post[f"secao-{n}-id"]
        if not id_permitido(id_, fasciculo):
            raise IdInvalido(id_)
        titulo = " ".join(post.get(f"secao-{n}-titulo", "").splitlines())  # campo de uma linha
        secoes.append({"id": id_, "titulo": titulo, "corpo": post.get(f"secao-{n}-corpo", "").replace("\r\n", "\n")})
    return secoes


def _recusa(id_):
    return HttpResponse(f"Seção não prevista neste fascículo: {id_}. Recarregue o editor.", status=422, content_type="text/plain; charset=utf-8")


def _contexto_secoes(tpl, secoes):
    """Seções para o editor e o índice, com rótulo, erros por campo e a prévia."""
    if not secoes:  # template ainda sem texto: começa pelas fixas
        secoes = [{"id": i, "titulo": "", "corpo": ""} for i in secoes_permitidas(tpl.fasciculo)["fixas"]]
    corpo = form_para_corpo(secoes)
    if len(corpo) > TEXTO_MAX:
        html, erros, por_secao = "", [GRANDE], {s["id"]: [] for s in secoes}
    else:
        html, erros, por_secao = previa_secoes(secoes, tpl.fasciculo)
    fixas = secoes_permitidas(tpl.fasciculo)["fixas"]
    for s in secoes:
        s["rotulo"], s["removivel"], s["erros"] = rotulo(s["id"]), s["id"] not in fixas, por_secao[s["id"]]
        s["erro_titulo"] = any(campo == "titulo" for _, campo in s["erros"])
        s["erro_corpo"] = any(campo == "corpo" for _, campo in s["erros"])
    return {"secoes": secoes, "previa_html": html, "previa_erros": erros}


def _editor(request, tpl, form, secoes=None, status=200):
    if secoes is None:
        secoes = secoes_para_form(form["texto"].value() or "")
    contexto = {
        "tpl": tpl,
        "ano": tpl.ano,
        "secao": "templates",
        "form": form,
        "atual": versao_atual(tpl.pk),
        "grupos": GRUPOS,
        "pode_gravar": request.pode_gravar,
        "sem_permissao": not pode_gravar(request.user),
        "permitidas": secoes_permitidas(tpl.fasciculo),
        **_contexto_secoes(tpl, secoes),
    }
    ids = [s["id"] for s in contexto["secoes"]]
    contexto["proximo"] = proximo_passo(ids)
    contexto["passos"] = [(i, rotulo(i)) for i in ids if i.startswith("passo")]
    contexto["modelo"] = {"id": "__ID__", "rotulo": "__ROTULO__", "titulo": "", "corpo": "", "removivel": True, "erros": []}
    return TemplateResponse(request, "ui/templates/editar.html", contexto, status=status)


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@com_bloqueio(lambda request, pk: get_object_or_404(Template, pk=pk), pode_gravar)
def editar(request, pk):
    if not pode_ver(request.user):
        raise PermissionDenied
    tpl = get_object_or_404(Template.objects.select_related("ano", "componente"), pk=pk)
    if request.method == "GET":
        return _editor(request, tpl, FormTemplate(instance=tpl))

    if "_voltar" in request.POST:
        inicial = {"nome": request.POST.get("nome", ""), "texto": request.POST.get("texto", "")}
        messages.info(request, "Voltou da tela de impacto: nada foi gravado. Revise o texto e salve de novo.")
        return _editor(request, tpl, FormTemplate(instance=tpl, initial=inicial))

    try:
        secoes = secoes_do_post(request.POST, tpl.fasciculo)
    except IdInvalido as e:
        return _recusa(e)
    dados = request.POST
    if secoes is not None:
        dados = request.POST.copy()
        dados["texto"] = form_para_corpo(secoes)
    form = FormTemplate(dados, instance=tpl)
    valido = form.is_valid()
    if secoes is not None and valido and previa_secoes(secoes, tpl.fasciculo)[1]:
        valido = False  # título vazio ou linha "## x" num campo: o markdown montado esconderia
    if not valido:
        messages.error(request, "Nada foi gravado: corrija os erros marcados.")
        return _editor(request, tpl, form, secoes)
    if not form.texto_mudou:
        form.save()
        messages.success(request, "Nome salvo. O texto é igual ao da versão atual, então nenhuma versão nova foi criada.")
        return redirect("ui_templates_editar", tpl.pk)

    novo = form.cleaned_data["texto"]
    esperada = assinatura(novo, form.atual)
    if "_confirmar" in request.POST and ler_assinatura(request.POST) == esperada:
        form.save()
        numero = criar_versao(tpl, novo, request.user)
        messages.success(request, f"Versão {numero} criada." if numero else "Nome salvo. O texto já era o da versão atual.")
        return redirect("ui_templates_editar", tpl.pk)
    if "_confirmar" in request.POST:
        messages.warning(request, "Não salvo: o texto ou a versão atual mudou desde a tela de impacto. Confira o impacto de novo e confirme.")
    tpl.refresh_from_db()  # o form alterou o nome em memória
    contexto = {
        "tpl": tpl,
        "ano": tpl.ano,
        "secao": "templates",
        "nome": form.cleaned_data["nome"],
        "texto": novo,
        "assinatura": assinar(esperada),
        "base": form.atual,
        "nova": (form.atual.numero if form.atual else 0) + 1,
        "revistas": impacto(tpl, novo),
    }
    return TemplateResponse(request, "ui/templates/impacto.html", contexto)


@require_POST
def previa_ao_vivo(request, pk):
    """Fragmento HTMX do preview. Sem login ou permissão: 403 (o HTMX não troca o alvo e avisa)."""
    if not pode_ver(request.user):
        raise PermissionDenied
    tpl = get_object_or_404(Template, pk=pk)
    try:
        secoes = secoes_do_post(request.POST, tpl.fasciculo)
    except IdInvalido as e:
        return _recusa(e)
    if secoes is None:
        secoes = secoes_para_form(request.POST.get("texto", ""))
    contexto = {"oob": True, **_contexto_secoes(tpl, secoes)}
    return TemplateResponse(request, "ui/parciais/templates_previa.html", contexto)


urlpatterns = [
    path("", lista, name="ui_templates_inicio"),
    path("<int:ano>/", lista, name="ui_templates"),
    path("editar/<int:pk>/", editar, name="ui_templates_editar"),
    path("editar/<int:pk>/previa/", previa_ao_vivo, name="ui_templates_previa"),
]
