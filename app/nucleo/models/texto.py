from django.conf import settings
from django.db import models
from django.db.models import Q
from simple_history.models import HistoricalRecords

from nucleo.db import max_len

from .cadastro import Ano, Componente


class Fasciculo(models.TextChoices):  # lista fixa, sem tabela (D-122)
    F1 = "F1"
    F2 = "F2"


def check_fasciculo(tabela):
    return models.CheckConstraint(
        condition=Q(fasciculo__in=Fasciculo.values), name=f"{tabela}_fasciculo_f1_f2"
    )


class Template(models.Model):
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    componente = models.ForeignKey(Componente, on_delete=models.PROTECT)
    fasciculo = models.TextField(choices=Fasciculo.choices)
    nome = models.TextField()
    origem = models.TextField(null=True, blank=True)  # .hbs do seed; nulo se criado na tela
    history = HistoricalRecords()

    class Meta:
        db_table = "template"
        constraints = [
            models.UniqueConstraint(
                fields=["ano", "componente", "fasciculo", "nome"], name="template_nome_uniq"
            ),
            # Alvo da FK composta de revista_fasciculo (D-098, D-124).
            models.UniqueConstraint(
                fields=["id", "ano", "componente", "fasciculo"], name="template_alvo_uniq"
            ),
            check_fasciculo("template"),
            max_len("template", "nome", 200),
            max_len("template", "origem", 200),
        ]

    def __str__(self):
        return f"{self.nome} ({self.fasciculo})"


class TemplateVersao(models.Model):
    """Só INSERT: a versão atual é a de maior número (D-115, D-125). Sem histórico."""

    template = models.ForeignKey(Template, on_delete=models.PROTECT)
    numero = models.IntegerField()
    texto = models.TextField()
    criada_em = models.DateTimeField(auto_now_add=True)
    # Nulo só no seed (carregar_templates), que não tem usuário.
    criada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True
    )

    class Meta:
        db_table = "template_versao"
        constraints = [
            models.UniqueConstraint(fields=["template", "numero"], name="template_versao_uniq"),
            # Alvo da FK composta de revista_secao (D-115).
            models.UniqueConstraint(fields=["id", "template"], name="template_versao_alvo_uniq"),
        ]

    def save(self, *args, **kwargs):
        # Mensagem amigável; o trigger da migração 0006 barra update e delete por qualquer caminho.
        if not self._state.adding:
            raise ValueError("template_versao é só INSERT: salve uma versão nova")
        super().save(*args, **kwargs)
