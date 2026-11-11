"""Exclusão só do que não está em uso (D-205), o ano inteiro (D-206) e o template com as versões (D-207).

O PROTECT continua no banco: `impedimentos` pergunta ao `Collector` do Django o que impede, objeto por
objeto e parte por parte (o PROTECT não desconta o que já está sendo coletado), e `excluir` confere de
novo com a linha travada. "Partes" (`PARTES`) saem junto e não contam como uso. Bloqueio de outra pessoa
(na MEC da matriz ou no template) também impede.

A `TemplateVersao` só aceita DELETE com a chave `revista.apagar_versoes` ligada na transação (migração
0017); só `excluir(template)` e `apagar_ano` a ligam, e a desligam antes de sair.

Parceiro em uso pode ser desativado (D-208): `desativar_parceiro`, `reativar_parceiro` e
`parceiros_do_ano` (ativos e os desativados com dados no ano).

Quem chama confere a permissão (`delete_<modelo>`; `delete_ano` só no Admin), como no `abrir_ano`.
"""

from collections import defaultdict
from contextlib import contextmanager
from typing import NamedTuple

from django.db import IntegrityError, connection, transaction
from django.db.models import Exists, OuterRef, Q
from django.db.models.deletion import Collector, ProtectedError, RestrictedError
from django.db.models.functions import Now
from django.urls import reverse
from django.utils import timezone

from nucleo.models import (
    Ano, Bloqueio, Componente, CorPadrao, Corte, Descritor, Etapa, FotoRevista, Matriz, MatrizEtapaCC, Parceiro,
    ParceiroAno, Projeto, ProjetoCor, ProjetoPasso, Revista, RevistaFasciculo, RevistaInfografico,
    RevistaSecao, Tarefa, Template, TemplateVersao,
)  # fmt: skip

PARTES = {Parceiro: ["parceiroano_set"], Matriz: ["matrizetapacc_set"], Template: ["templateversao_set"]}
LINKS = 5
EM_EDICAO = "em edição por outra pessoa"


class Impedimento(NamedTuple):
    rotulo: str  # plural: "revistas"
    contagem: int
    links: list  # até LINKS pares (texto, url)


class EmUso(Exception):
    def __init__(self, impedimentos):
        super().__init__("em uso")
        self.impedimentos = impedimentos


# Quem impede → (rótulo, modelo mostrado, caminho até ele). Fascículo, seção e infográfico contam como a revista.
GRUPO = {
    Corte: ("cortes", Corte, "pk"),
    Projeto: ("projetos", Projeto, "pk"),
    ProjetoPasso: ("projetos com passo próprio", Projeto, "projeto_id"),
    Revista: ("revistas", Revista, "pk"),
    RevistaFasciculo: ("revistas", Revista, "revista_id"),
    RevistaSecao: ("revistas", Revista, "revista_fasciculo__revista_id"),
    RevistaInfografico: ("revistas", Revista, "revista_id"),
    ParceiroAno: ("parceiros que usam a matriz", ParceiroAno, "pk"),
    MatrizEtapaCC: ("etapas × componente de matriz", MatrizEtapaCC, "pk"),
    Template: ("templates", Template, "pk"),
}
# Modelo mostrado → (select_related, texto, url).
MOSTRAR = {
    Corte: (
        ("parceiro_ano__parceiro", "etapa", "componente", "ano"),
        lambda o: f"{o.parceiro_ano.parceiro} · {o.etapa.codigo} {o.componente.codigo} ({o.ano})",
        lambda o: reverse("cortes", args=[o.ano.ano]),
    ),
    Projeto: (("ano",), lambda o: f"{o} ({o.ano})", lambda o: reverse("ui_projeto", args=[o.pk])),
    Revista: (
        ("projeto", "componente", "ano"), lambda o: f"{o} ({o.ano})",
        lambda o: reverse("ui_revista_editar", args=[o.ano.ano, o.pk]),
    ),  # fmt: skip
    ParceiroAno: (("parceiro", "ano"), str, lambda o: reverse("ui_lotes_matriz", args=[o.ano.ano])),
    MatrizEtapaCC: (
        ("matriz__ano", "etapa", "componente"), str, lambda o: reverse("ui_matriz_mec", args=[o.pk]),
    ),  # fmt: skip
    Template: (
        ("ano", "componente"), lambda o: f"{o.nome} {o.componente.codigo} {o.fasciculo} ({o.ano})",
        lambda o: reverse("ui_templates_editar", args=[o.pk]),
    ),  # fmt: skip
}


