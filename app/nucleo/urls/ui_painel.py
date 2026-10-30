"""Painel da temporada B (T23): /painel/<ano>/, rota `painel` (substituiu o painel no estilo do admin). Convenções: docs/telas/design-system.md.

Mesma regra do painel do admin (`urls/painel.py`: `filtrar`, `linha`, `COLUNAS`); só a casca muda.
Login (vai ao login do admin) e `view_revista` (403), como o painel atual. Não grava nada: a
validação em lote é a tela T24 (`ui_validar`).
Pedido HTMX (troca de filtro) devolve só o corpo (`parciais/painel_corpo.html`).
"""

from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.http import urlencode

from nucleo.models import Ano
from nucleo.ui_bloqueio import pagina_ou_parcial
from nucleo.urls.painel import COLUNAS, filtrar
from nucleo.urls.preview import protegida


@protegida
def painel(request, ano):
    ano = get_object_or_404(Ano, ano=ano)
    f = filtrar(ano, request.GET)
    recorte = {k: v.pk for k in ("parceiro", "template") if (v := f[k]) is not None}  # o que a falta preserva
    colunas = [
        {
            "chave": chave,
            "rotulo": rotulo,
            "faltam": sum(not x["faltas"][chave]["ok"] for x in f["todas"]),
            "url": "?" + urlencode({**recorte, "falta": chave}),
        }
        for chave, (rotulo, _) in COLUNAS.items()
    ]
    faltam = {c["chave"]: c["faltam"] for c in colunas}
    ctx = {
        **f,
        "ano": ano,
        "anos": Ano.objects.order_by("-ano"),
        "secao": "painel",
        "colunas": colunas,
        "faltam": faltam,
        "url_falta": {c["chave"]: c["url"] for c in colunas},
        "completas": sum(all(c["ok"] for c in x["faltas"].values()) for x in f["todas"]),
        "sem_falta": "?" + urlencode(recorte),
        "sem_template": "?" + urlencode({k: v for k, v in {"falta": f["falta"], "parceiro": recorte.get("parceiro")}.items() if v}),
        "filtrado": bool(f["falta"] or recorte),
        "pode_validar": request.user.has_perm("nucleo.validar_revista"),
    }
    return pagina_ou_parcial(request, "ui/painel/painel.html", "ui/parciais/painel_corpo.html", ctx)


urlpatterns = [
    path("<int:ano>/", painel, name="painel"),
]
