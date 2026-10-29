# FKs compostas do S03 (D-090, D-098, D-104, D-115, D-124): o ORM não as declara.
from django.db import migrations

from nucleo.db import fk_composta


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0004_projeto_revista_texto_controle")]

    operations = [
        fk_composta("parceiro_ano", "matriz"),  # matriz_id anulável (D-106)
        fk_composta("corte", "parceiro_ano"),
        fk_composta("corte", "etapa"),
        fk_composta("corte", "componente"),
        fk_composta("projeto", "parceiro_ano"),
        fk_composta("projeto_passo", "projeto"),
        fk_composta("projeto_passo", "etapa"),
        fk_composta("projeto_passo", "componente"),
        fk_composta("template", "componente"),
        fk_composta("revista", "projeto"),
        fk_composta("revista", "componente"),
        fk_composta(
            "revista_fasciculo", "revista",
            colunas=("revista_id", "ano_id", "componente_id"),
            nome="fk_revista_fasciculo_revista_ano",
        ),
        # template_id anulável (D-106): MATCH SIMPLE, nulo = sem template.
        fk_composta(
            "revista_fasciculo", "template",
            colunas=("template_id", "ano_id", "componente_id", "fasciculo"),
            nome="fk_revista_fasciculo_template_ano",
        ),
        # A cópia carrega o template: trocar o template com cópias é recusado (D-104).
        fk_composta(
            "revista_secao", "revista_fasciculo",
            colunas=("revista_fasciculo_id", "template_id"),
            nome="fk_revista_secao_fasciculo_template",
        ),
        # A cópia não aponta para versão de outro template (D-115).
        fk_composta(
            "revista_secao", "template_versao",
            colunas=("template_versao_id", "template_id"),
            nome="fk_revista_secao_versao_template",
        ),
    ]
