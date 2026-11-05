"""Renumera a ordem das etapas pela lógica escolar (EF antes de EM, pela série) em todos os anos.

Etapas gravadas fora da tela B ficaram com a ordem antiga e o preview mostrava 9EF antes de 5EF.
A partir daqui `Etapa.save` mantém a ordem; a regra está repetida aqui porque migração não importa
código do app (o modelo histórico não tem o `save` novo).
"""
import re

from django.db import migrations

CODIGO = re.compile(r"^\s*(\d+)\s*(EF|EM)\s*$", re.IGNORECASE)


def chave(codigo):
    m = CODIGO.match(codigo)
    return (("EF", "EM").index(m[2].upper()), int(m[1]), "") if m else (2, 0, codigo)


def renumerar(apps, schema_editor):
    Etapa = apps.get_model("nucleo", "Etapa")
    for ano_id in Etapa.objects.values_list("ano_id", flat=True).distinct():
        for n, e in enumerate(sorted(Etapa.objects.filter(ano_id=ano_id), key=lambda e: chave(e.codigo)), 1):
            if e.ordem != n:
                Etapa.objects.filter(pk=e.pk).update(ordem=n)


class Migration(migrations.Migration):
    dependencies = [("nucleo", "0014_excluir_tarefa_descritor")]
    operations = [migrations.RunPython(renumerar, migrations.RunPython.noop)]