def _protegidos(objs):
    """O que o PROTECT (ou RESTRICT) do Django recusa ao apagar `objs`."""
    if not objs:
        return []
    try:
        Collector(using=connection.alias, origin=objs[0]).collect(objs)
    except ProtectedError as e:
        return list(e.protected_objects)
    except RestrictedError as e:
        return list(e.restricted_objects)
    return []


def _agrupar(objs):
    pks = defaultdict(set)
    for o in objs:
        pks[type(o)].add(o.pk)
    grupos = defaultdict(set)  # (rótulo, modelo mostrado) → pks
    outros = []
    for modelo, ids in pks.items():
        if modelo not in GRUPO:  # FK nova sem rótulo: aparece pelo nome do modelo
            outros.append(Impedimento(str(modelo._meta.verbose_name_plural), len(ids), []))
            continue
        rotulo, alvo, caminho = GRUPO[modelo]
        destino = ids if caminho == "pk" else modelo.objects.filter(pk__in=ids).values_list(caminho, flat=True)
        grupos[rotulo, alvo] |= set(destino)
    saida = []
    for (rotulo, alvo), ids in grupos.items():
        relacionados, texto, url = MOSTRAR[alvo]
        primeiros = alvo.objects.filter(pk__in=ids).select_related(*relacionados).order_by("pk")[:LINKS]
        saida.append(Impedimento(rotulo, len(ids), [(texto(o), url(o)) for o in primeiros]))
    return saida + outros


def _em_edicao(obj, usuario):
    """Bloqueio válido de outra pessoa na MEC da matriz ou no template."""
    if isinstance(obj, Matriz):
        filtro, url = {"matriz_etapa_cc__matriz": obj}, lambda b: reverse("ui_matriz_mec", args=[b.matriz_etapa_cc_id])
    elif isinstance(obj, Template):
        filtro, url = {"template": obj}, lambda b: reverse("ui_templates_editar", args=[b.template_id])
    else:
        return []
    travas = Bloqueio.objects.filter(**filtro, expira_em__gte=Now()).select_related("usuario")
    if usuario is not None:
        travas = travas.exclude(usuario=usuario)
    travas = list(travas.order_by("pk"))
    if not travas:
        return []
    return [Impedimento(EM_EDICAO, len(travas), [(f"aberto por {b.usuario}", url(b)) for b in travas[:LINKS]])]


def impedimentos(obj, usuario=None):
    """[Impedimento] do que impede excluir `obj` (vazio = livre). `usuario`: o próprio bloqueio não impede."""
    modelos_partes = {getattr(obj, p).model for p in PARTES.get(type(obj), ())}
    achados = [o for o in _protegidos([obj]) if type(o) not in modelos_partes]
    for parte in PARTES.get(type(obj), ()):
        achados += _protegidos(list(getattr(obj, parte).all()))
    return _agrupar(achados) + _em_edicao(obj, usuario)


def _apagar(qs, usuario):
    """Apaga `qs` (e o que vem em CASCADE) com o autor no histórico de cada linha."""
    coletor = Collector(using=qs.db, origin=qs)
    coletor.collect(qs)
    for objs in coletor.data.values():
        for o in objs:
            o._history_user = usuario
    coletor.delete()


def _sql(comando):
    with connection.cursor() as c:
        c.execute(comando)


@contextmanager
def _versoes_apagaveis(ligar=True):
    """Liga a chave do trigger da TemplateVersao só no bloco. Com erro, o rollback a desfaz."""
    if not ligar:
        yield
        return
    _sql("SET LOCAL revista.apagar_versoes = 'on'")
    yield
    _sql("SET LOCAL revista.apagar_versoes = 'off'")


