# D-296: o F1 deixa de ter a seção "fechamento" (nucleo.texto.SECOES_F1 só com "introducao"). Regra congelada, como
# na 0025: não importa nucleo.texto nem lê o seed.
#   1. cada Template F1 cuja versão atual (a de maior número) tem "## fechamento" ganha uma TemplateVersao nova
#      (só INSERT, D-207) com o mesmo texto sem o bloco; o RevistaFasciculo aponta para o Template e passa a ler
#      a versão nova sozinho;
#   2. as cópias (RevistaSecao) "fechamento" de fascículo F1 são apagadas, inclusive de revista arquivada: o
#      resolver mantém cópia de seção que saiu do template (órfã), e ela seguiria no hash e no "o que mudou".
#      A revista arquivada mostra a foto (D-117), que não muda.
# Sem registro do simple-history (como na 0022, 0023 e 0025). Sem volta: o texto das cópias se perde; o do
# template fica na versão anterior.
import re

from django.db import migrations

BLOCO = re.compile(r"^## fechamento\n.*?(?=^## |\Z)", re.S | re.M)


def sem_fechamento(texto):
    return BLOCO.sub("", texto).rstrip("\n") + "\n"


def frente(apps, schema_editor):
    Template = apps.get_model("nucleo", "Template")
    TemplateVersao = apps.get_model("nucleo", "TemplateVersao")
    RevistaSecao = apps.get_model("nucleo", "RevistaSecao")

    for template in Template.objects.filter(fasciculo="F1"):
        ultima = TemplateVersao.objects.filter(template=template).order_by("-numero").first()
        if ultima is not None and BLOCO.search(ultima.texto):  # idempotente: a versão nova não tem o bloco
            TemplateVersao.objects.create(
                template=template, numero=ultima.numero + 1, texto=sem_fechamento(ultima.texto)
            )

    RevistaSecao.objects.filter(revista_fasciculo__fasciculo="F1", secao="fechamento").delete()


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0027_remove_preferida")]

    operations = [migrations.RunPython(frente, migrations.RunPython.noop)]
