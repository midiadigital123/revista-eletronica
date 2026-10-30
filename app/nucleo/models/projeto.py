from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, Func, Q, Value
from django.db.models.lookups import IsNull, Range
from simple_history.models import HistoricalRecords

from nucleo.db import max_len
from nucleo.variaveis import TAMANHO_MAX, VARIAVEIS

from .cadastro import Ano, Componente, Etapa, Parceiro
from .matriz import Matriz

# FKs compostas de ano destas tabelas: migração 0005 (D-090, D-124).


class ParceiroAno(models.Model):
    parceiro = models.ForeignKey(Parceiro, on_delete=models.PROTECT)
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    matriz = models.ForeignKey(Matriz, on_delete=models.PROTECT, null=True, blank=True)  # D-106
    history = HistoricalRecords()

    class Meta:
        db_table = "parceiro_ano"
        constraints = [
            models.UniqueConstraint(fields=["parceiro", "ano"], name="parceiro_ano_parceiro_ano_uniq"),
            models.UniqueConstraint(fields=["id", "ano"], name="parceiro_ano_id_ano_uniq"),
        ]

    def __str__(self):
        return f"{self.parceiro} {self.ano}"


class Corte(models.Model):
    parceiro_ano = models.ForeignKey(ParceiroAno, on_delete=models.PROTECT)
    etapa = models.ForeignKey(Etapa, on_delete=models.PROTECT)
    componente = models.ForeignKey(Componente, on_delete=models.PROTECT)
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    # Crescente e dentro de 0..escala_max: clean() de serviço (D-055), CHECK não lê etapa.
    valores = ArrayField(models.IntegerField())
    history = HistoricalRecords()

    class Meta:
        db_table = "corte"
        constraints = [
            models.UniqueConstraint(
                fields=["parceiro_ano", "etapa", "componente"], name="corte_uniq"
            ),
            models.CheckConstraint(
                condition=Range(
                    Func(F("valores"), function="cardinality", output_field=models.IntegerField()),
                    (1, 4),
                ),
                name="corte_valores_1a4",
            ),
            models.CheckConstraint(
                condition=IsNull(
                    Func(F("valores"), Value(None), function="array_position",
                         output_field=models.IntegerField()),
                    True,
                ),
                name="corte_valores_sem_nulo",
            ),
        ]


class Projeto(models.Model):
    parceiro_ano = models.ForeignKey(ParceiroAno, on_delete=models.PROTECT)
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    nome = models.TextField()
    arquivado_em = models.DateTimeField(null=True, blank=True)  # nulo = ativo
    # Uma coluna por variável não automática de nucleo.variaveis.VARIAVEIS (D-100).
    issn = models.TextField(blank=True, default="")
    adjetivo_patrio_singular_masculino = models.TextField(blank=True, default="")
    adjetivo_patrio_singular_feminino = models.TextField(blank=True, default="")
    adjetivo_patrio_plural_masculino = models.TextField(blank=True, default="")
    adjetivo_patrio_plural_feminino = models.TextField(blank=True, default="")
    do_da_de_nome_parceiro = models.TextField(blank=True, default="")
    no_na_em_nome_parceiro = models.TextField(blank=True, default="")
    nome_programa = models.TextField(blank=True, default="")
    do_da_nome_programa = models.TextField(blank=True, default="")
    no_na_nome_programa = models.TextField(blank=True, default="")
    nome_regional = models.TextField(blank=True, default="")
    nome_secretaria = models.TextField(blank=True, default="")
    pd01 = models.TextField(blank=True, default="")
    pd02 = models.TextField(blank=True, default="")
    pd03 = models.TextField(blank=True, default="")
    pd04 = models.TextField(blank=True, default="")
    pd05 = models.TextField(blank=True, default="")
    plataforma = models.TextField(blank=True, default="")
    quais_redes = models.TextField(blank=True, default="")
    sigla_programa = models.TextField(blank=True, default="")
    do_da_sigla_programa = models.TextField(blank=True, default="")
    no_na_sigla_programa = models.TextField(blank=True, default="")
    sigla_regional = models.TextField(blank=True, default="")
    sigla_secretaria = models.TextField(blank=True, default="")
    history = HistoricalRecords()

    class Meta:
        db_table = "projeto"
        constraints = [
            models.UniqueConstraint(
                fields=["parceiro_ano"],
                condition=Q(arquivado_em__isnull=True),
                name="projeto_um_ativo_por_parceiro_ano",
            ),
            models.UniqueConstraint(fields=["id", "ano"], name="projeto_id_ano_uniq"),
            max_len("projeto", "nome", 200),
        ] + [max_len("projeto", v.nome, TAMANHO_MAX) for v in VARIAVEIS if not v.automatica]

    def __str__(self):
        return self.nome


class ProjetoPasso(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT)
    etapa = models.ForeignKey(Etapa, on_delete=models.PROTECT)
    componente = models.ForeignKey(Componente, on_delete=models.PROTECT)
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)  # só para as FKs compostas
    passo = models.IntegerField(null=True, blank=True)  # nulo = sem linhas vazias, de propósito
    history = HistoricalRecords()

    class Meta:
        db_table = "projeto_passo"
        constraints = [
            models.UniqueConstraint(
                fields=["projeto", "etapa", "componente"], name="projeto_passo_uniq"
            ),
        ]


class ProjetoCor(models.Model):
    projeto = models.ForeignKey(Projeto, on_delete=models.PROTECT)
    padrao = models.IntegerField()
    cor = models.TextField()
    history = HistoricalRecords()

    class Meta:
        db_table = "projeto_cor"
        constraints = [
            models.UniqueConstraint(fields=["projeto", "padrao"], name="projeto_cor_uniq"),
            models.CheckConstraint(
                condition=Q(padrao__gte=1, padrao__lte=5), name="projeto_cor_padrao_1a5"
            ),
            models.CheckConstraint(
                condition=Q(cor__regex=r"^#[0-9A-Fa-f]{6}$"), name="projeto_cor_cor_hex"
            ),
        ]
