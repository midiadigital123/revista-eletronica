import re

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
    # D-208: nulo = ativo. Desativado some da grade dos anos em que não tem corte nem projeto ativo
    # (`servicos.exclusao.parceiros_do_ano`); nunca esconde o histórico de um ano.
    desativado_em = models.DateTimeField(null=True, blank=True)
    history = HistoricalRecords()

    class Meta:
        db_table = "parceiro"
        constraints = [max_len("parceiro", "nome", 200)]

    def __str__(self):
        return self.nome


ETAPA_CODIGO = re.compile(r"^\s*(\d+)\s*(EF|EM)\s*$", re.IGNORECASE)


def ordem_escolar(codigo):
    """Lógica escolar (pedido do usuário, 03/11): todo o fundamental (EF) antes do médio (EM) e, no
    mesmo ensino, pela série (2EF, 5EF, 9EF, 1EM, 3EM). Código fora do padrão vai para o fim."""
    m = ETAPA_CODIGO.match(codigo)
    return (("EF", "EM").index(m[2].upper()), int(m[1]), "") if m else (2, 0, codigo)


def renumerar_etapas(ano_id, etapas=None):
    """Ordem 1…N das etapas do ano pela `ordem_escolar`. Por `update`: a ordem é derivada do código,
    e o `save` da Etapa chama isto (save aqui entraria em recursão)."""
    etapas = etapas if etapas is not None else Etapa.objects.filter(ano_id=ano_id)
    for n, etapa in enumerate(sorted(etapas, key=lambda e: ordem_escolar(e.codigo)), 1):
        if etapa.ordem != n:
            type(etapa).objects.filter(pk=etapa.pk).update(ordem=n)


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

    def save(self, *args, **kwargs):
        # A ordem nasce do código, por qualquer caminho (tela B, admin, criar_demo, abrir ano): o preview
        # ordena por ela, e uma etapa gravada fora da tela B deixava 9EF antes de 5EF.
        if self.ordem is None:
            self.ordem = 0
        super().save(*args, **kwargs)
        renumerar_etapas(self.ano_id)
        self.ordem = Etapa.objects.values_list("ordem", flat=True).get(pk=self.pk)

    def delete(self, *args, **kwargs):
        # Sem buraco na ordem depois de excluir (D-205). O `apagar_ano` apaga pelo Collector, sem passar aqui.
        resultado = super().delete(*args, **kwargs)
        renumerar_etapas(self.ano_id)
        return resultado


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
