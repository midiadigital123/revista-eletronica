"""Context processor do ano (U6): o ano da página, os links do seletor do cabeçalho e o ano da sessão.

`ano_ctx`: o `Ano` do kwarg `ano`, ou do objeto da página (detalhe sem ano na URL), ou da sessão,
ou o mais recente. `trocas_ano`: [(ano, url)] para cada ano. A mesma rota com o kwarg `ano` trocado
e a query string mantida; em detalhe (ou rota com outros kwargs), o equivalente do outro ano
(mesmo parceiro) ou a lista daquele ano. Nunca um link que dá 404.

Preguiçoso: só consulta o banco quando o template usa as variáveis (a base, não os fragmentos HTMX).
"""

from functools import cache

from django.db.models import F
from django.urls import reverse

from nucleo.models import Ano, Matriz, MatrizEtapaCC, Projeto, Revista, Template

# Detalhe sem `ano` na URL: de onde vem o ano do objeto da página.
OBJETO = {
    "ui_projeto": (Projeto, "ano__ano"),
    "ui_matriz_detalhe": (Matriz, "ano__ano"),
    "ui_matriz_mec": (MatrizEtapaCC, "matriz__ano__ano"),
    "ui_matriz_descritor": (MatrizEtapaCC, "matriz__ano__ano"),
    "ui_templates_editar": (Template, "ano__ano"),
}
# Prefixo da rota → lista do outro ano, quando a rota não serve para ele. O resto cai no Painel.
LISTA = {
    "ui_projeto": "ui_projeto_lista", "ui_revista": "ui_revista", "ui_matriz": "ui_matriz",
    "ui_templates": "ui_templates", "ui_variaveis": "ui_variaveis", "ui_impresso": "ui_impresso",
    "ui_lotes": "ui_lotes_matriz", "ui_validar": "ui_validar", "ui_ano": "ui_ano", "cortes": "cortes",
}  # fmt: skip


def ano_da_sessao(request):
    """Ano guardado pelo seletor (o último ano visto) ou, sem ele, o mais recente. Usado pelas rotas `_inicio`."""
    return Ano.objects.filter(ano=request.session.get("ano")).first() or Ano.objects.order_by("-ano").first()


def _lista(nome, ano):
    rota = next((LISTA[p] for p in sorted(LISTA, key=len, reverse=True) if nome.startswith(p)), "painel")
    return reverse(rota, args=[ano])


def _equivalentes(nome, kwargs):
    """{ano: url} dos equivalentes (mesmo parceiro). Arquivados vêm antes na consulta: no dict, o ativo vence."""
    if nome == "ui_projeto":
        p = Projeto.objects.filter(pk=kwargs["pk"]).values_list("parceiro_ano__parceiro", flat=True).first()
        achados = Projeto.objects.filter(parceiro_ano__parceiro=p).order_by(F("arquivado_em").desc(nulls_last=True))
        return {a: reverse("ui_projeto", args=[pk]) for a, pk in achados.values_list("ano__ano", "pk")}
    if nome == "ui_revista_editar":
        r = Revista.objects.filter(pk=kwargs["pk"]).values("projeto__parceiro_ano__parceiro", "componente__codigo").first()
        if not r:
            return {}
        achados = Revista.objects.filter(
            projeto__parceiro_ano__parceiro=r["projeto__parceiro_ano__parceiro"], componente__codigo=r["componente__codigo"]
        ).order_by(F("arquivada_em").desc(nulls_last=True))
        return {a: reverse("ui_revista_editar", args=[a, pk]) for a, pk in achados.values_list("ano__ano", "pk")}
    return {}


def _calcular(request):
    rm = request.resolver_match
    nome, kwargs = (rm.url_name or "", rm.kwargs) if rm else ("", {})
    por_ano = {a.ano: a for a in Ano.objects.order_by("-ano")}
    anos = list(por_ano)
    atual = kwargs.get("ano")
    if atual is None and nome in OBJETO:
        modelo, campo = OBJETO[nome]
        atual = modelo.objects.filter(pk=kwargs["pk"]).values_list(campo, flat=True).first()
    if atual in anos:
        if request.session.get("ano") != atual:
            request.session["ano"] = atual
    else:
        atual = request.session.get("ano") if request.session.get("ano") in anos else (anos[0] if anos else None)

    query = f"?{request.GET.urlencode()}" if request.GET else ""
    mesma_rota = request.method == "GET" and set(kwargs) == {"ano"}
    equivalentes = {} if mesma_rota else _equivalentes(nome, kwargs)
    trocas = [
        (a, reverse(nome, kwargs={"ano": a}) + query if mesma_rota else equivalentes.get(a) or _lista(nome, a))
        for a in anos
    ]
    return {"ano": por_ano.get(atual), "trocas": trocas, "mesma_rota": mesma_rota}


def ano_atual(request):
    calcular = cache(lambda: _calcular(request))
    return {
        "ano_ctx": lambda: calcular()["ano"],
        "trocas_ano": lambda: calcular()["trocas"],
        "trocas_mesma_rota": lambda: calcular()["mesma_rota"],  # o JS reaplica a query que o HTMX empurrou
    }
