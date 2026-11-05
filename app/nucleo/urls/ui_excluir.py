"""Excluir o que não está em uso (D-205): /ui/excluir/<modelo>/<pk>/, rota `ui_excluir`.

Uma página para todas as entidades do `REGISTRO`. Exige `nucleo.delete_<modelo>` (403 até no GET, como
o excluir da matriz, D-181). Livre: confirmação forte com o código ou o nome digitado (`ExcluirForm`).
Em uso: lista o que impede (contagem e até 5 links) e não apaga. Ano: a página lista o que sai junto
(`resumo_ano`) e o Admin, só ele, apaga o ano inteiro digitando o ano (D-206). Para o ano, o `<pk>` é o
próprio ano (2027), não o id.

Parceiro em uso oferece "Desativar"/"Reativar" (D-208), num POST para `ui_parceiro_ativo`.
`?voltar=` (só deste site) é o "Voltar sem excluir" e o destino depois de excluir.
Projeto e Revista ficam fora: arquiva (D-205). Usuário tem rota própria em `ui_usuarios` (D-218), com
este mesmo template e a regra de rastro de `nucleo/usuarios.py`.
"""

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_http_methods, require_POST

from nucleo.matriz import ExcluirForm
from nucleo.models import Ano, Componente, Etapa, Matriz, Parceiro, Template
from nucleo.servicos import exclusao


def _ano(o):
    return o.ano.ano


# modelo → (classe, campo da URL, artigo + nome, o que se digita, seção do menu, destino padrão)
REGISTRO = {
    "ano": (Ano, "ano", lambda o: f"o ano {o.ano}", lambda o: str(o.ano), "anos", lambda o: reverse("ui_anos")),
    "parceiro": (Parceiro, "pk", lambda o: f"o parceiro {o.nome}", lambda o: o.nome.strip(), "projetos", lambda o: reverse("inicio")),
    "etapa": (Etapa, "pk", lambda o: f"a etapa {o.codigo} de {o.ano}", lambda o: o.codigo.strip(), "anos", lambda o: reverse("ui_ano", args=[_ano(o)])),
    "componente": (Componente, "pk", lambda o: f"o componente {o.codigo} de {o.ano}", lambda o: o.codigo.strip(), "anos", lambda o: reverse("ui_ano", args=[_ano(o)])),
    "matriz": (Matriz, "pk", lambda o: f"a matriz {o.nome} de {o.ano}", lambda o: o.nome.strip(), "matrizes", lambda o: reverse("ui_matriz", args=[_ano(o)])),
    "template": (Template, "pk", lambda o: f"o template {o.nome} ({o.componente.codigo} {o.fasciculo}) de {o.ano}", lambda o: o.nome.strip(), "templates", lambda o: reverse("ui_templates", args=[_ano(o)])),
}  # fmt: skip

# O que fazer quando está em uso.
DICA = {
    "parceiro": "Para excluir, limpe os cortes do parceiro em todos os anos: o projeto é arquivado. Se ele saiu do programa, desative.",
    "etapa": "Para excluir, tire os cortes, as matrizes e os passos de projeto desta etapa.",
    "componente": "Para excluir, tire os cortes, as matrizes e os templates deste componente: as revistas são arquivadas com os cortes.",
    "matriz": "Para excluir, troque a matriz dos parceiros na aba Lotes. Se alguém está editando, espere a pessoa sair.",
    "template": "Para excluir, troque o template das revistas que o usam. Se alguém está editando, espere a pessoa sair.",
}


def _voltar(request):
    url = request.GET.get("voltar", "")
    seguro = url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}, require_https=request.is_secure())
    return url if seguro else None


@require_http_methods(["GET", "POST"])
@login_required
def excluir(request, modelo, pk):
    if modelo not in REGISTRO:
        raise Http404
    classe, campo, nome, codigo, secao, padrao = REGISTRO[modelo]
    if not request.user.has_perm(f"nucleo.delete_{modelo}"):
        raise PermissionDenied
    obj = get_object_or_404(classe, **{campo: pk})
    voltar = _voltar(request)
    form = ExcluirForm(request.POST or None, codigo=codigo(obj))
    form.fields["confirmacao"].widget.attrs["class"] = "input"
    e_ano = classe is Ano
    impedimentos = [] if e_ano else exclusao.impedimentos(obj, request.user)
    titulo = nome(obj)  # antes de excluir: o objeto some
    if request.method == "POST" and not impedimentos and form.is_valid():
        destino = voltar or padrao(obj)
        try:
            exclusao.apagar_ano(obj, request.user) if e_ano else exclusao.excluir(obj, request.user)
        except exclusao.EmUso as e:
            impedimentos = e.impedimentos or [exclusao.Impedimento("dados novos que usam isto", 1, [])]
            messages.error(request, f"Nada foi excluído: alguém passou a usar {titulo} enquanto a página estava aberta.")
        else:
            messages.success(request, f"Ano {obj.ano} apagado, com tudo o que era dele." if e_ano else f"Exclusão feita: {titulo}.")
            return redirect(destino)
    contexto = {
        "obj": obj, "modelo": modelo, "titulo": titulo, "form": form, "codigo": codigo(obj),
        "voltar": voltar or padrao(obj), "impedimentos": impedimentos, "dica": DICA.get(modelo),
        "resumo": [(r, n) for r, n in exclusao.resumo_ano(obj) if n] if e_ano else None,
        "pode_desativar": modelo == "parceiro" and request.user.has_perm("nucleo.change_parceiro"),
        "voltar_query": request.GET.get("voltar", "") if voltar else "", "secao": secao,
    }  # fmt: skip
    return TemplateResponse(request, "ui/excluir.html", contexto)


@require_POST
@login_required
@permission_required("nucleo.change_parceiro", raise_exception=True)
def parceiro_ativo(request, pk):
    """D-208: desativar (ou reativar) o parceiro em uso. Desativado some da grade dos anos sem dados dele."""
    parceiro = get_object_or_404(Parceiro, pk=pk)
    acao = request.POST.get("acao")
    if acao == "desativar":
        exclusao.desativar_parceiro(parceiro, request.user)
        messages.success(request, f"Parceiro {parceiro.nome} desativado: sai da grade dos anos em que não tem cortes.")
    elif acao == "reativar":
        exclusao.reativar_parceiro(parceiro, request.user)
        messages.success(request, f"Parceiro {parceiro.nome} reativado.")
    else:
        raise Http404
    return redirect(_voltar(request) or reverse("ui_excluir", args=["parceiro", parceiro.pk]))


urlpatterns = [
    path("<str:modelo>/<int:pk>/", excluir, name="ui_excluir"),
    path("parceiro/<int:pk>/ativo/", parceiro_ativo, name="ui_parceiro_ativo"),
]
