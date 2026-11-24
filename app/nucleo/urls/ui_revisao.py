"""Revisar mudanças da base (D-292): /ui/revisao/<pk>/, rota ui_revisao. A etapa do projeto contra a base
dela, célula a célula; a regra é de `servicos/etapa_projeto.py` (`revisao`, `concluir`, D-284). O bloqueio é
o da própria etapa do projeto, o mesmo do editor da cópia (`ui_matriz`): os dois se excluem."""

import re
from pathlib import PurePosixPath

from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import path
from django.views.decorators.http import require_GET, require_http_methods

from nucleo.servicos.etapa_projeto import CAMPOS_TEXTO, pendente, revisao, textos_locais
from nucleo.texto import partes
from nucleo.ui_bloqueio import com_bloqueio
from nucleo.urls.preview import TIPOS_ITEM, servir
from nucleo.urls.ui_matriz import DescritorUiForm, _congelada, _contexto_ano, _dono, _mec, pode_editar

ROTULOS = {
    **DescritorUiForm.Meta.labels, "prerequisitos": "Pré-requisitos", "passo": "Intervalo mínimo",
    "texto": "Texto", "texto_alternativo": "Texto alternativo", "arquivo": "Imagem",
}  # fmt: skip
# ponytail: a chave de tarefa é reconhecida pelo formato; um descritor de código "X/100-150#1" ganharia
# título de tarefa (só o título: a escolha viaja pela chave inteira). Devolver o par no Item se acontecer.
TAREFA = re.compile(r"(.+)/(\d+)-(\d+)#(\d+)")
LADOS = (("local", "No projeto"), ("base", "Na base agora"), ("antes", "Como era quando o projeto copiou"))
MANTER_OU_BASE = [("local", "Manter o do projeto"), ("base", "Usar o da base")]


def _etapa(request, pk):
    """A etapa do projeto com base: a da matriz e a cópia solta (a base saiu) não têm revisão."""
    m = _mec(request, pk)
    if m.projeto_id is None or m.base_id is None:
        raise Http404
    return m


def _alvo_revisao(request, pk, **kwargs):
    """Alvo do `com_bloqueio`: o 404 vem antes de travar (a Comunitária não trava num GET daqui)."""
    m = _etapa(request, pk)
    return None if _congelada(m) else m


def _onde(chave):
    """("D01", "tarefa 100–150") da chave; a tarefa é "" na chave de descritor."""
    m = TAREFA.fullmatch(chave)
    if m is None:
        return chave, ""
    codigo, inicio, fim, n = m.groups()
    return codigo, f"tarefa {inicio}–{fim}" + (f" ({n}ª)" if n != "1" else "")


def _lado(nome, titulo, valor, campo, tarefa):
    """Um dos três lados de uma célula, pronto para o template; `caminho` (do storage) nunca vai à página."""
    lado = {"nome": nome, "titulo": titulo, "texto": "", "nota": "", "caminho": None, "vazio": "Vazio."}
    if campo == "existe":
        lado["vazio"] = "Não existe."
        if valor is not None:
            lado["texto"] = valor["texto" if tarefa else "descricao"]
            lado["caminho"] = valor.get("arquivo")
            lado["nota"] = "" if tarefa else f"{len(valor['tarefas'])} tarefa(s)"
    elif campo == "arquivo":
        lado["caminho"], lado["vazio"] = valor, "Sem imagem."
    elif campo == "prerequisitos":
        lado["texto"] = "\n".join(valor)
    elif campo == "passo":
        lado["texto"] = "Sem linhas vazias" if valor is None else str(valor)
    else:
        lado["texto"] = valor
    lado["imagem"] = PurePosixPath(lado["caminho"] or "").suffix in (".png", ".jpg")
    lado["partes"] = [("igual", lado["texto"])]
    return lado


def _existe(item, tarefa):
    """(nota, opções) do descritor ou da tarefa inteira."""
    o_que = "esta tarefa" if tarefa else "este descritor"
    if item.local is None:
        opcoes = [("base", "Trazer para o projeto"), ("local", "Não trazer")]
    elif item.base is None:
        opcoes = [("base", "Apagar também"), ("local", "Manter")]
    else:
        opcoes = MANTER_OU_BASE
    if item.base is None:
        return f"A base apagou {o_que}.", opcoes
    if item.antes is None:
        return f"A base criou {o_que}.", opcoes
    return f"A base mudou {o_que}, que o projeto apagou.", opcoes


