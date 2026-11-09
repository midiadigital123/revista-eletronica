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
        permissions = [
            ("validar_revista", "Pode clicar em Validado"),
            ("marcar_impressa", "Pode clicar em Revista Impressa Atualizada"),
        ]
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

    def __str__(self):
        return f"{self.projeto} · {self.componente.codigo}"


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

    def __str__(self):
        return f"{self.revista} {self.fasciculo}"


class RevistaSecao(models.Model):
    """Cópia editada de uma seção do template (D-115)."""

    revista_fasciculo = models.ForeignKey(RevistaFasciculo, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.PROTECT)  # só para FK composta
    secao = models.TextField()  # id de nucleo.texto.SECOES (F1: introducao, fechamento; F2: abertura, passo-*, dlg-descritor...)
    texto = models.TextField()
    template_versao = models.ForeignKey(TemplateVersao, on_delete=models.PROTECT)
    history = HistoricalRecords()

    class Meta:
        db_table = "revista_secao"
        constraints = [
            models.UniqueConstraint(fields=["revista_fasciculo", "secao"], name="revista_secao_uniq"),
            max_len("revista_secao", "secao", 100),
        ]


class TipoInfografico(models.TextChoices):  # D-230
    ALFA = "alfa", "Avaliação e Currículo – Alfa"
    OUTRAS = "outras", "Avaliação e Currículo – Outras Etapas"


PASSOS_DESLIGAVEIS = ("habilidades", "progressao", "tarefas")  # D-227: abertura e descritor são fixos


class EtapaReferencial(models.TextChoices):  # D-233
    """Lista fixa: o referencial cobre os 12 anos; a tabela Etapa do ano só tem as avaliadas."""

    EF1 = "1EF", "1º ano do Ensino Fundamental"
    EF2 = "2EF", "2º ano do Ensino Fundamental"
    EF3 = "3EF", "3º ano do Ensino Fundamental"
    EF4 = "4EF", "4º ano do Ensino Fundamental"
    EF5 = "5EF", "5º ano do Ensino Fundamental"
    EF6 = "6EF", "6º ano do Ensino Fundamental"
    EF7 = "7EF", "7º ano do Ensino Fundamental"
    EF8 = "8EF", "8º ano do Ensino Fundamental"
    EF9 = "9EF", "9º ano do Ensino Fundamental"
    EM1 = "1EM", "1ª série do Ensino Médio"
    EM2 = "2EM", "2ª série do Ensino Médio"
    EM3 = "3EM", "3ª série do Ensino Médio"


class Marca(models.TextChoices):  # legenda do docx
    INTRODUZIR = "I", "Introduzir"
    APROFUNDAR = "A", "Aprofundar"
    CONSOLIDAR = "C", "Consolidar"
    RETOMAR = "R", "Retomar"


class RevistaInfografico(models.Model):
    """Infográfico do F2 (D-230): `alfa` existe com cortes no 2EF; `outras`, com cortes em outra etapa."""

    revista = models.ForeignKey(Revista, on_delete=models.CASCADE)
    componente = models.ForeignKey(Componente, on_delete=models.PROTECT)  # só para FK composta
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)  # só para FK composta
    tipo = models.TextField(choices=TipoInfografico.choices)
    # nulo = ativo (D-117), E revista ativa: a arquivada guarda os seus como estavam (D-230).
    arquivado_em = models.DateTimeField(null=True, blank=True)
    passos_desligados = ArrayField(models.TextField(), default=list, blank=True)
    habilidade = models.TextField(blank=True, default="")  # habilidade destacada (redação canônica)
    # Textos dos cliques ❶ ❷ ❸.
    texto_descritor = models.TextField(blank=True, default="")
    texto_progressao = models.TextField(blank=True, default="")
    texto_habilidades = models.TextField(blank=True, default="")
    history = HistoricalRecords()

    class Meta:
        db_table = "revista_infografico"
        constraints = [
            models.UniqueConstraint(fields=["revista", "tipo"], name="revista_infografico_uniq"),
            # Alvo das FKs compostas das filhas (coerência de ano).
            models.UniqueConstraint(fields=["id", "ano"], name="revista_infografico_alvo_uniq"),
            models.CheckConstraint(condition=Q(tipo__in=TipoInfografico.values), name="revista_infografico_tipo"),
            models.CheckConstraint(
                condition=Q(passos_desligados__contained_by=list(PASSOS_DESLIGAVEIS)),
                name="revista_infografico_passos",
            ),
            max_len("revista_infografico", "habilidade", 500),
        ]

    def __str__(self):
        return f"{self.revista} {self.tipo}"


class RevistaInfograficoEtapa(models.Model):
    """Linha da tabela do referencial, uma por etapa. Código e texto vazios = célula mesclada (fase 2)."""

    infografico = models.ForeignKey(RevistaInfografico, on_delete=models.CASCADE)
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)  # só para FK composta
    etapa = models.TextField(choices=EtapaReferencial.choices)
    marca = models.TextField(choices=Marca.choices, blank=True, default="")  # vazio = sem marca
    codigo = models.TextField(blank=True, default="")  # código BNCC, ex.: EF15LP18
    texto = models.TextField(blank=True, default="")
    history = HistoricalRecords()

    class Meta:
        db_table = "revista_infografico_etapa"
        constraints = [
            models.UniqueConstraint(fields=["infografico", "etapa"], name="revista_infografico_etapa_uniq"),
            models.CheckConstraint(
                condition=Q(etapa__in=EtapaReferencial.values), name="revista_infografico_etapa_etapa"
            ),
            models.CheckConstraint(
                condition=Q(marca__in=["", *Marca.values]), name="revista_infografico_etapa_marca"
            ),
            max_len("revista_infografico_etapa", "codigo", 50),
        ]


class RevistaInfograficoItem(models.Model):
    """Um dos 4 itens do infográfico (D-235): descritor, etapa, imagem e análise próprios, sem tarefa da matriz."""

    infografico = models.ForeignKey(RevistaInfografico, on_delete=models.CASCADE)
    ano = models.ForeignKey(Ano, on_delete=models.PROTECT)  # só para FK composta
    posicao = models.SmallIntegerField()  # 1 a 4
    etapa = models.TextField(choices=EtapaReferencial.choices, blank=True, default="")  # vazio = ainda não escolhida
    descritor = models.TextField(blank=True, default="")  # código na matriz de referência, ex.: D05 (texto livre)
    imagem = models.TextField(null=True, blank=True)  # caminho no storage; item + suporte numa imagem só (D-232)
    imagem_sha256 = models.TextField(null=True, blank=True)
    texto_alternativo = models.TextField("Texto alternativo", blank=True, default="")  # D-180
    analise = models.TextField(blank=True, default="")
    history = HistoricalRecords()

    class Meta:
        db_table = "revista_infografico_item"
        constraints = [
            models.UniqueConstraint(fields=["infografico", "posicao"], name="revista_infografico_item_uniq"),
            models.CheckConstraint(
                condition=Q(posicao__gte=1, posicao__lte=4), name="revista_infografico_item_posicao_1a4"
            ),
            models.CheckConstraint(
                condition=Q(etapa__in=["", *EtapaReferencial.values]), name="revista_infografico_item_etapa"
            ),
            juntos("revista_infografico_item", "imagem", "imagem_sha256"),
            sha256("revista_infografico_item", "imagem_sha256"),
            max_len("revista_infografico_item", "imagem", 500),
            max_len("revista_infografico_item", "descritor", 20),
            max_len("revista_infografico_item", "texto_alternativo", 1000),
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
