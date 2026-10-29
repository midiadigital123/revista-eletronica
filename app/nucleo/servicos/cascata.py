"""Cascata dos cortes: cortes -> projeto -> revistas (D-061, D-065, D-068, D-093, D-094, D-117)."""

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from nucleo.models import (
    Corte,
    Fasciculo,
    FotoRevista,
    ParceiroAno,
    Projeto,
    Revista,
    RevistaFasciculo,
)
from nucleo.models.revista import Motivo
from nucleo.servicos.foto import fotografar


def validar_linhas(linhas, ano_id):
    """D-055: de 1 a 4 inteiros estritamente crescentes, estritamente dentro de (0, escala_max) (D-153)."""
    erros = []
    vistos = set()
    for etapa, componente, valores in linhas:
        rotulo = f"{etapa.codigo} {componente.codigo}"
        if etapa.ano_id != ano_id or componente.ano_id != ano_id:
            erros.append(f"{rotulo}: etapa e componente precisam ser do ano do parceiro.")
        if (etapa.pk, componente.pk) in vistos:
            erros.append(f"{rotulo}: linha repetida.")
        vistos.add((etapa.pk, componente.pk))
        if not 1 <= len(valores) <= 4:
            erros.append(f"{rotulo}: informe de 1 a 4 cortes.")
        if any(type(v) is not int for v in valores):
            erros.append(f"{rotulo}: cortes precisam ser inteiros.")
            continue
        if any(a >= b for a, b in zip(valores, valores[1:])):
            erros.append(f"{rotulo}: cortes precisam ser crescentes.")
        if any(not 0 < v < etapa.escala_max for v in valores):  # o JS do F1 recusa corte no limite (D-131)
            erros.append(f"{rotulo}: cortes precisam estar entre 1 e {etapa.escala_max - 1}.")
    if erros:
        raise ValidationError(erros)


def gravar_cortes(parceiro_ano, linhas, usuario):
    """Substitui TODOS os cortes do parceiro_ano por `linhas` e roda a cascata.

    `linhas`: lista de (Etapa, Componente, valores). Corte que não vier é apagado.
    `usuario`: autor das fotos (FotoRevista.criada_por é NOT NULL) e do histórico.
    """
    linhas = [(e, c, list(v)) for e, c, v in linhas]
    validar_linhas(linhas, parceiro_ano.ano_id)
    componentes = sorted({c.pk for _, c, _ in linhas})
    with transaction.atomic():
        # Serializa cascatas do mesmo parceiro_ano: sem isso, duas abas criariam 2 revistas.
        pa = (
            ParceiroAno.objects.select_for_update(no_key=True, of=("self",))
            .select_related("parceiro")
            .get(pk=parceiro_ano.pk)
        )
        agora = timezone.now()
        projeto = Projeto.objects.filter(parceiro_ano=pa, arquivado_em__isnull=True).first()
        # A foto de arquivamento lê os cortes: tira antes de _gravar apagá-los.
        a_arquivar = []
        if projeto is not None:
            a_arquivar = list(
                Revista.objects.filter(projeto=projeto, arquivada_em__isnull=True)
                .exclude(componente_id__in=componentes)
                .order_by("componente_id")
            )
            for revista in a_arquivar:
                fotografar(revista, Motivo.ARQUIVAMENTO, usuario)

        _gravar(pa, linhas, usuario)

        for revista in a_arquivar:
            revista.arquivada_em = agora
            _salvar(revista, usuario, update_fields=["arquivada_em"])
        if projeto is None:
            if not componentes:
                return
            # D-068: arquivado não volta; nasce outro projeto.
            projeto = _salvar(
                Projeto(parceiro_ano=pa, ano_id=pa.ano_id, nome=f"{pa.parceiro.nome} - NOME DO PROJETO"),
                usuario,
            )
        if not componentes:  # toda revista do projeto está arquivada
            projeto.arquivado_em = agora
            _salvar(projeto, usuario, update_fields=["arquivado_em"])
            return

        revistas = {r.componente_id: r for r in Revista.objects.filter(projeto=projeto)}
        for componente_id in componentes:
            revista = revistas.get(componente_id)
            if revista is None:
                _criar_revista(projeto, componente_id, usuario)
            elif revista.arquivada_em is not None:  # D-117: volta a mesma linha
                revista.arquivada_em = None
                _salvar(revista, usuario, update_fields=["arquivada_em"])


def _salvar(obj, usuario, **kwargs):
    obj._history_user = usuario
    obj.save(**kwargs)
    return obj


def _gravar(pa, linhas, usuario):
    atuais = {(c.etapa_id, c.componente_id): c for c in Corte.objects.filter(parceiro_ano=pa)}
    for etapa, componente, valores in linhas:
        corte = atuais.pop((etapa.pk, componente.pk), None)
        if corte is None:
            _salvar(
                Corte(parceiro_ano=pa, etapa=etapa, componente=componente, ano_id=pa.ano_id,
                      valores=valores),
                usuario,
            )
        elif corte.valores != valores:  # só grava o que mudou: histórico sem ruído
            corte.valores = valores
            _salvar(corte, usuario, update_fields=["valores"])
    for corte in atuais.values():
        corte._history_user = usuario
        corte.delete()


def _criar_revista(projeto, componente_id, usuario):
    revista = _salvar(
        Revista(projeto=projeto, componente_id=componente_id, ano_id=projeto.ano_id), usuario
    )
    for fasciculo in Fasciculo.values:
        _salvar(
            RevistaFasciculo(revista=revista, fasciculo=fasciculo, componente_id=componente_id,
                             ano_id=projeto.ano_id),
            usuario,
        )
    # D-094: herda a última foto de impresso do mesmo componente em projeto arquivado.
    ultima = (
        FotoRevista.objects.filter(
            motivo=Motivo.IMPRESSO,
            revista__componente_id=componente_id,
            revista__projeto__parceiro_ano_id=projeto.parceiro_ano_id,
            revista__projeto__arquivado_em__isnull=False,
        )
        .order_by("-criada_em", "-pk")
        .first()
    )
    if ultima is not None:
        FotoRevista.objects.create(
            revista=revista, motivo=Motivo.IMPRESSO, conteudo=ultima.conteudo,
            hash=ultima.hash, herdada=True, criada_por=usuario,
        )
    return revista
