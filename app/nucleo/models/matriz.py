from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import F, Q
from simple_history.models import HistoricalRecords

from nucleo.db import max_len

from .cadastro import Ano, Componente, Etapa


class Matriz(models.Model):
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    nome = models.TextField()
    # Só consulta (D-113); origem de qualquer ano (D-124). A FK do banco, com
    # ON DELETE SET NULL, vem da migração 0003: DB_SET_NULL daria fields.E323,
    # porque o resto da cadeia usa on_delete em Python.
    duplicada_de = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        db_constraint=False,
        null=True,
        blank=True,
        related_name="duplicatas",
    )
    history = HistoricalRecords()

    class Meta:
        db_table = "matriz"
        constraints = [
            models.UniqueConstraint(fields=["ano", "nome"], name="matriz_ano_nome_uniq"),
            models.UniqueConstraint(fields=["id", "ano"], name="matriz_id_ano_uniq"),
            models.CheckConstraint(
                condition=~Q(duplicada_de=F("id")), name="matriz_duplicada_de_outra"
            ),
            max_len("matriz", "nome", 200),
        ]

    def __str__(self):
        return f"{self.nome} ({self.ano})"


class MatrizEtapaCC(models.Model):
    # Mesmo ano em matriz, etapa e componente: FKs compostas na migração 0002 (D-090).
    matriz = models.ForeignKey(Matriz, on_delete=models.PROTECT)
    etapa = models.ForeignKey(Etapa, on_delete=models.PROTECT)
    componente = models.ForeignKey(Componente, on_delete=models.PROTECT)
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)
    passo = models.IntegerField(null=True, blank=True)  # nulo = sem linhas vazias (D-091)
    history = HistoricalRecords()

    class Meta:
        db_table = "matriz_etapa_cc"
        constraints = [
            models.UniqueConstraint(
                fields=["matriz", "etapa", "componente"], name="matriz_etapa_cc_uniq"
            ),
        ]

    def __str__(self):
        return f"{self.matriz} · {self.etapa.codigo} {self.componente.codigo}"


class Descritor(models.Model):
    matriz_etapa_cc = models.ForeignKey(MatrizEtapaCC, on_delete=models.CASCADE)
    codigo = models.TextField()
    descricao = models.TextField()
    prerequisitos = ArrayField(models.TextField(), default=list, blank=True)
    praticas = models.TextField(blank=True)
    conhecimento = models.TextField(blank=True)
    habilidades_relacionadas = models.TextField(blank=True)
    habilidade_correspondente = models.TextField(blank=True)
    ordem = models.IntegerField()
    history = HistoricalRecords()

    class Meta:
        db_table = "descritor"
        constraints = [
            models.UniqueConstraint(
                fields=["matriz_etapa_cc", "codigo"], name="descritor_mecc_codigo_uniq"
            ),
            max_len("descritor", "codigo", 20),
        ]

    def __str__(self):
        return self.codigo


class Tarefa(models.Model):
    descritor = models.ForeignKey(Descritor, on_delete=models.CASCADE)
    inicio = models.IntegerField()
    fim = models.IntegerField()
    texto = models.TextField()
    # Caminho no storage, compartilhado entre anos pelo abrir_ano: quem trocar o arquivo
    # só apaga o antigo se nenhuma outra Tarefa usar o mesmo caminho (D-150, D-181:
    # `servicos.arquivos.apagar_item_orfao`). Grava só `servicos.arquivos.receber_item`.
    arquivo = models.TextField(null=True, blank=True)
    texto_alternativo = models.TextField("Texto alternativo", blank=True, default="")  # D-180
    ordem = models.IntegerField()
    history = HistoricalRecords()

    class Meta:
        db_table = "tarefa"
        constraints = [
            models.CheckConstraint(condition=Q(inicio__lt=F("fim")), name="tarefa_inicio_menor_fim"),
            max_len("tarefa", "arquivo", 500),
            max_len("tarefa", "texto_alternativo", 1000),
        ]

    @property
    def codigo(self):
        """Código da tarefa nas telas (confirmação da exclusão, leitor de tela do F1): `D01 100-150`."""
        return f"{self.descritor.codigo} {self.inicio}-{self.fim}"

    def __str__(self):
        return self.codigo