def cartoes(itens, textos):
    """Os cartões da tela, na ordem dos itens: um por célula, e a `ordem` agrupada (um cartão para a dos
    descritores, um por descritor para a das tarefas). A escolha do cartão vale para todas as `celulas`
    dele; `i` é o índice que nomeia os campos do form (`escolha-<i>`, `texto-<i>`)."""
    saida, grupos = [], {}
    for item in itens:
        codigo, tarefa = _onde(item.chave)
        if item.campo == "ordem":
            grupo = grupos.get(codigo if tarefa else "")
            if grupo is None:
                grupo = grupos[codigo if tarefa else ""] = {
                    "titulo": f"{codigo} · a ordem das tarefas mudou na base" if tarefa else "A ordem dos descritores mudou na base",
                    "nota": "Não muda a revista." if tarefa else "",
                    "opcoes": [("base", "Usar a ordem da base"), ("local", "Manter a ordem do projeto")],
                    "decisao": False, "editavel": False, "itens": [],
                }  # fmt: skip
                saida.append(grupo)
            grupo["itens"].append((tarefa.removeprefix("tarefa ") or codigo, item))
            grupo["decisao"] = grupo["decisao"] or item.situacao == "conflito"
            continue
        cartao = {
            "titulo": " · ".join(p for p in (codigo if item.campo != "passo" else "", tarefa, ROTULOS.get(item.campo, "")) if p),
            "nota": "", "opcoes": MANTER_OU_BASE, "decisao": item.situacao == "conflito",
            "editavel": item.campo in CAMPOS_TEXTO, "texto": textos.get((item.chave, item.campo), ""),
            "celulas": [(item.chave, item.campo)],
            "lados": [_lado(nome, titulo, getattr(item, nome), item.campo, tarefa) for nome, titulo in LADOS],
        }  # fmt: skip
        if item.campo == "existe":
            cartao["titulo"] += "" if tarefa else " · descritor"
            cartao["nota"], cartao["opcoes"] = _existe(item, tarefa)
        elif cartao["editavel"]:
            cartao["opcoes"] = [*MANTER_OU_BASE, ("texto", "Escrever outro texto")]
            cartao["lados"][1]["partes"] = partes(item.antes, item.base)
        saida.append(cartao)
    for i, cartao in enumerate(saida):
        grupo = cartao.pop("itens", None)
        if grupo is not None:
            # ponytail: só os que mudaram de lugar aparecem; listar a etapa inteira se a lista curta confundir.
            cartao["celulas"] = [(item.chave, "ordem") for _, item in grupo]
            cartao["lados"] = [
                _lado(nome, titulo, ", ".join(n for n, _ in sorted(grupo, key=lambda g: getattr(g[1], nome))), "ordem", "")
                for nome, titulo in LADOS
            ]
        antes = cartao["lados"][2]
        antes["falta"] = bool(antes["caminho"]) and not default_storage.exists(antes["caminho"])
        cartao.update(i=i, marcada="" if cartao["decisao"] else "base", antes=antes, colunas=cartao["lados"][:2])
    return saida


@require_http_methods(["GET"])  # o POST (concluir) entra no próximo passo da D-292
@login_required
@com_bloqueio(_alvo_revisao, pode_editar)
def revisar(request, pk):
    m = _etapa(request, pk)  # leitura nova: `revisao` usa a base em cache da instância
    itens, visto = revisao(m)
    lista = cartoes(itens, textos_locais(m, itens))
    so_leitura = ""
    if not pode_editar(request.user):
        so_leitura = "Só leitura: seu perfil vê a revisão, mas não conclui. Para concluir, peça a permissão de matriz a um administrador."
    elif _congelada(m):
        so_leitura = "Só leitura: o projeto desta etapa está arquivado."
    return TemplateResponse(request, "ui/projeto/revisar_etapa.html", {
        **_contexto_ano(m.ano), **_dono(m), "secao": "projetos", "mec": m, "codigo": f"{m.etapa.codigo} {m.componente.codigo}",
        "pendente": pendente(m), "visto": visto, "cartoes": lista, "so_leitura": so_leitura,
        "decisoes": [c for c in lista if c["decisao"]], "entram": [c for c in lista if not c["decisao"]],
        "pode_gravar": request.pode_gravar,
    })  # fmt: skip


@require_GET
@login_required
def arquivo(request, pk, i, lado):
    """A imagem de um lado do cartão `i`: só leitura, fora do bloqueio (como `item_baixar`). O caminho sai
    da revisão de agora, nunca da URL; qualquer falta é 404."""
    lista = cartoes(revisao(_etapa(request, pk))[0], {})
    caminho = next((l["caminho"] for l in lista[i]["lados"] if l["nome"] == lado), None) if i < len(lista) else None
    tipo = TIPOS_ITEM.get(PurePosixPath(caminho or "").suffix)
    if tipo is None:
        raise Http404
    try:
        # sandbox no PDF impede o visualizador do Chrome (preview.servir): o PDF baixa, a imagem abre no <img>.
        return servir(default_storage.open(caminho), tipo, as_attachment=tipo == "application/pdf")
    except FileNotFoundError:
        raise Http404 from None


urlpatterns = [
    path("<int:pk>/", revisar, name="ui_revisao"),
    path("<int:pk>/arquivo/<int:i>/<slug:lado>/", arquivo, name="ui_revisao_arquivo"),
]