def excluir(obj, usuario):
    """Exclui `obj` livre, com as partes (PARTES). Em uso, ou se algo passou a usá-lo, levanta EmUso."""
    modelo = type(obj)
    with transaction.atomic():
        obj = modelo.objects.select_for_update().get(pk=obj.pk)
        if achados := impedimentos(obj, usuario):
            raise EmUso(achados)
        try:
            with transaction.atomic(), _versoes_apagaveis(modelo is Template):
                for parte in PARTES.get(modelo, ()):
                    _apagar(getattr(obj, parte).all(), usuario)
                obj._history_user = usuario
                obj.delete()
                # As FKs do Django são DEFERRED: sem isto, a corrida só estouraria no commit, fora daqui.
                _sql("SET CONSTRAINTS ALL IMMEDIATE")
        except (IntegrityError, ProtectedError, RestrictedError) as e:
            erro = e
        else:
            erro = None
        finally:
            _sql("SET CONSTRAINTS ALL DEFERRED")  # volta ao padrão das FKs do Django
        if erro is not None:
            raise EmUso(impedimentos(obj, usuario)) from erro


# --- Ano inteiro (D-206) -----------------------------------------------------------------------

# Ordem das dependências (folhas primeiro). Fascículos, seções e infográficos saem com a revista; descritores e
# tarefas com a MEC; bloqueios com o alvo (CASCADE).
ORDEM_ANO = (
    (FotoRevista, "revista__ano"), (Revista, "ano"),
    (ProjetoPasso, "ano"), (ProjetoCor, "projeto__ano"), (Projeto, "ano"),
    (Corte, "ano"), (ParceiroAno, "ano"),
    (MatrizEtapaCC, "ano"), (Matriz, "ano"),
    (TemplateVersao, "template__ano"), (Template, "ano"),
    (CorPadrao, "ano"), (Componente, "ano"), (Etapa, "ano"),
)  # fmt: skip

RESUMO = (
    ("projetos", Projeto, "ano"), ("revistas", Revista, "ano"), ("fotos de revista", FotoRevista, "revista__ano"),
    ("cortes", Corte, "ano"), ("parceiros no ano", ParceiroAno, "ano"), ("matrizes", Matriz, "ano"),
    ("descritores", Descritor, "matriz_etapa_cc__ano"), ("tarefas", Tarefa, "descritor__matriz_etapa_cc__ano"),
    ("templates", Template, "ano"), ("versões de template", TemplateVersao, "template__ano"),
    ("etapas", Etapa, "ano"), ("componentes", Componente, "ano"),
)  # fmt: skip


def resumo_ano(ano):
    """[(rótulo, contagem)] do que sai junto com o ano, para a página de confirmação."""
    return [(rotulo, modelo.objects.filter(**{campo: ano}).count()) for rotulo, modelo, campo in RESUMO]


def apagar_ano(ano, usuario):
    """Apaga o ano e tudo dele numa transação. Parceiros e usuários ficam (são de todos os anos).

    ponytail: os arquivos no storage (capa, SVG, item, imagem de infográfico) ficam; o item é compartilhado entre anos (D-150).
    """
    with transaction.atomic(), _versoes_apagaveis():
        ano = Ano.objects.select_for_update().get(pk=ano.pk)
        for modelo, campo in ORDEM_ANO:
            _apagar(modelo.objects.filter(**{campo: ano}), usuario)
        ano._history_user = usuario
        ano.delete()


# --- Parceiro desativado (D-208) ---------------------------------------------------------------


def _ativo(parceiro, usuario, valor):
    parceiro.desativado_em = valor
    parceiro._history_user = usuario
    parceiro.save(update_fields=["desativado_em"])


def desativar_parceiro(parceiro, usuario):
    _ativo(parceiro, usuario, timezone.now())


def reativar_parceiro(parceiro, usuario):
    _ativo(parceiro, usuario, None)


def parceiros_do_ano(ano):
    """Ativos e os desativados com corte ou projeto ativo no ano: desativar nunca esconde um ano."""
    com_dados = Exists(Corte.objects.filter(parceiro_ano__parceiro=OuterRef("pk"), ano=ano)) | Exists(
        Projeto.objects.filter(parceiro_ano__parceiro=OuterRef("pk"), ano=ano, arquivado_em__isnull=True)
    )
    return Parceiro.objects.filter(Q(desativado_em__isnull=True) | com_dados)
