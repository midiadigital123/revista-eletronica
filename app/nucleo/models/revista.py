from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords

from nucleo.db import max_len, sha256

from .cadastro import Ano, Componente
from .projeto import Projeto
from .texto import Fasciculo, Template, TemplateVersao, check_fasciculo

# FKs compostas destas tabelas: migração 0005 (D-098, D-104, D-115, D-124).


def juntos(tabela, a, b):
    """CHECK (a IS NULL) = (b IS NULL): arquivo e hash andam juntos (D-118)."""
    return models.CheckConstraint(
        condition=Q(**{f"{a}__isnull": True, f"{b}__isnull": True})
        | Q(**{f"{a}__isnull": False, f"{b}__isnull": False}),
        name=f"{tabela}_{a}_com_hash",
    )


class Revista(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT)
    componente = models.ForeignKey(Componente, on_delete=models.PROTECT)
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)  # só para as FKs compostas
    capa = models.TextField(null=True, blank=True)  # caminho no storage
    capa_sha256 = models.TextField(null=True, blank=True)
    svg_f2 = models.TextField(null=True, blank=True)  # caminho no storage, nome com uuid
    svg_sha256 = models.TextField(null=True, blank=True)
    svg_ids = ArrayField(models.TextField(), default=list, blank=True)
    arquivada_em = models.DateTimeField(null=True, blank=True)  # nulo = ativa (D-117)
    hash_validado = models.TextField(null=True, blank=True)
    validado_em = models.DateTimeField(null=True, blank=True)
    validado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )
    history = HistoricalRecords()

    class Meta:
        db_table = "revista"
        constraints = [
            models.UniqueConstraint(fields=["projeto", "componente"], name="revista_uniq"),
            models.UniqueConstraint(fields=["id", "ano", "componente"], name="revista_alvo_uniq"),
            juntos("revista", "capa", "capa_sha256"),
            juntos("revista", "svg_f2", "svg_sha256"),
            sha256("revista", "capa_sha256"),
            sha256("revista", "svg_sha256"),
            sha256("revista", "hash_validado"),
            max_len("revista", "capa", 500),
            max_len("revista", "svg_f2", 500),
        ]


class RevistaFasciculo(models.Model):
    revista = models.ForeignKey(Revista, on_delete=models.CASCADE)
    fasciculo = models.TextField(choices=Fasciculo.choices)
    componente = models.ForeignKey(Componente, on_delete=models.PROTECT)  # só para FK composta
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)  # só para FK composta
    # Nulo até escolher (D-106); com MATCH SIMPLE, nulo = sem conferência.
    template = models.ForeignKey(Template, on_delete=models.PROTECT, null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        db_table = "revista_fasciculo"
        constraints = [
            models.UniqueConstraint(fields=["revista", "fasciculo"], name="revista_fasciculo_uniq"),
            # Alvo da FK composta de revista_secao: a cópia trava a troca de template.
            models.UniqueConstraint(fields=["id", "template"], name="revista_fasciculo_alvo_uniq"),
            check_fasciculo("revista_fasciculo"),
        ]


class RevistaSecao(models.Model):
    """Cópia editada de uma seção do template (D-115)."""

    revista_fasciculo = models.ForeignKey(RevistaFasciculo, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.PROTECT)  # só para FK composta
    secao = models.TextField()  # introducao, fechamento, passo1, dlg-p2
    texto = models.TextField()
    template_versao = models.ForeignKey(TemplateVersao, on_delete=models.PROTECT)
    history = HistoricalRecords()

    class Meta:
        db_table = "revista_secao"
        constraints = [
            models.UniqueConstraint(fields=["revista_fasciculo", "secao"], name="revista_secao_uniq"),
            max_len("revista_secao", "secao", 100),
        ]


class Motivo(models.TextChoices):
    IMPRESSO = "impresso"
    ARQUIVAMENTO = "arquivamento"


class FotoRevista(models.Model):
    revista = models.ForeignKey(Revista, on_delete=models.PROTECT)
    motivo = models.TextField(choices=Motivo.choices)
    conteudo = models.JSONField()  # textos da revista resolvida
    hash = models.TextField()
    herdada = models.BooleanField(default=False)  # veio de revista arquivada (D-094)
    criada_em = models.DateTimeField(auto_now_add=True)
    criada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    history = HistoricalRecords()

    class Meta:
        db_table = "foto_revista"
        constraints = [
            models.CheckConstraint(
                condition=Q(motivo__in=Motivo.values), name="foto_revista_motivo"
            ),
            sha256("foto_revista", "hash"),
        ]
        indexes = [
            models.Index(fields=["revista", "motivo", "-criada_em"], name="foto_revista_ultima_idx"),
        ]
