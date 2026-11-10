"""Pendências: o que bloqueia o "Validado" (D-112, D-116, D-125), por fascículo (D-252).

Lê a revista resolvida (`servicos/resolver.py`); o resolver não importa este módulo.
"""

from typing import NamedTuple

from nucleo.models import Corte, MatrizEtapaCC
from nucleo.servicos.f2 import texto_puro
from nucleo.servicos.resolver import resolver


class Pendencia(NamedTuple):
    codigo: str
    mensagem: str
    # ponytail: link nulo até existirem as telas (S11/S12); o painel monta o link pelo código.
    link: str | None = None


def problema_dos_cortes(dados):
    """Espelho do problemaDaEtapa do JS (D-131): cortes estritamente crescentes em (min, max).
    Defensivo: a cascata já recusa (D-153), mas o dado pode ter entrado por outro caminho."""
    anterior, maximo = dados["scaleRange"]["min"], dados["scaleRange"]["max"]
    for i in range(1, len(dados["cortes"]) + 1):
        v = dados["cortes"].get(f"padrao-{i}")
        if v is None or not anterior < v < maximo:
            return True
        anterior = v
    return False


def pendencias_f1(revista, resolvido):
    """Matriz, cortes e templates (o template do F2 também: vem das lacunas)."""
    pa = revista.projeto.parceiro_ano
    saida = []
    if pa.matriz_id is None:
        saida.append(Pendencia("matriz", "Falta escolher a matriz do parceiro no ano."))
    else:
        com_mec = set(
            MatrizEtapaCC.objects.filter(matriz_id=pa.matriz_id, componente_id=revista.componente_id)
            .values_list("etapa_id", flat=True)
        )
        sem_mec = [
            c.etapa.codigo
            for c in Corte.objects.filter(parceiro_ano=pa, componente_id=revista.componente_id)
            .select_related("etapa")
            .order_by("etapa__ordem")
            if c.etapa_id not in com_mec
        ]
        if sem_mec:
            saida.append(Pendencia("corte_sem_matriz", f"A matriz não tem a etapa: {', '.join(sem_mec)}."))
    dados = resolvido["f1"]["dados"]
    invalidas = [e.upper() for e in resolvido["f1"]["etapas"] if problema_dos_cortes(dados[e])]
    if invalidas:
        saida.append(
            Pendencia("corte_invalido", f"Cortes fora de ordem ou da escala: {', '.join(invalidas)}.")
        )
    for lacuna in resolvido["lacunas"]:
        if lacuna["tipo"] == "template":
            saida.append(
                Pendencia(f"template_{lacuna['fasciculo'].lower()}", f"Falta escolher o template do {lacuna['fasciculo']}.")
            )
    return saida


def pendencias_f2(resolvido):
    """Os infográficos ativos: o que falta para o svg-tour não abrir modal vazio."""
    saida = []
    for inf in resolvido["f2"].get("infograficos", []):  # foto antiga (arquivada) não tem a chave
        passos, etapas, faltas = inf["passos"], inf["etapas"], []
        if not inf["habilidade"].strip():
            faltas.append("falta a habilidade destacada.")
        if "habilidades" in passos and not any(e["codigo"].strip() or e["texto"].strip() for e in etapas):
            faltas.append("o passo Habilidades está ligado e nenhuma etapa tem código ou texto.")
        if "progressao" in passos and sum(bool(e["marca"]) for e in etapas) < 2:
            faltas.append("o passo Progressão precisa de pelo menos 2 etapas com marca.")
        faltas += [  # sem o texto, o + abriria um modal só com o título (D-250)
            f"o passo {rotulo} está ligado e falta o texto do clique."
            for p, rotulo in (("habilidades", "Habilidades"), ("progressao", "Progressão"))
            if p in passos and not texto_puro(inf["textos"][p])
        ]
        if "tarefas" in passos and sum(bool(i["imagem"]) for i in inf["itens"]) < 4:  # posições 1 a 4, únicas
            faltas.append("o passo Tarefas precisa dos 4 itens com imagem.")
        saida += [Pendencia("infografico", f"{inf['titulo']}: {f}") for f in faltas]
    return saida


def pendencias(revista, resolvido=None):
    """Lista vazia = pode validar. Ordem fixa (telas e testes dependem): F1, F2, capa, variáveis, nome.
    `resolvido`: reaproveita um já montado (o painel monta uma vez para pendências e hash)."""
    if resolvido is None:
        resolvido = resolver(revista)
    saida = pendencias_f1(revista, resolvido) + pendencias_f2(resolvido)
    if not revista.capa:
        saida.append(Pendencia("capa", "Falta a imagem de capa."))
    vazias = [lacuna["nome"] for lacuna in resolvido["lacunas"] if lacuna["tipo"] == "variavel"]
    if vazias:
        saida.append(Pendencia("variaveis", f"Variáveis sem valor: {', '.join(vazias)}."))
    if revista.projeto.nome.endswith(" - NOME DO PROJETO"):  # nome inicial da cascata (D-065)
        saida.append(Pendencia("nome_projeto", "Troque o nome padrão do projeto."))
    return saida
