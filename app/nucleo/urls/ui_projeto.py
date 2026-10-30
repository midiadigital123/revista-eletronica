"""Projeto B (T15/T16: nome, variáveis, passo e cor): /ui/projeto/<pk>/, rota ui_projeto. Convenções: docs/telas/design-system.md.

Regra em `nucleo/projeto.py` (os mesmos forms do change form do admin); bloqueio pela peça comum
(`ui_bloqueio.com_bloqueio`). Lista do ano (T15) em /ui/projeto/ano/<ano>/.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.forms.utils import pretty_name
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_GET, require_http_methods

from nucleo.models import Ano, CorPadrao, MatrizEtapaCC, Projeto
from nucleo.projeto import MAX_CORES, ProjetoForm, formsets
from nucleo.servicos.resolver import cores_efetivas, valores_das_variaveis
from nucleo.ui_bloqueio import com_bloqueio
from nucleo.variaveis import VARIAVEIS

# ponytail: exige também add/change/delete de passo e cor (os perfis dão tudo junto); o admin
# deixaria quem só tem change_projeto editar nome e variáveis. Separar se surgir esse perfil.
ESCRITA = [f"nucleo.{a}_{m}" for m in ("projetopasso", "projetocor") for a in ("add", "change", "delete")]
ESCRITA.append("nucleo.change_projeto")
GRUPOS = list(dict.fromkeys(v.grupo for v in VARIAVEIS if not v.automatica))


def pode_ver(user):
    return user.has_perm("nucleo.view_projeto") or user.has_perm("nucleo.change_projeto")


def pode_gravar(user):
    return user.has_perms(ESCRITA)


def _alvo(request, pk, **kwargs):
    """Trava o projeto; arquivado (D-093) não trava: a view mostra só leitura."""
    projeto = get_object_or_404(Projeto, pk=pk)
    return None if projeto.arquivado_em else projeto


@require_GET
@login_required(login_url="admin:login")
def inicio(request):
    ano = Ano.objects.order_by("-ano").first()
    return redirect("ui_projeto_lista", ano.ano) if ano else redirect("admin:nucleo_projeto_changelist")


@require_GET
@login_required(login_url="admin:login")
def lista(request, ano):
    if not pode_ver(request.user):
        raise PermissionDenied
    ano = get_object_or_404(Ano, ano=ano)
    projetos = (
        Projeto.objects.filter(ano=ano)
        .select_related("parceiro_ano__parceiro", "parceiro_ano__matriz")
        .order_by("arquivado_em", "parceiro_ano__parceiro__nome")  # ativos (NULL) primeiro
    )
    contexto = {"ano": ano, "anos": Ano.objects.order_by("-ano"), "secao": "variaveis", "projetos": projetos}
    return TemplateResponse(request, "ui/projeto/lista.html", contexto)


def _vestir(*forms, desabilitar=False):
    """Classes do design system nos widgets, `aria-invalid` no campo com erro; só leitura: disabled.

    Linha de formset (prefixo `passos-0`): o <th> não rotula o controle, então vai `aria-label`.
    O checkbox Remover já tem <label>."""
    for f in forms:
        for nome, campo in f.fields.items():
            tipo = campo.widget.attrs.get("type") or getattr(campo.widget, "input_type", "")
            classe = {"select": "select", "checkbox": "", "color": "pj-cor"}.get(tipo, "input")
            if classe:
                campo.widget.attrs["class"] = classe
            if "-" in (f.prefix or "") and tipo not in ("checkbox", "hidden"):
                campo.widget.attrs.setdefault("aria-label", campo.label or pretty_name(nome))
            if f.is_bound and nome in f.errors:
                campo.widget.attrs["aria-invalid"] = "true"
            campo.disabled |= desabilitar


@require_http_methods(["GET", "POST"])
@login_required(login_url="admin:login")
@com_bloqueio(_alvo, pode_gravar)
def projeto(request, pk):
    if not pode_ver(request.user):
        raise PermissionDenied
    projeto = get_object_or_404(Projeto.objects.select_related("ano", "parceiro_ano__parceiro", "parceiro_ano__matriz"), pk=pk)
    arquivado = projeto.arquivado_em is not None
    if arquivado and request.method == "POST":
        raise PermissionDenied  # arquivado é congelado (D-093, D-167)
    pode = request.pode_gravar and not arquivado

    if request.method == "POST":
        form = ProjetoForm(request.POST, instance=projeto)
        passos, cores = formsets(projeto, request.POST)
        if all([form.is_valid(), passos.is_valid(), cores.is_valid()]):  # all([...]): valida os três
            form.save()
            passos.save()
            cores.save()
            messages.success(request, f"Projeto {projeto.nome} salvo.")
            return redirect("ui_projeto", projeto.pk)
        messages.error(request, "Nada foi gravado: corrija os erros marcados.")
    else:
        form = ProjetoForm(instance=projeto)
        passos, cores = formsets(projeto)
    _vestir(form, *passos.forms, *cores.forms, desabilitar=not pode)

    efetivas = cores_efetivas(projeto, projeto, MAX_CORES)  # mesma regra da revista (D-060)
    nomes = valores_das_variaveis(projeto)
    sobrescritas = {c.instance.padrao for c in cores.forms if c.instance.pk}
    contexto = {
        "projeto": projeto,
        "arquivado": arquivado,
        "pode_gravar": pode,
        "form": form,
        "tem_permissao": pode_gravar(request.user),
        "grupos": [(g, [(form[v.nome], v) for v in VARIAVEIS if v.grupo == g and not v.automatica]) for g in GRUPOS],
        "passos": passos,
        "cores": cores,
        "max_cores": MAX_CORES,
        "faixa": [
            {"padrao": k, "cor": efetivas[f"padrao-{k}"], "nome": nomes.get(f"pd{k:02d}", ""), "projeto": k in sobrescritas}
            for k in range(1, MAX_CORES + 1) if f"padrao-{k}" in efetivas
        ],
        "passos_matriz": MatrizEtapaCC.objects.filter(matriz_id=projeto.parceiro_ano.matriz_id)
        .select_related("etapa", "componente").order_by("etapa__ordem", "componente__codigo"),
        "ano": projeto.ano,
        "secao": "variaveis",
    }
    return TemplateResponse(request, "ui/projeto/projeto.html", contexto)


@require_GET
@login_required(login_url="admin:login")
@com_bloqueio(_alvo, pode_gravar)
def linha(request, pk, tipo):
    """Fragmento HTMX: uma linha nova de passo ou cor, no índice TOTAL_FORMS, e o contador atualizado."""
    if tipo not in ("passos", "cores"):
        raise Http404
    if not request.pode_gravar:
        raise PermissionDenied
    projeto = get_object_or_404(Projeto, pk=pk, arquivado_em__isnull=True)
    passos, cores = formsets(projeto)
    fs = passos if tipo == "passos" else cores
    total = request.GET.get(f"{tipo}-TOTAL_FORMS", "")
    i = int(total) if total.isascii() and total.isdigit() and len(total) < 4 else fs.total_form_count()
    nova = fs.empty_form
    nova.prefix = fs.add_prefix(i)
    if tipo == "cores":
        # Sugere o primeiro padrão ainda sem cor no form, já com a cor da paleta do ano.
        usados = {request.GET.get(f"cores-{n}-padrao", "") for n in range(i)}
        livre = next((k for k in range(1, MAX_CORES + 1) if str(k) not in usados), None)
        paleta = dict(CorPadrao.objects.filter(ano_id=projeto.ano_id).values_list("padrao", "cor"))
        nova.initial = {"padrao": livre, "cor": paleta.get(livre, "#000000")}
    _vestir(nova)
    contexto = {"projeto": projeto, "f": nova, "tipo": tipo, "total": i + 1, "cheio": tipo == "cores" and i + 1 >= MAX_CORES, "nova": True}
    return TemplateResponse(request, "ui/parciais/projeto_linha.html", contexto)


urlpatterns = [
    path("", inicio, name="ui_projeto_inicio"),
    path("ano/<int:ano>/", lista, name="ui_projeto_lista"),
    path("<int:pk>/", projeto, name="ui_projeto"),
    path("<int:pk>/linha/<str:tipo>/", linha, name="ui_projeto_linha"),
]
