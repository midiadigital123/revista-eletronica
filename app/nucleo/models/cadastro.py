from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords

from nucleo.db import max_len


class Ano(models.Model):
    ano = models.IntegerField(unique=True)
    history = HistoricalRecords()

    class Meta:
        db_table = "ano"
        permissions = [("abrir_ano", "Pode abrir ano novo")]

    def __str__(self):
        return str(self.ano)


class Parceiro(models.Model):
    nome = models.TextField(unique=True)
    history = HistoricalRecords()

    class Meta:
        db_table = "parceiro"
        constraints = [max_len("parceiro", "nome", 200)]

    def __str__(self):
        return self.nome


class Etapa(models.Model):
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    codigo = models.TextField()
    escala_max = models.IntegerField()
    ordem = models.IntegerField()
    history = HistoricalRecords()

    class Meta:
        db_table = "etapa"
        constraints = [
            models.UniqueConstraint(fields=["ano", "codigo"], name="etapa_ano_codigo_uniq"),
            models.UniqueConstraint(fields=["id", "ano"], name="etapa_id_ano_uniq"),
            max_len("etapa", "codigo", 20),
        ]

    def __str__(self):
        return f"{self.codigo} ({self.ano})"


class Componente(models.Model):
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    codigo = models.TextField()
    nome = models.TextField()
    history = HistoricalRecords()

    class Meta:
        db_table = "componente"
        constraints = [
            models.UniqueConstraint(fields=["ano", "codigo"], name="componente_ano_codigo_uniq"),
            models.UniqueConstraint(fields=["id", "ano"], name="componente_id_ano_uniq"),
            max_len("componente", "codigo", 20),
            max_len("componente", "nome", 200),
        ]

    def __str__(self):
        return f"{self.codigo} ({self.ano})"


# Os CHECKs *_padrao_1a5 e *_cor_hex ficam no banco; os validators dão a mensagem no form (D-090).
PADRAO_1A5 = [MinValueValidator(1), MaxValueValidator(5)]
COR_HEX = [RegexValidator(r"^#[0-9A-Fa-f]{6}$", "Use o formato #RRGGBB.")]


class CorPadrao(models.Model):
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    padrao = models.IntegerField("Padrão", validators=PADRAO_1A5)
    cor = models.TextField(validators=COR_HEX)
    # Nome do padrão no ano; o `pdNN` do projeto sobrescreve quando preenchido (D-175).
    nome = models.TextField(blank=True, default="", max_length=200)
    history = HistoricalRecords()

    class Meta:
        db_table = "cor_padrao"
        verbose_name = "padrão do ano"
        verbose_name_plural = "padrões do ano (cor e nome)"
        constraints = [
            models.UniqueConstraint(fields=["ano", "padrao"], name="cor_padrao_ano_padrao_uniq"),
            models.CheckConstraint(
                condition=Q(padrao__gte=1, padrao__lte=5), name="cor_padrao_padrao_1a5"
            ),
            models.CheckConstraint(
                condition=Q(cor__regex=r"^#[0-9A-Fa-f]{6}$"), name="cor_padrao_cor_hex"
            ),
            max_len("cor_padrao", "nome", 200),
        ]

    def __str__(self):
        return f"Padrão {self.padrao} {self.cor} ({self.ano})"
