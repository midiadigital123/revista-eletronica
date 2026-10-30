"""Templates B (T12-T14: lista com abas, editor, impacto): /ui/templates/<ano>/, rota ui_templates. Convenções: docs/telas/design-system.md.

Mesma regra do admin (`admin/templates.py`): o form `TemplateForm` (validação do texto) e
`nucleo/templates_texto.py` (uso, impacto, assinatura, versão nova, preview). Ver exige
`view_template` ou `change_template` (403); gravar exige `change_template` + `add_templateversao`,
sem elas o editor é só leitura. Bloqueio por template, como o `BloqueioAdminMixin` do admin.

Salvar: texto igual ao da versão atual grava só o nome; texto mudado vai à tela de impacto (mesma
URL, nada gravado); "Confirmar e criar versão" com a assinatura da tela cria a versão N+1;
"Voltar e editar" reabre o editor com o texto pendente.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Count
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from nucleo.admin.templates import TemplateForm
from nucleo.models import Ano, Template
from nucleo.models.texto import Fasciculo
from nucleo.servicos.resolver import versao_atual
from nucleo.templates_texto import assinar, assinatura, com_uso, criar_versao, impacto, ler_assinatura, previa
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
            return redirect("ui_templates", anos[0].ano)
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


def _editor(request, tpl, form, status=200):
    corpo = form["texto"].value() or ""
    html, erros = previa(corpo, tpl.fasciculo) if len(corpo) <= TEXTO_MAX else ("", [GRANDE])
    contexto = {
        "tpl": tpl,
        "ano": tpl.ano,
        "secao": "templates",
        "form": form,
        "atual": versao_atual(tpl.pk),
        "grupos": GRUPOS,
        "pode_gravar": request.pode_gravar,
        "sem_permissao": not pode_gravar(request.user),
        "previa_html": html,
        "previa_erros": erros,
    }
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

    form = FormTemplate(request.POST, instance=tpl)
    if not form.is_valid():
        messages.error(request, "Nada foi gravado: corrija os erros marcados.")
        return _editor(request, tpl, form)
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
    corpo = request.POST.get("texto", "")
    html, erros = previa(corpo, tpl.fasciculo) if len(corpo.replace("\r\n", "\n")) <= TEXTO_MAX else ("", [GRANDE])
    return TemplateResponse(request, "ui/parciais/templates_previa.html", {"previa_html": html, "previa_erros": erros})


urlpatterns = [
    path("", lista, name="ui_templates_inicio"),
    path("<int:ano>/", lista, name="ui_templates"),
    path("editar/<int:pk>/", editar, name="ui_templates_editar"),
    path("editar/<int:pk>/previa/", previa_ao_vivo, name="ui_templates_previa"),
]
