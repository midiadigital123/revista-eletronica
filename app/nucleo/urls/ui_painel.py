"""Painel da temporada B (T23): /painel/<ano>/, rota `painel` (substituiu o painel no estilo do admin). Convenções: docs/telas/design-system.md.

Mesma regra do painel do admin (`urls/painel.py`: `filtrar`, `linha`, `COLUNAS`); só a casca muda.
Login (vai ao login do admin) e `view_revista` (403), como o painel atual. Não grava nada: a
validação em lote é a tela T24 (`ui_validar`).
Pedido HTMX (troca de filtro) devolve só o corpo (`parciais/painel_corpo.html`).
As linhas vêm agrupadas por projeto (um ativo por parceiro no ano), na ordem de `revistas_do_ano`
(parceiro, componente); "N de M completas" conta o recorte antes do filtro de falta.
"""


from django.shortcuts import get_object_or_404
from django.urls import path
from django.utils.http import urlencode

from nucleo.models import Ano
from nucleo.ui_bloqueio import pagina_ou_parcial
from nucleo.urls.painel import COLUNAS, filtrar
from nucleo.urls.preview import protegida


def completa(linha):
    return all(c["ok"] for c in linha["faltas"].values())


def agrupar(linhas, todas):
    """Um grupo por projeto, na ordem da primeira revista (dict guarda a ordem de inserção)."""
    grupos, contagem = {}, {}
    for x in todas:
        contagem.setdefault(x["revista"].projeto_id, []).append(completa(x))
    for x in linhas:
        p = x["revista"].projeto
        g = grupos.setdefault(p.pk, {"projeto": p, "parceiro": p.parceiro_ano.parceiro, "linhas": []})
        g["linhas"].append(x)
    for k, g in grupos.items():
        g["completas"], g["total"] = sum(contagem[k]), len(contagem[k])
    return list(grupos.values())


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
    sem_falta = "?" + urlencode(recorte) if recorte else request.path
    ctx = {
        **f,
        "ano": ano,
        "anos": Ano.objects.order_by("-ano"),
        "secao": "painel",
        "colunas": colunas,
        "grupos": agrupar(f["linhas"], f["todas"]),
        "completas": sum(map(completa, f["todas"])),
        "sem_falta": sem_falta,
        "sem_template": "?" + urlencode({k: v for k, v in {"falta": f["falta"], "parceiro": recorte.get("parceiro")}.items() if v}),
        "filtrado": bool(f["falta"] or recorte),
        # Estado vazio com filtro: o que significa e como sair dele.
        "vazio_texto": (
            f"Nenhuma revista deste recorte está sem {COLUNAS[f['falta']][0]}: a coluna está em dia. Limpe o filtro para ver todas."
            if f["falta"]
            else "Este recorte ainda não tem revistas ativas. Lance os cortes do parceiro para criar as revistas, ou limpe os filtros."
        ),
        "vazio_url": sem_falta if f["falta"] else request.path,
        "pode_validar": request.user.has_perm("nucleo.validar_revista"),
    }
    return pagina_ou_parcial(request, "ui/painel/painel.html", "ui/parciais/painel_corpo.html", ctx)


urlpatterns = [
    path("<int:ano>/", painel, name="painel"),
]
